import sys
import subprocess
from datetime import datetime
from pathlib import Path

# ==============================
# valida parâmetros
# ==============================
if len(sys.argv) != 3:
    print("Uso: python3 run_pipeline.py YYYY MM")
    sys.exit(1)

ano = sys.argv[1]
mes = sys.argv[2]

if not (ano.isdigit() and len(ano) == 4):
    print("Ano inválido. Use YYYY.")
    sys.exit(1)

if not (mes.isdigit() and 1 <= int(mes) <= 12):
    print("Mês inválido. Use valores de 01 a 12.")
    sys.exit(1)

mes = f"{int(mes):02d}"

BASE_DIR = Path("/dados/projetos/mrdba")
log_path = BASE_DIR / "logs" / "pipeline.log"
log_path.parent.mkdir(parents=True, exist_ok=True)

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
        if resultado.stdout:
            print(resultado.stdout)
        if resultado.stderr:
            print(resultado.stderr)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro na etapa: {nome}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)

        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"{datetime.now()} - PIPELINE ERRO - Etapa: {nome} - {ano}-{mes}\n")

        sys.exit(1)

# ==============================
# execução
# ==============================
inicio = datetime.now()

executar(
    "RAW → STAGING",
    ["python3", str(BASE_DIR / "scripts/transformacao/json_to_staging.py"), ano, mes]
)

executar(
    "STAGING → CURATED",
    ["python3", str(BASE_DIR / "scripts/transformacao/staging_to_curated.py"), ano, mes]
)

executar(
    "CURATED → DW",
    ["python3", str(BASE_DIR / "scripts/carga/load_dw.py"), ano, mes]
)

fim = datetime.now()
duracao = fim - inicio

# ==============================
# log
# ==============================
with open(log_path, "a", encoding="utf-8") as log:
    log.write(f"{inicio} - PIPELINE SUCESSO - {ano}-{mes} - duração: {duracao}\n")

print("\n✅ Pipeline concluído com sucesso!")
print(f"⏱️ Duração: {duracao}")
