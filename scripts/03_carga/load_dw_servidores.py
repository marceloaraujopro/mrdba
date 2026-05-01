#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


# =========================================================
# CONFIGURAÇÕES
# =========================================================
STAGING_DIR = Path("/dados/projetos/mrdba/data_lake/staging/servidores")
ARQ_STAGING = STAGING_DIR / "servidores_staging_20260415_124748.csv"

DB_USER = "marcelo"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "db_mrdba"

SCHEMA = "dw"
TABELA = "fato_servidores_mensal"


# =========================================================
# AUXILIARES
# =========================================================
def criar_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def ler_csv(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo de staging não encontrado: {caminho}")

    df = pd.read_csv(caminho)

    colunas_numericas = [
        "ANOMES",
        "TAMANHO_GB",
        "DELTA_1_MES",
        "DELTA_2_MESES",
        "DELTA_3_MESES",
        "DELTA_6_MESES",
        "DELTA_12_MESES",
        "DISPONIBILIDADE_PCT",
    ]

    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "ANOMES" in df.columns:
        df["ANOMES"] = df["ANOMES"].astype("Int64")

    if "MINUTOS_INDISPONIVEIS" in df.columns:
        df["MINUTOS_INDISPONIVEIS"] = pd.to_numeric(
            df["MINUTOS_INDISPONIVEIS"], errors="coerce"
        ).astype("Int64")

    return df


def anomes_para_data(anomes):
    try:
        anomes_int = int(anomes)
        ano = anomes_int // 100
        mes = anomes_int % 100
        return pd.Timestamp(year=ano, month=mes, day=1).date()
    except Exception:
        return None


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    colunas_esperadas = [
        "INSTANCIA",
        "HOST_NAME",
        "ANOMES",
        "TAMANHO_GB",
        "DELTA_1_MES",
        "DELTA_2_MESES",
        "DELTA_3_MESES",
        "DELTA_6_MESES",
        "DELTA_12_MESES",
        "DISPONIBILIDADE_PCT",
        "MINUTOS_INDISPONIVEIS",
    ]

    faltantes = [c for c in colunas_esperadas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas ausentes no staging: {faltantes}")

    df["DATA_REFERENCIA"] = df["ANOMES"].apply(anomes_para_data)

    invalidos = df[df["DATA_REFERENCIA"].isna()]
    if not invalidos.empty:
        valores_invalidos = invalidos["ANOMES"].tolist()
        raise ValueError(f"Valores inválidos em ANOMES: {valores_invalidos}")

    df = df[
        [
            "INSTANCIA",
            "HOST_NAME",
            "ANOMES",
            "DATA_REFERENCIA",
            "TAMANHO_GB",
            "DELTA_1_MES",
            "DELTA_2_MESES",
            "DELTA_3_MESES",
            "DELTA_6_MESES",
            "DELTA_12_MESES",
            "DISPONIBILIDADE_PCT",
            "MINUTOS_INDISPONIVEIS",
        ]
    ]

    return df


def criar_estrutura(engine) -> None:
    ddl = f"""
    CREATE SCHEMA IF NOT EXISTS {SCHEMA};

    CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABELA} (
        instancia               VARCHAR(100)   NOT NULL,
        host_name               VARCHAR(200),
        anomes                  INTEGER        NOT NULL,
        data_referencia         DATE           NOT NULL,
        tamanho_gb              NUMERIC(14,2),
        delta_1_mes             NUMERIC(14,2),
        delta_2_meses           NUMERIC(14,2),
        delta_3_meses           NUMERIC(14,2),
        delta_6_meses           NUMERIC(14,2),
        delta_12_meses          NUMERIC(14,2),
        disponibilidade_pct     NUMERIC(7,2),
        minutos_indisponiveis   INTEGER
    );
    """

    with engine.begin() as conn:
        conn.execute(text(ddl))


def deduplicar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates(subset=["INSTANCIA", "ANOMES"]).reset_index(drop=True)


def deletar_periodos_existentes(engine, df: pd.DataFrame) -> None:
    periodos = [int(p) for p in df["ANOMES"].dropna().unique().tolist()]
    if not periodos:
        return

    delete_sql = text(
        f"""
        DELETE FROM {SCHEMA}.{TABELA}
        WHERE anomes = ANY(:periodos)
        """
    )

    with engine.begin() as conn:
        conn.execute(delete_sql, {"periodos": periodos})


def carregar_dataframe(engine, df: pd.DataFrame) -> None:
    df_banco = df.rename(
        columns={
            "INSTANCIA": "instancia",
            "HOST_NAME": "host_name",
            "ANOMES": "anomes",
            "DATA_REFERENCIA": "data_referencia",
            "TAMANHO_GB": "tamanho_gb",
            "DELTA_1_MES": "delta_1_mes",
            "DELTA_2_MESES": "delta_2_meses",
            "DELTA_3_MESES": "delta_3_meses",
            "DELTA_6_MESES": "delta_6_meses",
            "DELTA_12_MESES": "delta_12_meses",
            "DISPONIBILIDADE_PCT": "disponibilidade_pct",
            "MINUTOS_INDISPONIVEIS": "minutos_indisponiveis",
        }
    )

    df_banco.to_sql(
        name=TABELA,
        con=engine,
        schema=SCHEMA,
        if_exists="append",
        index=False,
        method="multi",
    )


def main() -> int:
    print("=" * 70)
    print("CARGA DW - SERVIDORES MENSAL")
    print("=" * 70)
    print(f"Arquivo staging: {ARQ_STAGING}")
    print(f"Destino        : {DB_NAME}.{SCHEMA}.{TABELA}")
    print("-" * 70)

    try:
        df = ler_csv(ARQ_STAGING)
        print(f"Linhas lidas do CSV: {len(df)}")

        df = preparar_dataframe(df)
        df = deduplicar_dataframe(df)

        print(f"Linhas após preparação: {len(df)}")
        print("Prévia da carga:")
        print(df.head(10).to_string(index=False))

        engine = criar_engine()

        criar_estrutura(engine)
        deletar_periodos_existentes(engine, df)
        carregar_dataframe(engine, df)

        print("-" * 70)
        print("Carga concluída com sucesso.")

        return 0

    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
