#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd


# =========================================================
# CONFIGURAÇÕES
# =========================================================
RAW_DIR = Path("/dados/projetos/mrdba/data_lake/raw/servidores")
STAGING_DIR = Path("/dados/projetos/mrdba/data_lake/staging/servidores")

ARQ_DISPONIBILIDADE = RAW_DIR / "disponibilidade_ECP_20260415_124748_limpo.json"
ARQ_VOLUMETRIA = RAW_DIR / "volumetria_ECP_20260415_124748.json"

INSTANCIA_PADRAO = "ECP"
HOST_NAME_PADRAO = "SMAWSECCVBP01"


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================
def extrair_stamp(nome_arquivo: str) -> str:
    m = re.search(r"(\d{8}_\d{6})", nome_arquivo)
    return m.group(1) if m else "sem_stamp"


def carregar_json(caminho: Path) -> dict[str, Any]:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    with caminho.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalizar_numero(valor: Any) -> float | None:
    if valor is None:
        return None

    if isinstance(valor, (int, float)):
        return float(valor)

    valor_str = str(valor).strip()
    if valor_str == "":
        return None

    valor_str = valor_str.replace(" ", "")

    try:
        return float(valor_str)
    except ValueError:
        return None


def normalizar_anomes(valor: Any) -> int | None:
    """
    Converte 'MM/YYYY' para inteiro no padrão YYYYMM.
    Ex.: '04/2026' -> 202604
    """
    if valor is None:
        return None

    valor_str = str(valor).strip()
    if valor_str == "":
        return None

    dt = pd.to_datetime(valor_str, format="%m/%Y", errors="coerce")
    if pd.isna(dt):
        return None

    return int(dt.strftime("%Y%m"))


def anomes_para_data(anomes: Any) -> pd.Timestamp | pd.NaT:
    """
    Converte YYYYMM (int) para timestamp do primeiro dia do mês.
    Ex.: 202604 -> 2026-04-01
    """
    try:
        anomes_int = int(anomes)
        ano = anomes_int // 100
        mes = anomes_int % 100
        return pd.Timestamp(year=ano, month=mes, day=1)
    except Exception:
        return pd.NaT


# =========================================================
# LEITURA DOS JSONS DE TESTE
# =========================================================
def ler_disponibilidade(
    caminho: Path,
    instancia_padrao: str,
    host_name_padrao: str | None,
) -> pd.DataFrame:
    payload = carregar_json(caminho)

    try:
        items = payload["results"][0]["items"]
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(f"Estrutura inesperada no arquivo de disponibilidade: {caminho}") from e

    registros = []
    for item in items:
        registros.append(
            {
                "INSTANCIA": instancia_padrao,
                "HOST_NAME": host_name_padrao,
                "ANOMES": normalizar_anomes(item.get("anomes")),
                "DISPONIBILIDADE_PCT": normalizar_numero(item.get("disponibilidade_pct")),
                "MINUTOS_INDISPONIVEIS": pd.to_numeric(item.get("minutos_indisponiveis"), errors="coerce"),
            }
        )

    df = pd.DataFrame(registros)

    if not df.empty:
        df["ANOMES"] = pd.to_numeric(df["ANOMES"], errors="coerce").astype("Int64")
        df["MINUTOS_INDISPONIVEIS"] = pd.to_numeric(
            df["MINUTOS_INDISPONIVEIS"], errors="coerce"
        ).astype("Int64")
        df["DISPONIBILIDADE_PCT"] = pd.to_numeric(
            df["DISPONIBILIDADE_PCT"], errors="coerce"
        )

    return df


def ler_volumetria(
    caminho: Path,
    host_name_padrao: str | None,
) -> pd.DataFrame:
    payload = carregar_json(caminho)

    try:
        items = payload["results"][0]["items"]
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(f"Estrutura inesperada no arquivo de volumetria: {caminho}") from e

    registros = []
    for item in items:
        registros.append(
            {
                "INSTANCIA": item.get("db"),
                "HOST_NAME": host_name_padrao,
                "ANOMES": normalizar_anomes(item.get("mes")),
                "TAMANHO_GB": normalizar_numero(item.get("gb_total")),
                "DELTA_1_MES": normalizar_numero(item.get("diff_1m")),
                "DELTA_2_MESES": None,  # não existe nesta carga teste
                "DELTA_3_MESES": normalizar_numero(item.get("diff_3m")),
                "DELTA_6_MESES": normalizar_numero(item.get("diff_6m")),
                "DELTA_12_MESES": normalizar_numero(item.get("diff_12m")),
            }
        )

    df = pd.DataFrame(registros)

    if not df.empty:
        df["ANOMES"] = pd.to_numeric(df["ANOMES"], errors="coerce").astype("Int64")

    return df


# =========================================================
# CONSOLIDAÇÃO
# =========================================================
def consolidar(df_disp: pd.DataFrame, df_vol: pd.DataFrame) -> pd.DataFrame:
    if df_disp.empty and df_vol.empty:
        return pd.DataFrame()

    if df_disp.empty:
        df_final = df_vol.copy()
    elif df_vol.empty:
        df_final = df_disp.copy()
    else:
        df_final = pd.merge(
            df_vol,
            df_disp,
            on=["INSTANCIA", "ANOMES"],
            how="outer",
            validate="one_to_one",
            suffixes=("_vol", "_disp"),
        )

        host_vol = (
            df_final["HOST_NAME_vol"]
            if "HOST_NAME_vol" in df_final.columns
            else pd.Series([pd.NA] * len(df_final))
        )
        host_disp = (
            df_final["HOST_NAME_disp"]
            if "HOST_NAME_disp" in df_final.columns
            else pd.Series([pd.NA] * len(df_final))
        )
        df_final["HOST_NAME"] = host_vol.combine_first(host_disp)

        for col in ["HOST_NAME_vol", "HOST_NAME_disp"]:
            if col in df_final.columns:
                df_final = df_final.drop(columns=[col])

    colunas_finais = [
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

    for col in colunas_finais:
        if col not in df_final.columns:
            df_final[col] = pd.NA

    df_final = df_final[colunas_finais]
    df_final["ANOMES"] = pd.to_numeric(df_final["ANOMES"], errors="coerce").astype("Int64")

    df_final["_ordem_data"] = df_final["ANOMES"].apply(anomes_para_data)
    df_final = (
        df_final.sort_values(
            by=["_ordem_data", "INSTANCIA"],
            ascending=[False, True],
            na_position="last",
        )
        .drop(columns=["_ordem_data"])
        .reset_index(drop=True)
    )

    return df_final


def salvar_csv(df: pd.DataFrame, caminho_saida: Path) -> None:
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho_saida, index=False, encoding="utf-8")


# =========================================================
# MAIN
# =========================================================
def main() -> int:
    print("=" * 70)
    print("TRANSFORMAÇÃO JSON -> STAGING (SERVIDORES)")
    print("=" * 70)
    print(f"Disponibilidade: {ARQ_DISPONIBILIDADE}")
    print(f"Volumetria     : {ARQ_VOLUMETRIA}")
    print("-" * 70)

    try:
        df_disp = ler_disponibilidade(
            ARQ_DISPONIBILIDADE,
            instancia_padrao=INSTANCIA_PADRAO,
            host_name_padrao=HOST_NAME_PADRAO,
        )

        df_vol = ler_volumetria(
            ARQ_VOLUMETRIA,
            host_name_padrao=HOST_NAME_PADRAO,
        )

        print(f"Linhas disponibilidade: {len(df_disp)}")
        print(f"Linhas volumetria     : {len(df_vol)}")

        df_staging = consolidar(df_disp, df_vol)

        if df_staging.empty:
            print("Nenhum dado encontrado para gerar staging.")
            return 1

        stamp = extrair_stamp(ARQ_DISPONIBILIDADE.name)
        caminho_saida = STAGING_DIR / f"servidores_staging_{stamp}.csv"

        salvar_csv(df_staging, caminho_saida)

        print("-" * 70)
        print("Prévia do staging:")
        print(df_staging.head(10).to_string(index=False))
        print("-" * 70)
        print(f"Arquivo gerado : {caminho_saida}")
        print(f"Total de linhas: {len(df_staging)}")
        print(f"Total colunas  : {len(df_staging.columns)}")

        return 0

    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
