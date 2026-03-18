import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# ==============================
# valida parâmetros
# ==============================
if len(sys.argv) != 3:
    print("Uso: python load_dw_v3.py YYYY MM")
    sys.exit(1)

ano = sys.argv[1]
mes = sys.argv[2]

mes_ref = f"{ano}_{mes}"

# ==============================
# caminhos
# ==============================
arquivo_curated = f"../../data_lake/curated/tickets/mrdba_tickets_curated_{mes_ref}.csv"

BASE_DIR = "/dados/projetos/mrdba"
log_path = f"{BASE_DIR}/logs/pipeline.log"
os.makedirs(os.path.dirname(log_path), exist_ok=True)

# ==============================
# conexão com postgres
# ==============================
engine = create_engine(
    "postgresql://marcelo:1234@localhost:5432/db_mrdba"
)

# ==============================
# leitura do arquivo
# ==============================
try:
    df = pd.read_csv(arquivo_curated)
except FileNotFoundError:
    print(f"❌ Arquivo não encontrado: {arquivo_curated}")
    sys.exit(1)

# ==============================
# tratamento
# ==============================
df = df.rename(columns={
    "id": "ticket_id",
    "priority": "prioridade",
    "type": "tipo_ticket",
    "custom_fields.cf_sgdb": "sgdb",
    "custom_fields.cf_ambiente": "ambiente"
})

if "data_abertura" in df.columns:
    df["data_abertura"] = pd.to_datetime(df["data_abertura"], utc=True, errors="coerce")
    df["data_abertura"] = df["data_abertura"].dt.tz_localize(None)
else:
    df["data_abertura"] = pd.NaT

colunas_esperadas = [
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

for col in colunas_esperadas:
    if col not in df.columns:
        df[col] = None

df_final = df[colunas_esperadas].copy()

# ==============================
# diagnóstico
# ==============================
print("🔎 Prévia dos dados:")
print(df_final.head(5))

print("\n🔎 Tipos das colunas:")
print(df_final.dtypes)

print(f"\n🔎 Valores nulos em data_abertura: {df_final['data_abertura'].isna().sum()}")

# ==============================
# carga + log
# ==============================
status = "SUCESSO"

try:
    with engine.begin() as conn:
        print("🧹 Removendo dados do mês (se existirem)...")

        conn.execute(
            text("""
                DELETE FROM dw.fato_tickets
                WHERE date_trunc('month', data_abertura) = :data_ref
            """),
            {"data_ref": f"{ano}-{mes}-01"}
        )

        print("📦 Inserindo novos dados...")

        df_final.to_sql(
            "fato_tickets",
            conn,
            schema="dw",
            if_exists="append",
            index=False
        )

    print(f"✅ Carga do mês {ano}-{mes} concluída com sucesso!")

except Exception as e:
    print(f"❌ Erro na carga: {e}")
    status = f"ERRO: {e}"
    raise

finally:
    with open(log_path, "a") as log:
        log.write(f"{datetime.now()} - {status} - {ano}-{mes}\n")
