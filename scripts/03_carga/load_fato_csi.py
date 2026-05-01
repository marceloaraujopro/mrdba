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
BASE_DIR = Path("/dados/projetos/mrdba")
CURATED_DIR = BASE_DIR / "data_lake" / "03_curated" / "tickets"

DB_USER = "marcelo"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "db_mrdba"

SCHEMA = "dw"
TABELA = "fato_csi"


# =========================================================
# AUXILIARES
# =========================================================
def criar_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def caminho_curated(ano: str, mes: str) -> Path:
    return CURATED_DIR / f"mrdba_tickets_curated_{ano}_{mes}.csv"


def ler_curated(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    df = pd.read_csv(caminho)

    colunas_esperadas = [
        "id_ticket",
        "empresa",
        "data_criacao",
        "data_ultima_alteracao",
        "tipo_ticket",
        "foi_atuado",
        "titulo_ticket",
        "csi_status",
        "nk_servidor",
        "tempo_resolucao_horas",
    ]

    faltantes = [c for c in colunas_esperadas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas ausentes no curated: {faltantes}")

    return df


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["tipo_ticket"] = df["tipo_ticket"].fillna("").astype(str).str.strip()
    df = df[df["tipo_ticket"].str.upper() == "CSI"].copy()

    df["id_ticket"] = pd.to_numeric(df["id_ticket"], errors="coerce")
    df = df.dropna(subset=["id_ticket"])
    df["id_ticket"] = df["id_ticket"].astype("int64")

    df["data_criacao"] = pd.to_datetime(df["data_criacao"], errors="coerce").dt.date
    df["data_ultima_alteracao"] = pd.to_datetime(df["data_ultima_alteracao"], errors="coerce").dt.date
    df["tempo_resolucao_horas"] = pd.to_numeric(df["tempo_resolucao_horas"], errors="coerce")

    colunas_texto = [
        "empresa",
        "foi_atuado",
        "titulo_ticket",
        "csi_status",
        "nk_servidor",
    ]

    for col in colunas_texto:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["foi_atuado_flag"] = df["foi_atuado"].str.lower().map({
        "sim": 1,
        "não": 0,
        "nao": 0
     })

    return df


def carregar_dimensoes(engine):
    with engine.connect() as conn:
        dim_cliente = pd.read_sql(text(f"""
            SELECT sk_cliente, nm_cliente
            FROM {SCHEMA}.dim_cliente
        """), conn)

        dim_servidor = pd.read_sql(text(f"""
            SELECT sk_servidor, nk_servidor
            FROM {SCHEMA}.dim_servidor
        """), conn)

        dim_status_csi = pd.read_sql(text(f"""
            SELECT sk_status_csi, nm_status_csi
            FROM {SCHEMA}.dim_status_csi
        """), conn)

        dim_tempo = pd.read_sql(text(f"""
            SELECT sk_tempo, data_completa
            FROM {SCHEMA}.dim_tempo
        """), conn)

    dim_cliente["nm_cliente"] = dim_cliente["nm_cliente"].astype(str).str.strip()
    dim_servidor["nk_servidor"] = dim_servidor["nk_servidor"].astype(str).str.strip()
    dim_status_csi["nm_status_csi"] = dim_status_csi["nm_status_csi"].astype(str).str.strip().str.lower()
    dim_tempo["data_completa"] = pd.to_datetime(dim_tempo["data_completa"], errors="coerce").dt.date

    return dim_cliente, dim_servidor, dim_status_csi, dim_tempo


def enriquecer_com_sks(df, dim_cliente, dim_servidor, dim_status_csi, dim_tempo):
    df = df.merge(
        dim_cliente,
        how="left",
        left_on="empresa",
        right_on="nm_cliente"
    ).drop(columns=["nm_cliente"])

    df = df.merge(
        dim_servidor,
        how="left",
        on="nk_servidor"
    )

    df["csi_status_norm"] = df["csi_status"].astype(str).str.strip().str.lower()
    df = df.merge(
        dim_status_csi,
        how="left",
        left_on="csi_status_norm",
        right_on="nm_status_csi"
    ).drop(columns=["csi_status_norm", "nm_status_csi"])

    dim_tempo_criacao = dim_tempo.rename(columns={
        "sk_tempo": "sk_tempo_criacao",
        "data_completa": "data_criacao"
    })

    dim_tempo_fech = dim_tempo.rename(columns={
        "sk_tempo": "sk_tempo_fechamento",
        "data_completa": "data_ultima_alteracao"
    })

    df = df.merge(dim_tempo_criacao, how="left", on="data_criacao")
    df = df.merge(dim_tempo_fech, how="left", on="data_ultima_alteracao")

    return df


def validar_sks(df: pd.DataFrame):
    obrigatorias = {
        "sk_status_csi": "csi_status",
        "sk_tempo_criacao": "data_criacao",
    }

    for sk, origem in obrigatorias.items():
        faltando = df[df[sk].isna()]
        if not faltando.empty:
            raise ValueError(
                f"Há registros sem {sk} resolvida a partir de {origem}. "
                f"Exemplo: {faltando[[origem]].head(5).to_dict(orient='records')}"
            )


def montar_fato(df: pd.DataFrame) -> pd.DataFrame:
    df_fato = pd.DataFrame({
        "id_ticket_origem": df["id_ticket"].astype("int64"),
        "sk_cliente": df["sk_cliente"].astype("Int64"),
        "sk_servidor": df["sk_servidor"].astype("Int64"),
        "sk_status_csi": df["sk_status_csi"].astype("int64"),
        "sk_tempo_criacao": df["sk_tempo_criacao"].astype("int64"),
        "sk_tempo_fechamento": df["sk_tempo_fechamento"].astype("Int64"),
        "titulo_csi": df["titulo_ticket"].fillna("").astype(str).str.strip(),
        "foi_atuado": df["foi_atuado_flag"].astype("Int64"),
        "tempo_resolucao_horas": df["tempo_resolucao_horas"],
    })

    return df_fato.drop_duplicates(subset=["id_ticket_origem"]).reset_index(drop=True)


def deletar_existentes(engine, ids_ticket: list[int]) -> None:
    if not ids_ticket:
        return

    sql = text(f"""
        DELETE FROM {SCHEMA}.{TABELA}
        WHERE id_ticket_origem = ANY(:ids_ticket)
    """)

    with engine.begin() as conn:
        conn.execute(sql, {"ids_ticket": ids_ticket})


def inserir(engine, df: pd.DataFrame):
    if df.empty:
        return

    df.to_sql(
        name=TABELA,
        con=engine,
        schema=SCHEMA,
        if_exists="append",
        index=False,
        method="multi",
    )


# =========================================================
# MAIN
# =========================================================
def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: python3 load_fato_csi.py YYYY MM")
        return 1

    ano = sys.argv[1]
    mes = sys.argv[2]
    arquivo = caminho_curated(ano, mes)

    print("=" * 70)
    print("CARGA FATO_CSI")
    print("=" * 70)
    print(f"Arquivo curated: {arquivo}")
    print(f"Destino        : {DB_NAME}.{SCHEMA}.{TABELA}")
    print("-" * 70)

    try:
        df = ler_curated(arquivo)
        print(f"Linhas lidas: {len(df)}")

        df = preparar_dataframe(df)
        print(f"Linhas CSI após filtro/preparação: {len(df)}")

        engine = criar_engine()
        dim_cliente, dim_servidor, dim_status_csi, dim_tempo = carregar_dimensoes(engine)

        df = enriquecer_com_sks(df, dim_cliente, dim_servidor, dim_status_csi, dim_tempo)
        validar_sks(df)

        df_fato = montar_fato(df)
        print(f"Linhas finais da fato_csi: {len(df_fato)}")

        ids_ticket = df_fato["id_ticket_origem"].astype(int).tolist()
        deletar_existentes(engine, ids_ticket)

        print("Prévia da carga:")
        print(df_fato.head(10).to_string(index=False))

        inserir(engine, df_fato)

        print("-" * 70)
        print("Carga da fato_csi concluída com sucesso.")
        return 0

    except Exception as e:
        print(f"ERRO: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
