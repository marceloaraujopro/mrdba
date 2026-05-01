#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


# =========================================================
# CONFIGURAÇÕES
# =========================================================
BASE_DIR = Path("/dados/projetos/mrdba")

DB_USER = "marcelo"
DB_PASSWORD = "1234"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "db_mrdba"

SCHEMA = "dw"
TABELA_FATO = "fato_servidor"
TABELA_DIM_TEMPO = "dim_tempo"
TABELA_DIM_SERVIDOR = "dim_servidor"


# =========================================================
# AUXILIARES GERAIS
# =========================================================
def criar_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


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


def padronizar_nk_servidor(host_name, instancia) -> str:
    valor = ""

    if pd.notna(host_name) and str(host_name).strip():
        valor = str(host_name).strip()
    elif pd.notna(instancia) and str(instancia).strip():
        valor = str(instancia).strip()

    valor = valor.upper()
    valor = re.sub(r"\s+", " ", valor)

    return valor


def anomes_para_data(anomes):
    try:
        anomes_int = int(anomes)
        ano = anomes_int // 100
        mes = anomes_int % 100
        return pd.Timestamp(year=ano, month=mes, day=1).date()
    except Exception:
        return None


# =========================================================
# LEITURA E PREPARAÇÃO
# =========================================================
def ler_csv(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    df = pd.read_csv(caminho)

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
        raise ValueError(f"Colunas ausentes no arquivo de servidores: {faltantes}")

    return df


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["ANOMES"] = pd.to_numeric(df["ANOMES"], errors="coerce").astype("Int64")

    colunas_numericas = [
        "TAMANHO_GB",
        "DELTA_1_MES",
        "DELTA_2_MESES",
        "DELTA_3_MESES",
        "DELTA_6_MESES",
        "DELTA_12_MESES",
        "DISPONIBILIDADE_PCT",
        "MINUTOS_INDISPONIVEIS",
    ]

    for col in colunas_numericas:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["INSTANCIA"] = df["INSTANCIA"].fillna("").astype(str).str.strip()
    df["HOST_NAME"] = df["HOST_NAME"].fillna("").astype(str).str.strip()

    df["DATA_REFERENCIA"] = df["ANOMES"].apply(anomes_para_data)

    invalidos = df[df["DATA_REFERENCIA"].isna()]
    if not invalidos.empty:
        raise ValueError(
            f"Há valores inválidos em ANOMES: {invalidos['ANOMES'].tolist()}"
        )

    df["NK_SERVIDOR"] = df.apply(
        lambda row: padronizar_nk_servidor(row["HOST_NAME"], row["INSTANCIA"]),
        axis=1,
    )

    df = df[df["NK_SERVIDOR"] != ""].copy()
    df = df.drop_duplicates(subset=["NK_SERVIDOR", "ANOMES"]).reset_index(drop=True)

    return df


# =========================================================
# DIM_TEMPO
# =========================================================
def montar_dim_tempo_referencias(datas: pd.Series) -> pd.DataFrame:
    datas = (
        pd.to_datetime(datas, errors="coerce")
        .dropna()
        .drop_duplicates()
        .sort_values()
    )

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

    return df[
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
    ].drop_duplicates(subset=["sk_tempo"])


def garantir_dim_tempo(engine, datas: pd.Series) -> None:
    df_dim = montar_dim_tempo_referencias(datas)

    if df_dim.empty:
        return

    with engine.connect() as conn:
        existentes = pd.read_sql(
            text(f"SELECT sk_tempo FROM {SCHEMA}.{TABELA_DIM_TEMPO}"),
            conn,
        )

    sk_existentes = (
        set(existentes["sk_tempo"].astype(int).tolist())
        if not existentes.empty
        else set()
    )

    df_novas = df_dim[~df_dim["sk_tempo"].isin(sk_existentes)].copy()

    if df_novas.empty:
        return

    df_novas.to_sql(
        name=TABELA_DIM_TEMPO,
        con=engine,
        schema=SCHEMA,
        if_exists="append",
        index=False,
        method="multi",
    )


# =========================================================
# DIM_SERVIDOR
# =========================================================
def carregar_dim_servidor(engine) -> pd.DataFrame:
    with engine.connect() as conn:
        df = pd.read_sql(
            text(
                f"""
                SELECT sk_servidor, nk_servidor, instancia, host_name, nome_servidor
                FROM {SCHEMA}.{TABELA_DIM_SERVIDOR}
                """
            ),
            conn,
        )

    if not df.empty:
        df["nk_servidor"] = df["nk_servidor"].astype(str).str.strip()

    return df


def inserir_servidores_ausentes(engine, df: pd.DataFrame) -> None:
    dim_atual = carregar_dim_servidor(engine)
    existentes = set(dim_atual["nk_servidor"].tolist()) if not dim_atual.empty else set()

    df_novos = df[~df["NK_SERVIDOR"].isin(existentes)].copy()

    if df_novos.empty:
        return

    df_insert = pd.DataFrame(
        {
            "nk_servidor": df_novos["NK_SERVIDOR"],
            "instancia": df_novos["INSTANCIA"].replace("", None),
            "host_name": df_novos["HOST_NAME"].replace("", None),
            "nome_servidor": df_novos.apply(
                lambda row: row["HOST_NAME"] if row["HOST_NAME"] else row["INSTANCIA"],
                axis=1,
            ).replace("", None),
            "ambiente": None,
            "ambiente_macro": None,
            "sgdb": None,
            "sk_cliente": None,
            "ativo": True,
        }
    ).drop_duplicates(subset=["nk_servidor"])

    df_insert.to_sql(
        name=TABELA_DIM_SERVIDOR,
        con=engine,
        schema=SCHEMA,
        if_exists="append",
        index=False,
        method="multi",
    )


def atualizar_servidores_existentes(engine, df: pd.DataFrame) -> None:
    """
    Enriquece servidores já existentes na dim_servidor.

    Caso o servidor tenha sido criado antes a partir dos tickets,
    os campos instancia e host_name podem estar nulos.
    Esta função preenche esses campos usando a fonte técnica de servidores.
    """
    df_base = df.drop_duplicates(subset=["NK_SERVIDOR"]).copy()

    registros = []

    for _, row in df_base.iterrows():
        instancia = row["INSTANCIA"] if row["INSTANCIA"] else None
        host_name = row["HOST_NAME"] if row["HOST_NAME"] else None
        nome_servidor = row["HOST_NAME"] if row["HOST_NAME"] else row["INSTANCIA"]

        registros.append(
            {
                "nk_servidor": row["NK_SERVIDOR"],
                "instancia": instancia,
                "host_name": host_name,
                "nome_servidor": nome_servidor if nome_servidor else None,
            }
        )

    if not registros:
        return

    sql = text(
        f"""
        UPDATE {SCHEMA}.{TABELA_DIM_SERVIDOR}
        SET
            instancia = COALESCE(NULLIF(instancia, ''), :instancia),
            host_name = COALESCE(NULLIF(host_name, ''), :host_name),
            nome_servidor = COALESCE(NULLIF(nome_servidor, ''), :nome_servidor)
        WHERE nk_servidor = :nk_servidor
        """
    )

    with engine.begin() as conn:
        conn.execute(sql, registros)


# =========================================================
# ENRIQUECIMENTO FATO
# =========================================================
def carregar_dimensoes_fato(engine):
    with engine.connect() as conn:
        dim_servidor = pd.read_sql(
            text(
                f"""
                SELECT sk_servidor, nk_servidor
                FROM {SCHEMA}.{TABELA_DIM_SERVIDOR}
                """
            ),
            conn,
        )

        dim_tempo = pd.read_sql(
            text(
                f"""
                SELECT sk_tempo, data_completa
                FROM {SCHEMA}.{TABELA_DIM_TEMPO}
                """
            ),
            conn,
        )

    dim_servidor["nk_servidor"] = dim_servidor["nk_servidor"].astype(str).str.strip()
    dim_tempo["data_completa"] = pd.to_datetime(
        dim_tempo["data_completa"],
        errors="coerce",
    ).dt.date

    return dim_servidor, dim_tempo


def enriquecer_com_sks(
    df: pd.DataFrame,
    dim_servidor: pd.DataFrame,
    dim_tempo: pd.DataFrame,
) -> pd.DataFrame:
    df = df.merge(
        dim_servidor,
        how="left",
        left_on="NK_SERVIDOR",
        right_on="nk_servidor",
    ).drop(columns=["nk_servidor"])

    dim_tempo_ref = dim_tempo.rename(
        columns={
            "sk_tempo": "sk_tempo_referencia",
            "data_completa": "DATA_REFERENCIA",
        }
    )

    df = df.merge(
        dim_tempo_ref,
        how="left",
        on="DATA_REFERENCIA",
    )

    faltando_servidor = df[df["sk_servidor"].isna()]
    if not faltando_servidor.empty:
        raise ValueError(
            "Há servidores sem SK resolvida. "
            f"Exemplo: {faltando_servidor[['NK_SERVIDOR']].head(5).to_dict(orient='records')}"
        )

    faltando_tempo = df[df["sk_tempo_referencia"].isna()]
    if not faltando_tempo.empty:
        raise ValueError(
            "Há datas de referência sem SK resolvida. "
            f"Exemplo: {faltando_tempo[['DATA_REFERENCIA']].head(5).to_dict(orient='records')}"
        )

    return df


def montar_fato(df: pd.DataFrame) -> pd.DataFrame:
    df_fato = pd.DataFrame(
        {
            "sk_servidor": df["sk_servidor"].astype("int64"),
            "sk_tempo_referencia": df["sk_tempo_referencia"].astype("int64"),
            "tamanho_gb": df["TAMANHO_GB"],
            "delta_1_mes": df["DELTA_1_MES"],
            "delta_2_meses": df["DELTA_2_MESES"],
            "delta_3_meses": df["DELTA_3_MESES"],
            "delta_6_meses": df["DELTA_6_MESES"],
            "delta_12_meses": df["DELTA_12_MESES"],
            "disponibilidade_pct": df["DISPONIBILIDADE_PCT"],
            "minutos_indisponiveis": df["MINUTOS_INDISPONIVEIS"].astype("Int64"),
            "arquivo_origem": df["ARQUIVO_ORIGEM"],
        }
    )

    return (
        df_fato
        .drop_duplicates(subset=["sk_servidor", "sk_tempo_referencia"])
        .reset_index(drop=True)
    )


def deletar_periodos_existentes(engine, df: pd.DataFrame) -> None:
    if df.empty:
        return

    sks_tempo = sorted(df["sk_tempo_referencia"].astype(int).unique().tolist())

    sql = text(
        f"""
        DELETE FROM {SCHEMA}.{TABELA_FATO}
        WHERE sk_tempo_referencia = ANY(:sks_tempo)
        """
    )

    with engine.begin() as conn:
        conn.execute(sql, {"sks_tempo": sks_tempo})


def inserir_fato(engine, df: pd.DataFrame) -> None:
    if df.empty:
        return

    df.to_sql(
        name=TABELA_FATO,
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
    if len(sys.argv) != 2:
        print("Uso: python3 load_fato_servidor.py /caminho/arquivo_servidores.csv")
        return 1

    arquivo_csv = Path(sys.argv[1])

    print("=" * 70)
    print("CARGA FATO_SERVIDOR")
    print("=" * 70)
    print(f"Arquivo origem: {arquivo_csv}")
    print(f"Destino       : {DB_NAME}.{SCHEMA}.{TABELA_FATO}")
    print("-" * 70)

    try:
        df = ler_csv(arquivo_csv)
        print(f"Linhas lidas: {len(df)}")

        df = preparar_dataframe(df)
        df["ARQUIVO_ORIGEM"] = str(arquivo_csv)

        print(f"Linhas após preparação: {len(df)}")
        print("Prévia da origem tratada:")
        print(
            df[
                [
                    "INSTANCIA",
                    "HOST_NAME",
                    "ANOMES",
                    "DATA_REFERENCIA",
                    "NK_SERVIDOR",
                    "TAMANHO_GB",
                    "DISPONIBILIDADE_PCT",
                ]
            ].head(10).to_string(index=False)
        )

        engine = criar_engine()

        garantir_dim_tempo(
            engine,
            pd.to_datetime(df["DATA_REFERENCIA"], errors="coerce"),
        )

        inserir_servidores_ausentes(engine, df)
        atualizar_servidores_existentes(engine, df)

        dim_servidor, dim_tempo = carregar_dimensoes_fato(engine)
        df = enriquecer_com_sks(df, dim_servidor, dim_tempo)

        df_fato = montar_fato(df)
        print(f"Linhas finais da fato_servidor: {len(df_fato)}")

        deletar_periodos_existentes(engine, df_fato)

        print("Prévia da carga:")
        print(df_fato.head(10).to_string(index=False))

        inserir_fato(engine, df_fato)

        print("-" * 70)
        print("Carga da fato_servidor concluída com sucesso.")
        return 0

    except Exception as e:
        print(f"ERRO: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
