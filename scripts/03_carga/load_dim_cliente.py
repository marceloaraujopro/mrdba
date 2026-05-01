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
TABELA = "dim_cliente"


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

    if "empresa" not in df.columns:
        raise ValueError("Coluna 'empresa' não encontrada no curated")

    return df


def extrair_clientes(df: pd.DataFrame) -> pd.DataFrame:
    df_clientes = (
    df["empresa"]
    .fillna("NÃO IDENTIFICADO")
    .astype(str)
    .str.strip()
    .replace("", "NÃO IDENTIFICADO")
    )

    # remove vazios
    df_clientes = df_clientes[df_clientes != ""]

    # únicos
    df_clientes = df_clientes.drop_duplicates()

    return pd.DataFrame({"nm_cliente": df_clientes})


def buscar_existentes(engine) -> set[str]:
    sql = text(f"SELECT nm_cliente FROM {SCHEMA}.{TABELA}")

    with engine.connect() as conn:
        resultado = conn.execute(sql).fetchall()

    return {str(linha[0]).strip() for linha in resultado}


def filtrar_novos(df: pd.DataFrame, existentes: set[str]) -> pd.DataFrame:
    return df[~df["nm_cliente"].isin(existentes)].copy()


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


# =========================================================
# MAIN
# =========================================================
def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: python3 load_dim_cliente.py YYYY MM")
        return 1

    ano = sys.argv[1]
    mes = sys.argv[2]

    arquivo = caminho_curated(ano, mes)

    print("=" * 70)
    print("CARGA DIM_CLIENTE")
    print("=" * 70)
    print(f"Arquivo curated: {arquivo}")
    print(f"Destino        : {DB_NAME}.{SCHEMA}.{TABELA}")
    print("-" * 70)

    try:
        df = ler_curated(arquivo)
        print(f"Linhas lidas: {len(df)}")

        df_clientes = extrair_clientes(df)
        print(f"Clientes únicos encontrados: {len(df_clientes)}")

        engine = criar_engine()
        existentes = buscar_existentes(engine)

        df_novos = filtrar_novos(df_clientes, existentes)
        print(f"Novos clientes a inserir: {len(df_novos)}")

        if not df_novos.empty:
            print("Prévia:")
            print(df_novos.head(10).to_string(index=False))

        inserir(engine, df_novos)

        print("-" * 70)
        print("Carga da dim_cliente concluída com sucesso.")
        return 0

    except Exception as e:
        print(f"ERRO: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
