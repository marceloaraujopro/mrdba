import sys
import pandas as pd
import re
import os

# ==============================
# validação de parâmetros
# ==============================
if len(sys.argv) != 3:
    print("Uso: python staging_to_curated_v3.py YYYY MM")
    sys.exit(1)

ano = sys.argv[1]
mes = sys.argv[2]

# ==============================
# caminhos
# ==============================
entrada = f"/dados/projetos/mrdba/data_lake/staging/tickets/mrdba_tickets_staging_{ano}_{mes}.csv"
saida = f"/dados/projetos/mrdba/data_lake/curated/tickets/mrdba_tickets_curated_{ano}_{mes}.csv"

# ==============================
# valida arquivo de entrada
# ==============================
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
# valida colunas obrigatórias
# ==============================
colunas_obrigatorias = ["id", "subject", "status", "priority", "created_at", "updated_at"]

for col in colunas_obrigatorias:
    if col not in df.columns:
        print(f"❌ Coluna obrigatória ausente: {col}")
        sys.exit(1)

# ==============================
# evitar duplicidade prioridade
# ==============================
if "prioridade" in df.columns:
    df = df.drop(columns=["prioridade"])

# ==============================
# mapeamento status e prioridade
# ==============================
status_map = {
    1: "Aberto",
    2: "Resolvido",
    3: "Fechado",
    4: "Em Execução",
    5: "Aguardando o cliente",
    6: "Waiting on Third Party",
    7: "Em análise",
    8: "Fechamento automático"
}

prioridade_map = {
    1: "Baixa",
    2: "Média",
    3: "Alta",
    4: "Urgente"
}

df["status"] = df["status"].map(status_map)
df["priority"] = df["priority"].map(prioridade_map)

# ==============================
# funções de extração
# ==============================
def extrair_servidor(subject):
    match = re.search(r"Server:\s*([\w\-\\]+)", str(subject))
    return match.group(1) if match else None

def extrair_cliente(subject):
    subject = str(subject)

    # remove prefixos técnicos
    subject = re.sub(r"^(INFO|ALERT|CLEAR):\s*", "", subject)

    # padrão CLIENTE - resto
    if " - " in subject:
        return subject.split(" - ")[0].strip()

    return None

# ==============================
# aplicar extrações
# ==============================
df["servidor"] = df["subject"].apply(extrair_servidor)
df["cliente"] = df["subject"].apply(extrair_cliente)

# ==============================
# normalização cliente
# ==============================
df["cliente"] = df["cliente"].str.upper().str.strip()
df["cliente"] = df["cliente"].fillna("NAO IDENTIFICADO")

# ==============================
# tratamento de datas
# ==============================
df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")

# ==============================
# cálculo tempo resolução
# ==============================
df["tempo_resolucao_horas"] = (
    df["updated_at"] - df["created_at"]
).dt.total_seconds() / 3600

# ==============================
# renomeação padrão DW
# ==============================
df = df.rename(columns={
    "id": "ticket_id",
    "created_at": "data_abertura",
    "priority": "prioridade",
    "type": "tipo_ticket",
    "custom_fields.cf_sgdb": "sgdb",
    "custom_fields.cf_ambiente": "ambiente"
})

# ==============================
# valida colunas finais
# ==============================
colunas_finais = [
    "ticket_id",
    "data_abertura",
    "status",
    "prioridade",
    "tipo_ticket",
    "cliente",
    "sgdb",
    "ambiente",
    "servidor",
    "tempo_resolucao_horas"
]

for col in colunas_finais:
    if col not in df.columns:
        print(f"❌ Coluna final ausente: {col}")
        sys.exit(1)

# ==============================
# seleção final
# ==============================
df_final = df[colunas_finais]

# ==============================
# limpeza
# ==============================
df_final = df_final.dropna(subset=["ticket_id"])
df_final = df_final.drop_duplicates(subset=["ticket_id"])

# ==============================
# salvar (overwrite)
# ==============================
df_final.to_csv(saida, index=False)

print(f"✅ CURATED gerado com sucesso: {saida}")
print(f"📦 Total de registros: {len(df_final)}")
