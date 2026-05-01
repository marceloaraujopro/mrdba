#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from pathlib import Path
import pandas as pd

BASE_DIR = Path("/dados/projetos/mrdba")
DIR_STAGING = BASE_DIR / "data_lake" / "02_staging" / "tickets"
DIR_CURATED = BASE_DIR / "data_lake" / "03_curated" / "tickets"

DIR_CURATED.mkdir(parents=True, exist_ok=True)

STATUS_MAP = {
    1: "Aberto",
    2: "Resolvido",
    3: "Aguardando o cliente",
    4: "Em Execução",
    5: "Fechado",
    6: "Aguardando terceiros",
    7: "Em análise",
    8: "Fechamento automático",
}

EMPRESA_MAP = {
    72000664348: "MILLS",
    72001771221: "SENAC",
    72000835424: "AND",
    72000747023: "SES",
}


def normalizar_texto(valor):
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def normalizar_minusculo_sem_espacos(valor):
    return normalizar_texto(valor).lower().strip()


def normalizar_data(coluna):
    return pd.to_datetime(coluna, errors="coerce").dt.strftime("%Y-%m-%d")


def mapear_status(valor):
    if pd.isna(valor):
        return "Outros"
    try:
        return STATUS_MAP.get(int(valor), "Outros")
    except Exception:
        return str(valor).strip()


def detectar_tipo_ticket(subject):
    s = normalizar_minusculo_sem_espacos(subject)

    if "csi" in s:
        return "CSI"
    if "crise" in s:
        return "CRISE"
    if "checklist" in s or "health check" in s or "server summary" in s:
        return "Checklist"
    if "incidente" in s or s.startswith("alert:") or s.startswith("clear:") or "alerta de restart" in s:
        return "Incidente"

    return "Outros"


def mapear_empresa(df):
    empresa = pd.Series([""] * len(df), index=df.index, dtype="object")

    if "company_id" in df.columns:
        empresa = df["company_id"].map(EMPRESA_MAP).fillna("")

    if "subject" in df.columns:
        subj = df["subject"].fillna("").astype(str)

        empresa = empresa.mask(
            empresa.eq("") & subj.str.contains(r"\bMILLS\b", case=False, regex=True),
            "MILLS"
        )
        empresa = empresa.mask(
            empresa.eq("") & subj.str.contains(r"\bSENAC\b", case=False, regex=True),
            "SENAC"
        )
        empresa = empresa.mask(
            empresa.eq("") & subj.str.contains(r"\bAND\b|\bA NOSSA DROGARIA\b", case=False, regex=True),
            "AND"
        )
        empresa = empresa.mask(
            empresa.eq("") & subj.str.contains(r"\bSES\b|\bSECRETARIA DA SAUDE\b|\bSECRETARIA DA SAÚDE\b", case=False, regex=True),
            "SES"
        )

    return empresa


def extrair_csi_status(valor, tipo_ticket=""):
    if str(tipo_ticket).strip().upper() != "CSI":
        return "na"

    v = normalizar_texto(valor)
    return v if v else ""


def limpar_titulo_ticket(subject, tipo_ticket):
    s = normalizar_texto(subject)
    if not s:
        return ""

    if tipo_ticket == "CSI":
        return re.sub(r"\s+", " ", s).strip()

    s = re.sub(r"^(INFO(?:\s+\w+)?)\s*:\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^(ALERT|CLEAR)\s*:\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^(Mills|A Nossa Drogaria|AND|SES|Senac)\s*-\s*", "", s, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", s).strip()


def normalizar_sgdb(valor, subject=""):
    v = normalizar_texto(valor).upper()

    if v:
        return v

    s = normalizar_texto(subject).upper()

    if "ORACLE" in s:
        return "ORACLE"
    if "SQL SERVER" in s or "SQLSERVER" in s:
        return "SQL SERVER"
    if "POSTGRES" in s or "POSTGRESQL" in s:
        return "POSTGRESQL"
    if "MYSQL" in s:
        return "MYSQL"
    if "MONGODB" in s or "MONGO" in s:
        return "MONGODB"

    return ""


def normalizar_ambiente(valor):
    v = normalizar_texto(valor)
    if not v:
        return ""

    v_upper = v.upper()

    if v_upper in {"PRD", "PROD", "PRODUCAO", "PRODUÇÃO"}:
        return "Produção"
    if v_upper in {"HML", "HOMOLOG", "HOMOLOGACAO", "HOMOLOGAÇÃO"}:
        return "Homologação"
    if v_upper in {"DEV", "DESENV", "DESENVOLVIMENTO"}:
        return "Desenvolvimento"
    if v_upper in {"TESTE", "TESTES", "QA"}:
        return "Teste"
    if v_upper in {"OUTRO", "OUTROS"}:
        return "Outro"

    return v


def extrair_instancia(subject):
    s = normalizar_texto(subject)
    if not s:
        return ""

    match = re.search(r"\(([^)]+)\)", s)
    if match:
        return match.group(1).strip().upper()

    return ""


def extrair_nome_servidor(subject):
    s = normalizar_texto(subject)
    if not s:
        return ""

    padroes = [
        r"(?i)\bServer\s*[:\-]\s*([A-Z0-9._\-]+)",
        r"(?i)\bHost\s*[:\-]\s*([A-Z0-9._\-]+)",
        r"(?i)\bServidor\s*[:\-]\s*([A-Z0-9._\-]+)",
        r"(?i)\bInst[aâ]ncia\s*[:\-]\s*([A-Z0-9._\-]+)",
        r"(?i)\bDatabase\s*[:\-]\s*([A-Z0-9._\-]+)",
        r"(?i)\bDB\s*[:\-]\s*([A-Z0-9._\-]+)",
        r"(?i)^([A-Z0-9._\-]{5,})\s*-\s*",
        r"(?i)-\s*([A-Z0-9._\-]{5,})\s*\(",
    ]

    termos_invalidos = {
        "CHECKLIST", "ORACLE", "SERVER", "SUMMARY", "HEALTH",
        "DIARIO", "DIÁRIO", "CSI", "CRISE", "INCIDENTE",
        "MILLS", "SENAC", "SES", "AND", "MCP", "NOSSA",
        "ALERTA", "ALERT", "CLEAR", "DATABASE", "CAPACIDADE",
        "SQL", "SQLSERVER", "POSTGRES", "POSTGRESQL", "MYSQL",
        "MONGODB", "STORAGE", "BANCO", "GESTAO", "GESTÃO",
        "SAP", "ANALISE", "ANÁLISE", "APOIO", "CARGA",
        "CARREGAR", "LOGFILE", "RECARGA", "RELEASE",
        "REPLICAR", "SENHA", "BACKUP", "RESTORE", "ERRO",
        "FALHA", "ACESSO", "USUARIO", "USUÁRIO", "PERMISSAO",
        "PERMISSÃO", "TABELA", "INDICE", "ÍNDICE"
    }

    def candidato_valido(valor):
        candidato = str(valor).strip().upper()
        candidato = re.sub(r"\s+", " ", candidato)

        if not candidato:
            return ""

        if candidato in termos_invalidos:
            return ""

        if len(candidato) < 5:
            return ""

        # Evita capturar palavras comuns como ANALISE, CARGA, SENHA, RELEASE.
        # Um nome técnico de servidor normalmente tem número, ponto, hífen ou underline.
        if not re.search(r"[0-9._\-]", candidato):
            return ""

        return candidato

    for padrao in padroes:
        achados = re.findall(padrao, s)
        if not achados:
            continue

        for item in achados:
            candidato = candidato_valido(item)
            if candidato:
                return candidato

    return ""


def definir_servidor_logico(subject):
    nome_servidor = extrair_nome_servidor(subject)
    instancia = extrair_instancia(subject)

    if nome_servidor:
        return nome_servidor, instancia

    if instancia:
        return instancia, instancia

    return "", ""


def construir_nk_servidor(nome_servidor):
    nome_servidor = normalizar_texto(nome_servidor).upper()
    nome_servidor = re.sub(r"\s+", " ", nome_servidor)

    if not nome_servidor:
        return ""

    return nome_servidor


def calcular_tempo_resolucao_horas(created_at, updated_at):
    if pd.isna(created_at) or pd.isna(updated_at):
        return None

    diferenca = (updated_at - created_at).total_seconds() / 3600

    if diferenca < 0:
        return None

    return round(diferenca, 2)


def main():
    if len(sys.argv) != 3:
        print("Uso: python staging_to_curated_tickets_star_v3.py <ano> <mes>")
        sys.exit(1)

    ano = sys.argv[1]
    mes = sys.argv[2].zfill(2)

    arquivo_staging = DIR_STAGING / f"mrdba_tickets_staging_{ano}_{mes}.csv"
    arquivo_curated = DIR_CURATED / f"mrdba_tickets_curated_{ano}_{mes}.csv"

    print("=" * 70)
    print("TRANSFORMAÇÃO STAGING -> CURATED (STAR V3)")
    print("=" * 70)
    print(f"Arquivo staging : {arquivo_staging}")
    print(f"Arquivo curated : {arquivo_curated}")
    print("-" * 70)

    if not arquivo_staging.exists():
        print(f"ERRO: arquivo staging não encontrado: {arquivo_staging}")
        sys.exit(1)

    try:
        df = pd.read_csv(arquivo_staging)
        if len(df.columns) == 1:
            df = pd.read_csv(arquivo_staging, sep=";")
    except Exception:
        df = pd.read_csv(arquivo_staging, sep=";")

    print(f"Linhas lidas do staging: {len(df)}")
    print(f"Colunas encontradas: {df.columns.tolist()}")
    print("-" * 70)

    colunas_obrigatorias = ["id", "subject", "status", "created_at", "updated_at"]
    faltantes = [c for c in colunas_obrigatorias if c not in df.columns]
    if faltantes:
        print(f"ERRO: colunas obrigatórias ausentes no staging: {faltantes}")
        sys.exit(1)

    curated = pd.DataFrame()

    curated["id_ticket"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    curated["empresa"] = mapear_empresa(df)
    curated["data_criacao"] = normalizar_data(df["created_at"])
    curated["data_ultima_alteracao"] = normalizar_data(df["updated_at"])
    curated["tipo_ticket"] = df["subject"].apply(detectar_tipo_ticket)
    curated["status_ticket"] = df["status"].apply(mapear_status)

    dt_created = pd.to_datetime(df["created_at"], errors="coerce")
    dt_updated = pd.to_datetime(df["updated_at"], errors="coerce")

    curated["foi_atuado"] = (dt_updated > dt_created).map({True: "sim", False: "nao"})
    curated["tempo_resolucao_horas"] = [
        calcular_tempo_resolucao_horas(created_at, updated_at)
        for created_at, updated_at in zip(dt_created, dt_updated)
    ]

    curated["titulo_ticket"] = [
        limpar_titulo_ticket(subject, tipo)
        for subject, tipo in zip(df["subject"], curated["tipo_ticket"])
    ]

    if "custom_fields.cf_csi_status" in df.columns:
        curated["csi_status"] = [
            extrair_csi_status(valor, tipo)
            for valor, tipo in zip(df["custom_fields.cf_csi_status"], curated["tipo_ticket"])
        ]
    else:
        curated["csi_status"] = ["na" if tipo != "CSI" else "" for tipo in curated["tipo_ticket"]]

    if "custom_fields.cf_sgdb" in df.columns:
        curated["sgdb"] = [
            normalizar_sgdb(sgdb, subject)
            for sgdb, subject in zip(df["custom_fields.cf_sgdb"], df["subject"])
        ]
    else:
        curated["sgdb"] = df["subject"].apply(lambda x: normalizar_sgdb("", x))

    if "custom_fields.cf_ambiente" in df.columns:
        curated["ambiente"] = df["custom_fields.cf_ambiente"].apply(normalizar_ambiente)
    else:
        curated["ambiente"] = ""

    servidores_extraidos = df["subject"].apply(definir_servidor_logico)
    curated["nome_servidor"] = servidores_extraidos.apply(lambda x: x[0])
    curated["instancia"] = servidores_extraidos.apply(lambda x: x[1])
    curated["nk_servidor"] = curated["nome_servidor"].apply(construir_nk_servidor)

    curated["empresa"] = curated["empresa"].fillna("").astype(str).str.strip().str.upper()
    curated["csi_status"] = curated["csi_status"].fillna("na").astype(str).str.strip()
    curated["sgdb"] = curated["sgdb"].fillna("").astype(str).str.strip()
    curated["ambiente"] = curated["ambiente"].fillna("").astype(str).str.strip()
    curated["nome_servidor"] = curated["nome_servidor"].fillna("").astype(str).str.strip()
    curated["instancia"] = curated["instancia"].fillna("").astype(str).str.strip()
    curated["nk_servidor"] = curated["nk_servidor"].fillna("").astype(str).str.strip()

    colunas_finais = [
        "id_ticket",
        "empresa",
        "data_criacao",
        "data_ultima_alteracao",
        "tipo_ticket",
        "status_ticket",
        "foi_atuado",
        "titulo_ticket",
        "csi_status",
        "sgdb",
        "ambiente",
        "nome_servidor",
        "instancia",
        "nk_servidor",
        "tempo_resolucao_horas",
    ]

    curated = curated[colunas_finais].copy()
    curated = curated[curated["id_ticket"].notna()].copy()
    curated = curated.drop_duplicates(subset=["id_ticket"])

    curated.to_csv(arquivo_curated, index=False)

    print(f"Linhas gravadas no curated: {len(curated)}")
    print("Prévia:")
    print(curated.head(10).to_string(index=False))
    print("-" * 70)
    print("Curated V3 gerado com sucesso.")


if __name__ == "__main__":
    main()
