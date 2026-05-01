import sys
import pandas as pd
import re
import os

# ==============================
# validação de parâmetros
# ==============================
if len(sys.argv) != 3:
    print("Uso: python3 staging_to_curated.py YYYY MM")
    sys.exit(1)

ano = sys.argv[1]
mes = sys.argv[2]

# ==============================
# caminhos
# ==============================
entrada = f"/dados/projetos/mrdba/data_lake/staging/tickets/mrdba_tickets_staging_{ano}_{mes}.csv"
saida = f"/dados/projetos/mrdba/data_lake/curated/tickets/mrdba_tickets_curated_{ano}_{mes}.csv"

if not os.path.exists(entrada):
    print(f"❌ Arquivo não encontrado: {entrada}")
    sys.exit(1)

print(f"📥 Lendo arquivo: {entrada}")

# ==============================
# leitura
# ==============================
df = pd.read_csv(entrada)

print(f"📊 Colunas encontradas: {list(df.columns)}")

# ==============================
# valida colunas mínimas
# ==============================
colunas_obrigatorias = ["id", "status", "created_at", "updated_at"]

for col in colunas_obrigatorias:
    if col not in df.columns:
        print(f"❌ Coluna obrigatória ausente: {col}")
        sys.exit(1)

# ==============================
# mapeamento status
# ==============================
status_map = {
    1: "outros",
    2: "aberto",
    3: "outros",
    4: "outros",
    5: "fechado",
    6: "outros",
    7: "outros",
    8: "outros"
}

if pd.api.types.is_numeric_dtype(df["status"]):
    df["status"] = df["status"].map(status_map)

df["status"] = (
    df["status"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)

# ==============================
# tratamento de datas
# ==============================
df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")

def formatar_data(data):
    if pd.isna(data):
        return ""
    return data.strftime("%Y-%m-%d")

# ==============================
# padronização do tipo_ticket
# ==============================
def padronizar_tipo_ticket(valor, subject=""):
    valor = "" if pd.isna(valor) else str(valor).strip().lower()
    subject_txt = "" if pd.isna(subject) else str(subject).strip().lower()

    mapa = {
        "csi": "CSI",
        "checklist": "Checklist",
        "incidente": "Incidentes",
        "incidentes": "Incidentes",
        "crise": "CRISE"
    }

    if valor in mapa:
        return mapa[valor]

    if subject_txt.startswith("csi"):
        return "CSI"
    if "checklist" in subject_txt or "health check" in subject_txt or "server summary" in subject_txt:
        return "Checklist"
    if subject_txt.startswith("alert:") or subject_txt.startswith("clear:") or "alerta de restart" in subject_txt:
        return "Incidentes"

    return str(valor).strip() if valor else ""

if "type" in df.columns:
    df["tipo_ticket"] = df.apply(
        lambda row: padronizar_tipo_ticket(row.get("type"), row.get("subject")),
        axis=1
    )
else:
    df["tipo_ticket"] = df["subject"].apply(lambda x: padronizar_tipo_ticket("", x)) if "subject" in df.columns else ""

# ==============================
# empresa via company_id
# ==============================
MAPA_COMPANY_ID_PARA_NOME = {
    72000664348: "Mills",
    72001771221: "Senac",
    72000835424: "A Nossa Drogaria",
    72000747023: "Secretaria da Saúde do Rio de Janeiro - SES",
}

def normalizar_nome_empresa(nome):
    if nome is None:
        return ""

    texto = str(nome).strip().upper()

    if texto == "MILLS":
        return "MILLS"

    if texto == "SENAC":
        return "SENAC"

    if texto in {"A NOSSA DROGARIA", "AND"}:
        return "AND"

    if texto in {
        "SECRETARIA DA SAÚDE DO RIO DE JANEIRO",
        "SECRETARIA DA SAUDE DO RIO DE JANEIRO",
        "SECRETARIA DA SAÚDE DO RIO DE JANEIRO - SES",
        "SECRETARIA DA SAUDE DO RIO DE JANEIRO - SES",
        "SES"
    }:
        return "SES"

    return ""

def obter_empresa_por_company_id(company_id):
    if pd.isna(company_id):
        return ""

    try:
        company_id = int(company_id)
    except (ValueError, TypeError):
        return ""

    nome_empresa = MAPA_COMPANY_ID_PARA_NOME.get(company_id)
    return normalizar_nome_empresa(nome_empresa)

if "company_id" in df.columns:
    df["empresa"] = df["company_id"].apply(obter_empresa_por_company_id)
else:
    df["empresa"] = ""

# ==============================
# titulo_ticket
# regra:
# - se for CSI, mantém o subject completo
# - caso contrário, aplica limpeza
# ==============================
def limpar_titulo_ticket(subject, tipo_ticket):
    if pd.isna(subject):
        return ""

    texto = str(subject).strip()
    tipo = "" if pd.isna(tipo_ticket) else str(tipo_ticket).strip().lower()

    if tipo == "csi":
        return texto

    texto = re.sub(r"^(INFO(?:\s+\w+)?)\s*:\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"^(ALERT|CLEAR)\s*:\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"^(Mills|A Nossa Drogaria)\s*-\s*", "", texto, flags=re.IGNORECASE)

    return texto.strip()

if "subject" in df.columns:
    df["titulo_ticket"] = df.apply(
        lambda row: limpar_titulo_ticket(row.get("subject"), row.get("tipo_ticket")),
        axis=1
    )
else:
    df["titulo_ticket"] = ""

# ==============================
# campos derivados
# ==============================
df["data_criacao"] = df["created_at"].apply(formatar_data).astype(str)
df["data_ultima_alteracao"] = df["updated_at"].apply(formatar_data).astype(str)

df["foi_atuado"] = df.apply(
    lambda row: "sim"
    if pd.notna(row["updated_at"]) and pd.notna(row["created_at"]) and row["updated_at"] > row["created_at"]
    else "não",
    axis=1
)

# ==============================
# csi_status
# regra:
# - se tipo_ticket for CSI, usa o campo da origem
# - caso contrário, preenche com "na"
# ==============================
if "custom_fields.cf_csi_status" in df.columns:
    df["csi_status"] = df.apply(
        lambda row: (
            str(row["custom_fields.cf_csi_status"]).strip().lower()
            if pd.notna(row["custom_fields.cf_csi_status"]) and str(row["tipo_ticket"]).strip().upper() == "CSI"
            else "na"
        ),
        axis=1
    )
else:
    df["csi_status"] = df["tipo_ticket"].apply(
        lambda x: "" if str(x).strip().upper() == "CSI" else "na"
    )

# ==============================
# renomeação final
# ==============================
df = df.rename(columns={
    "id": "id_ticket",
    "status": "status_ticket"
})

# ==============================
# conversão do id_ticket
# ==============================
df["id_ticket"] = pd.to_numeric(df["id_ticket"], errors="coerce")

# ==============================
# seleção final
# ==============================
colunas_finais = [
    "id_ticket",
    "empresa",
    "data_criacao",
    "data_ultima_alteracao",
    "tipo_ticket",
    "status_ticket",
    "foi_atuado",
    "titulo_ticket",
    "csi_status"
]

for col in colunas_finais:
    if col not in df.columns:
        print(f"❌ Coluna final ausente: {col}")
        sys.exit(1)

df_final = df[colunas_finais].copy()

# ==============================
# limpeza
# ==============================
df_final = df_final.dropna(subset=["id_ticket"])
df_final["id_ticket"] = df_final["id_ticket"].astype(int)
df_final = df_final.drop_duplicates(subset=["id_ticket"])

colunas_texto = [
    "empresa",
    "data_criacao",
    "data_ultima_alteracao",
    "tipo_ticket",
    "status_ticket",
    "foi_atuado",
    "titulo_ticket",
    "csi_status"
]

for col in colunas_texto:
    df_final[col] = df_final[col].fillna("").astype(str).str.strip()

# ==============================
# salvar
# ==============================
os.makedirs(os.path.dirname(saida), exist_ok=True)
df_final.to_csv(saida, index=False)

print(f"✅ CURATED gerado com sucesso: {saida}")
print(f"📦 Total de registros: {len(df_final)}")
print("📋 Colunas finais:", list(df_final.columns))
print("\n🔎 Prévia dos dados:")
print(df_final.head(20))
