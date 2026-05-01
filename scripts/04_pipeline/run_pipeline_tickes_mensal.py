#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
from pathlib import Path
from datetime import datetime


BASE_DIR = Path("/dados/projetos/mrdba/scripts")

INGESTAO = BASE_DIR / "01_ingestao"
TRANSFORMACAO = BASE_DIR / "02_transformacao"
CARGA = BASE_DIR / "03_carga"

LOG_FILE = Path("/dados/projetos/mrdba/logs/pipeline_tickets.log")


def log(msg):
    linha = f"{datetime.now()} - {msg}"
    print(linha)
    with open(LOG_FILE, "a") as f:
        f.write(linha + "\n")


def executar(nome, comando):
    log("=" * 70)
    log(f"EXECUTANDO: {nome}")
    log(" ".join(comando))

    resultado = subprocess.run(comando)

    if resultado.returncode != 0:
        log(f"ERRO: {nome}")
        sys.exit(1)

    log(f"OK: {nome}")


def main():

    if len(sys.argv) != 3:
        print("Uso: python3 run_pipeline_tickets_mensal_v2.py YYYY MM")
        sys.exit(1)

    ano = sys.argv[1]
    mes = sys.argv[2].zfill(2)

    log("=" * 70)
    log(f"PIPELINE TICKETS {ano}-{mes}")
    log("=" * 70)

    # 1. EXTRAÇÃO
    executar(
        "EXTRAÇÃO TICKETS",
        ["python3", str(INGESTAO / "extrair_tickets_mes.py"), ano, mes]
    )

    # 2. STAGING
    executar(
        "JSON → STAGING",
        ["python3", str(TRANSFORMACAO / "json_to_staging_tickets.py"), ano, mes]
    )

    # 3. CURATED
    executar(
        "STAGING → CURATED (STAR)",
        ["python3", str(TRANSFORMACAO / "staging_to_curated_tickets_star.py"), ano, mes]
    )

    # 4. DIMENSÕES (ordem correta)
    executar("DIM_TEMPO", ["python3", str(CARGA / "load_dim_tempo.py"), ano, mes])
    executar("DIM_CLIENTE", ["python3", str(CARGA / "load_dim_cliente.py"), ano, mes])
    executar("DIM_TIPO_TICKET", ["python3", str(CARGA / "load_dim_tipo_ticket.py"), ano, mes])
    executar("DIM_STATUS_TICKET", ["python3", str(CARGA / "load_dim_status_ticket.py"), ano, mes])
    executar("DIM_STATUS_CSI", ["python3", str(CARGA / "load_dim_status_csi.py"), ano, mes])
    executar("DIM_SERVIDOR", ["python3", str(CARGA / "load_dim_servidor.py"), ano, mes])

    # 5. FATOS
    executar("FATO_TICKET", ["python3", str(CARGA / "load_fato_ticket.py"), ano, mes])
    executar("FATO_CSI", ["python3", str(CARGA / "load_fato_csi.py"), ano, mes])

    log("=" * 70)
    log("PIPELINE FINALIZADO COM SUCESSO")
    log("=" * 70)


if __name__ == "__main__":
    main()
