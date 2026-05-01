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
TABELA = "dim_tempo"


# =========================================================
# AUXILIARES
# =========================================================
def criar_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def caminho_curated_tickets(ano: str, mes: str) -> Path:
    return CURATED_DIR / f"mrdba_tickets_curated_{ano}_{mes}.csv"


def ler_curated_tickets(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo curated não encontrado: {caminho}")

    df = pd.read_csv(caminho)

    colunas_esperadas = ["data_criacao", "data_ultima_alteracao"]
    faltantes = [c for c in colunas_esperadas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas ausentes no curated: {faltantes}")

    return df


def coletar_datas_tickets(df: pd.DataFrame) -> pd.Series:
    datas_criacao = pd.to_datetime(df["data_criacao"], errors="coerce")
    datas_alteracao = pd.to_datetime(df["data_ultima_alteracao"], errors="coerce")

    datas = pd.concat([datas_criacao, datas_alteracao], ignore_index=True)
    datas = datas.dropna().dt.normalize().drop_duplicates().sort_values()

    return datas


def nome_mes_pt(mes: int) -> str:
    mapa = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }
    return mapa[mes]


def montar_dim_tempo(datas: pd.Series) -> pd.DataFrame:
    if datas.empty:
        return pd.DataFrame(
            columns=[
                "sk_tempo",
                "data_completa",
                "ano",
                "mes",
                "dia",
                "anomes",
                "nome_mes",
                "trimestre",
                "semestre",
            ]
        )

    df = pd.DataFrame({"data_completa": datas.dt.date})
    data_ts = pd.to_datetime(df["data_completa"])

    df["ano"] = data_ts.dt.year.astype(int)
    df["mes"] = data_ts.dt.month.astype(int)
    df["dia"] = data_ts.dt.day.astype(int)
    df["anomes"] = data_ts.dt.strftime("%Y%m").astype(int)
    df["nome_mes"] = df["mes"].apply(nome_mes_pt)
    df["trimestre"] = (((df["mes"] - 1) // 3) + 1).astype(int)
    df["semestre"] = df["mes"].apply(lambda x: 1 if x <= 6 else 2).astype(int)
    df["sk_tempo"] = data_ts.dt.strftime("%Y%m%d").astype(int)

    df = df[
        [
            "sk_tempo",
            "data_completa",
            "ano",
            "mes",
            "dia",
            "anomes",
            "nome_mes",
            "trimestre",
            "semestre",
        ]
    ].drop_duplicates(subset=["sk_tempo"]).sort_values("sk_tempo")

    return df


def buscar_sk_existentes(engine) -> set[int]:
    sql = text(f"SELECT sk_tempo FROM {SCHEMA}.{TABELA}")

    with engine.connect() as conn:
        resultado = conn.execute(sql).fetchall()

    return {int(linha[0]) for linha in resultado}


def filtrar_novas_datas(df_dim: pd.DataFrame, sk_existentes: set[int]) -> pd.DataFrame:
    if df_dim.empty:
        return df_dim

    return df_dim[~df_dim["sk_tempo"].isin(sk_existentes)].copy()


def inserir_dim_tempo(engine, df_dim: pd.DataFrame) -> None:
    if df_dim.empty:
        return

    df_dim.to_sql(
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
        print("Uso: python3 load_dim_tempo.py YYYY MM")
        return 1

    ano = sys.argv[1]
    mes = sys.argv[2]

    arquivo_curated = caminho_curated_tickets(ano, mes)

    print("=" * 70)
    print("CARGA DIM_TEMPO")
    print("=" * 70)
    print(f"Arquivo curated: {arquivo_curated}")
    print(f"Destino        : {DB_NAME}.{SCHEMA}.{TABELA}")
    print("-" * 70)

    try:
        df = ler_curated_tickets(arquivo_curated)
        print(f"Linhas lidas do curated: {len(df)}")

        datas = coletar_datas_tickets(df)
        print(f"Datas únicas identificadas: {len(datas)}")

        df_dim = montar_dim_tempo(datas)
        print(f"Linhas montadas para dim_tempo: {len(df_dim)}")

        engine = criar_engine()
        sk_existentes = buscar_sk_existentes(engine)
        df_novas = filtrar_novas_datas(df_dim, sk_existentes)

        print(f"Linhas novas para inserir: {len(df_novas)}")

        if not df_novas.empty:
            print("Prévia das novas linhas:")
            print(df_novas.head(10).to_string(index=False))

        inserir_dim_tempo(engine, df_novas)

        print("-" * 70)
        print("Carga da dim_tempo concluída com sucesso.")
        return 0

    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
