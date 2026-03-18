import sys
import pandas as pd
import re

# ==============================
# parâmetros
# ==============================
if len(sys.argv) != 3:
    print("Uso: python staging_to_curated.py YYYY MM")
    sys.exit(1)

ano = sys.argv[1]
mes = sys.argv[2]

# ==============================
# caminhos
# ==============================
entrada = f"/dados/projetos/mrdba/data_lake/staging/mrdba_tickets_staging_{ano}_{mes}.csv"
saida = f"/dados/projetos/mrdba/data_lake/curated/mrdba_tickets_curated_{ano}_{mes}.csv"

# ==============================
# leitura
# ==============================
df = pd.read_csv(entrada)

# ==============================
# extrair servidor do subject
# ==============================
def extrair_servidor(subject):
    match = re.search(r"Server:\s*([\w\-]+)", str(subject))
    return match.group(1) if match else None

df["servidor"] = df["subject"].apply(extrair_servidor)

# ==============================
# tratamento de datas
# ==============================
df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")

# ==============================
# cálculo tempo de resolução
# ==============================
df["tempo_resolucao_horas"] = (
    df["updated_at"] - df["created_at"]
).dt.total_seconds() / 3600

# ==============================
# mapeamento de status e prioridade
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
df["prioridade"] = df["priority"].map(prioridade_map)

# ==============================
# renomear colunas (padrão DW)
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
# selecionar colunas finais
# ==============================
df_final = df[
    [
        "ticket_id",
        "data_abertura",
        "status",
        "prioridade",
        "tipo_ticket",
        "sgdb",
        "ambiente",
        "servidor",
        "tempo_resolucao_horas"
    ]
]

# ==============================
# limpeza básica
# ==============================
df_final = df_final.dropna(subset=["ticket_id"])
df_final = df_final.drop_duplicates(subset=["ticket_id"])

# ==============================
# salvar curated
# ==============================
df_final.to_csv(saida, index=False)

print(f"✅ CURATED criado: {saida}")
