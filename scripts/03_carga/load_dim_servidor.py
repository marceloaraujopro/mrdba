#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


BASE_DIR = Path("/dados/projetos/mrdba")
CURATED_DIR = BASE_DIR / "data_lake" / "03_curated" / "tickets"

DB_USER = "marcelo"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "db_mrdba"

SCHEMA = "dw"
TABELA = "dim_servidor"


def criar_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def caminho_curated(ano: str, mes: str) -> Path:
    return CURATED_DIR / f"mrdba_tickets_curated_{ano}_{mes}.csv"


def ler_curated(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    df = pd.read_csv(caminho)

    colunas_esperadas = ["empresa", "sgdb", "ambiente", "nome_servidor", "nk_servidor"]
    faltantes = [c for c in colunas_esperadas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Colunas ausentes no curated: {faltantes}")

    if "instancia" not in df.columns:
        df["instancia"] = ""

    return df


def classificar_ambiente_macro(valor: str) -> str | None:
    if pd.isna(valor):
        return None

    texto = str(valor).strip().lower()
    if texto == "":
        return None

    if any(chave in texto for chave in ["prod", "produção", "producao"]):
        return "Produção"

    return "Não Produção"


def preparar_servidores(df: pd.DataFrame) -> pd.DataFrame:
    df_dim = df.copy()

    for col in ["empresa", "sgdb", "ambiente", "nome_servidor", "nk_servidor", "instancia"]:
        df_dim[col] = df_dim[col].fillna("").astype(str).str.strip()

    df_dim = df_dim[
        (df_dim["nk_servidor"] != "") &
        (df_dim["nome_servidor"] != "")
    ].copy()

    df_dim["ambiente_macro"] = df_dim["ambiente"].apply(classificar_ambiente_macro)

    df_dim["host_name"] = None
    df_dim["ativo"] = True

    df_dim["instancia"] = df_dim["instancia"].replace("", None)

    df_dim = (
        df_dim.sort_values(["nk_servidor", "empresa", "ambiente", "sgdb", "nome_servidor"])
        .drop_duplicates(subset=["nk_servidor"], keep="first")
        .reset_index(drop=True)
    )

    return df_dim[
        [
            "nk_servidor",
            "instancia",
            "host_name",
            "nome_servidor",
            "ambiente",
            "ambiente_macro",
            "sgdb",
            "empresa",
            "ativo",
        ]
    ]


def buscar_clientes(engine) -> pd.DataFrame:
    sql = text(f"""
        SELECT sk_cliente, nm_cliente
        FROM {SCHEMA}.dim_cliente
    """)

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)

    df["nm_cliente"] = df["nm_cliente"].astype(str).str.strip()
    return df


def enriquecer_com_sk_cliente(df_servidor: pd.DataFrame, df_clientes: pd.DataFrame) -> pd.DataFrame:
    df = df_servidor.merge(
        df_clientes,
        how="left",
        left_on="empresa",
        right_on="nm_cliente"
    )

    df = df.drop(columns=["empresa", "nm_cliente"])
    return df


def buscar_nks_existentes(engine) -> set[str]:
    sql = text(f"SELECT nk_servidor FROM {SCHEMA}.{TABELA}")

    with engine.connect() as conn:
        resultado = conn.execute(sql).fetchall()

    return {str(linha[0]).strip() for linha in resultado}


def filtrar_novos(df: pd.DataFrame, existentes: set[str]) -> pd.DataFrame:
    return df[~df["nk_servidor"].isin(existentes)].copy()


def inserir(engine, df: pd.DataFrame):
    if df.empty:
        return

    df.to_sql(
        name=TABELA,
        con=engine,
        schema=SCHEMA,
        if_exists="append",
        index=False,
        method="multi"
    )


def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: python3 load_dim_servidor.py YYYY MM")
        return 1

    ano = sys.argv[1]
    mes = sys.argv[2].zfill(2)

    arquivo = caminho_curated(ano, mes)

    print("=" * 70)
    print("CARGA DIM_SERVIDOR")
    print("=" * 70)
    print(f"Arquivo curated: {arquivo}")
    print(f"Destino        : {DB_NAME}.{SCHEMA}.{TABELA}")
    print("-" * 70)

    try:
        df = ler_curated(arquivo)
        print(f"Linhas lidas: {len(df)}")

        df_servidor = preparar_servidores(df)
        print(f"Servidores distintos no curated: {len(df_servidor)}")

        engine = criar_engine()

        df_clientes = buscar_clientes(engine)
        df_servidor = enriquecer_com_sk_cliente(df_servidor, df_clientes)

        existentes = buscar_nks_existentes(engine)
        df_novos = filtrar_novos(df_servidor, existentes)

        print(f"Novos servidores a inserir: {len(df_novos)}")

        if not df_novos.empty:
            print("Prévia:")
            print(df_novos.head(10).to_string(index=False))

        inserir(engine, df_novos)

        print("-" * 70)
        print("Carga da dim_servidor concluída com sucesso.")
        return 0

    except Exception as e:
        print(f"ERRO: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
