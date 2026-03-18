import sys
import subprocess
from datetime import datetime

# ==============================
# valida parâmetros
# ==============================
if len(sys.argv) != 3:
    print("Uso: python run_pipeline.py YYYY MM")
    sys.exit(1)

ano = sys.argv[1]
mes = sys.argv[2]

# ==============================
# função para executar etapas
# ==============================
def executar_etapa(nome_etapa, comando):
    print(f"\n🔄 Iniciando etapa: {nome_etapa}")

    try:
        resultado = subprocess.run(
            comando,
            check=True,
            text=True,
            capture_output=True
        )
        print(resultado.stdout)

    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na etapa: {nome_etapa}")
        print(e.stderr)
        sys.exit(1)

# ==============================
# pipeline
# ==============================
inicio = datetime.now()

executar_etapa(
    "JSON → STAGING",
    ["python", "../transformacao/json_to_staging.py", ano, mes]
)

executar_etapa(
    "STAGING → CURATED",
    ["python", "../transformacao/staging_to_curated.py", ano, mes]
)

executar_etapa(
    "CURATED → DW",
    ["python", "../carga/load_dw.py", ano, mes]
)

fim = datetime.now()

# ==============================
# log
# ==============================
duracao = fim - inicio

log_msg = f"{inicio} - Pipeline executado para {ano}-{mes} em {duracao}\n"

with open("../../logs/pipeline.log", "a") as log:
    log.write(log_msg)

print("\n✅ Pipeline executado com sucesso!")
print(f"⏱️ Duração: {duracao}")
