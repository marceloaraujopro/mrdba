import sys
import pandas as pd
import json
import os

# ==============================
# validação de parâmetros
# ==============================
if len(sys.argv) != 3:
    print("Uso: python3 json_to_staging.py YYYY MM")
    sys.exit(1)

ano = sys.argv[1]
mes = sys.argv[2]

# ==============================
# caminhos
# ==============================
arquivo_json = f"/dados/projetos/mrdba/data_lake/01_raw/tickets/mrdba_tickets_{ano}_{mes}.json"
arquivo_saida = f"/dados/projetos/mrdba/data_lake/02_staging/tickets/mrdba_tickets_staging_{ano}_{mes}.csv"

if not os.path.exists(arquivo_json):
    print(f"❌ Arquivo não encontrado: {arquivo_json}")
    sys.exit(1)

# ==============================
# leitura do raw
# ==============================
with open(arquivo_json, "r", encoding="utf-8") as f:
    dados = json.load(f)

# ==============================
# normalização
# ==============================
df = pd.json_normalize(dados)

# ==============================
# seleção das colunas principais
# ==============================
colunas_desejadas = [
    "id",
    "company_id",
    "subject",
    "status",
    "priority",
    "type",
    "created_at",
    "updated_at",
    "custom_fields.cf_sgdb",
    "custom_fields.cf_ambiente",
    "custom_fields.cf_csi_status"
]

colunas_existentes = [c for c in colunas_desejadas if c in df.columns]
colunas_ausentes = [c for c in colunas_desejadas if c not in df.columns]

if colunas_ausentes:
    print("⚠️ Colunas ausentes no raw:")
    for c in colunas_ausentes:
        print(f"- {c}")

df = df[colunas_existentes].copy()

# ==============================
# salvar staging
# ==============================
os.makedirs(os.path.dirname(arquivo_saida), exist_ok=True)
df.to_csv(arquivo_saida, index=False)

print("✅ STAGING criado")
print(f"📋 Colunas finais: {list(df.columns)}")
print(f"📦 Total de registros: {len(df)}")
