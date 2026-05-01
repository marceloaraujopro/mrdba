import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# ==============================
# valida parâmetros
# ==============================
if len(sys.argv) != 3:
    print("Uso: python3 load_dw.py YYYY MM")
    sys.exit(1)

ano = sys.argv[1]
mes = sys.argv[2]
mes_ref = f"{ano}_{mes}"

# ==============================
# caminhos
# ==============================
BASE_DIR = "/dados/projetos/mrdba"
arquivo_curated = f"{BASE_DIR}/data_lake/curated/tickets/mrdba_tickets_curated_{mes_ref}.csv"
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
# valida colunas do curated
# ==============================
colunas_esperadas = [
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

for col in colunas_esperadas:
    if col not in df.columns:
        print(f"❌ Coluna obrigatória ausente no curated: {col}")
        sys.exit(1)

# ==============================
# tratamento
# ==============================
df["id_ticket"] = pd.to_numeric(df["id_ticket"], errors="coerce")
df = df.dropna(subset=["id_ticket"])
df["id_ticket"] = df["id_ticket"].astype("int64")

df["data_criacao"] = pd.to_datetime(df["data_criacao"], errors="coerce").dt.date
df["data_ultima_alteracao"] = pd.to_datetime(df["data_ultima_alteracao"], errors="coerce").dt.date

colunas_texto = [
    "empresa",
    "tipo_ticket",
    "status_ticket",
    "foi_atuado",
    "titulo_ticket",
    "csi_status"
]

for col in colunas_texto:
    df[col] = df[col].fillna("").astype(str).str.strip()

df_final = df[colunas_esperadas].copy()

# ==============================
# diagnóstico
# ==============================
print("🔎 Prévia dos dados:")
print(df_final.head(5))

print("\n🔎 Tipos das colunas:")
print(df_final.dtypes)

print(f"\n🔎 Total de registros para carga: {len(df_final)}")

# ==============================
# carga + log
# ==============================
status_execucao = "SUCESSO"

try:
    with engine.begin() as conn:
        print("🧹 Removendo dados do mês (se existirem)...")

        conn.execute(
            text("""
                DELETE FROM dw.fato_tickets
                WHERE date_trunc('month', data_criacao) = :data_ref
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
    status_execucao = f"ERRO: {e}"
    raise

finally:
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"{datetime.now()} - CARGA DW - {status_execucao} - {ano}-{mes}\n")
