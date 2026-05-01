#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

import os
from dotenv import load_dotenv

# =========================================================
# CONFIGURAÇÕES
# =========================================================
BASE_DIR = Path("/dados/projetos/mrdba")
CURATED_DIR = BASE_DIR / "data_lake" / "03_curated" / "tickets"

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

SCHEMA = "dw"
TABELA = "dim_status_csi"


# =========================================================
# AUXILIARES
# =========================================================
def criar_engine():
    variaveis_obrigatorias = {
        "DB_USER": DB_USER,
        "DB_PASSWORD": DB_PASSWORD,
        "DB_HOST": DB_HOST,
        "DB_PORT": DB_PORT,
        "DB_NAME": DB_NAME,
    }

    faltando = [nome for nome, valor in variaveis_obrigatorias.items() if not valor]

    if faltando:
        raise EnvironmentError(
            f"Variáveis de ambiente ausentes no .env: {', '.join(faltando)}"
        )

    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def caminho_curated(ano: str, mes: str) -> Path:
    return CURATED_DIR / f"mrdba_tickets_curated_{ano}_{mes}.csv"


def ler_curated(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    df = pd.read_csv(caminho)

    if "csi_status" not in df.columns:
        raise ValueError("Coluna 'csi_status' não encontrada no curated")

    return df


def extrair_status_csi(df: pd.DataFrame) -> pd.DataFrame:
    serie = (
        df["csi_status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    serie = serie[serie != ""]
    serie = serie.drop_duplicates().sort_values()

    return pd.DataFrame({"nm_status_csi": serie})


def buscar_existentes(engine) -> set[str]:
    sql = text(f"SELECT nm_status_csi FROM {SCHEMA}.{TABELA}")

    with engine.connect() as conn:
        resultado = conn.execute(sql).fetchall()

    return {str(linha[0]).strip().lower() for linha in resultado}


def filtrar_novos(df: pd.DataFrame, existentes: set[str]) -> pd.DataFrame:
    return df[~df["nm_status_csi"].isin(existentes)].copy()


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
        print("Uso: python3 load_dim_status_csi.py YYYY MM")
        return 1

    ano = sys.argv[1]
    mes = sys.argv[2]

    arquivo = caminho_curated(ano, mes)

    print("=" * 70)
    print("CARGA DIM_STATUS_CSI")
    print("=" * 70)
    print(f"Arquivo curated: {arquivo}")
    print(f"Destino        : {DB_NAME}.{SCHEMA}.{TABELA}")
    print("-" * 70)

    try:
        df = ler_curated(arquivo)
        print(f"Linhas lidas: {len(df)}")

        df_status = extrair_status_csi(df)
        print(f"Status CSI únicos encontrados: {len(df_status)}")

        engine = criar_engine()
        existentes = buscar_existentes(engine)

        df_novos = filtrar_novos(df_status, existentes)
        print(f"Novos status CSI a inserir: {len(df_novos)}")

        if not df_novos.empty:
            print("Prévia:")
            print(df_novos.head(10).to_string(index=False))

        inserir(engine, df_novos)

        print("-" * 70)
        print("Carga da dim_status_csi concluída com sucesso.")
        return 0

    except Exception as e:
        print(f"ERRO: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
