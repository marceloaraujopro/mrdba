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

if not (mes.isdigit() and 1 <= int(mes) <= 12):
    print("Mês inválido. Use valores de 01 a 12.")
    sys.exit(1)

print(f"🚀 Iniciando pipeline para {ano}-{mes}")

# ==============================
# função de execução segura
# ==============================
def executar(nome, comando):
    print(f"\n🔄 Etapa: {nome}")
    try:
        resultado = subprocess.run(
            comando,
            check=True,
            text=True,
            capture_output=True
        )
        print(resultado.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na etapa: {nome}")
        print(e.stderr)
        sys.exit(1)

# ==============================
# execução
# ==============================
inicio = datetime.now()

executar(
    "RAW → STAGING",
    ["python", "/dados/projetos/mrdba/scripts/transformacao/json_to_staging.py", ano, mes]
)

executar(
    "STAGING → CURATED",
    ["python", "/dados/projetos/mrdba/scripts/transformacao/staging_to_curated.py", ano, mes]
)

executar(
    "CURATED → DW",
    ["python", "/dados/projetos/mrdba/scripts/carga/load_dw.py", ano, mes]
)

fim = datetime.now()

# ==============================
# log
# ==============================
duracao = fim - inicio

with open("../../logs/pipeline.log", "a") as log:
    log.write(f"{inicio} - Pipeline {ano}-{mes} executado em {duracao}\n")

print("\n✅ Pipeline concluído com sucesso!")
print(f"⏱️ Duração: {duracao}")
