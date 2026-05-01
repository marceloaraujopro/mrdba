#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
from pathlib import Path


# =========================================================
# CONFIGURAÇÃO
# =========================================================
BASE_DIR = Path("/dados/projetos/mrdba/scripts")

INGESTAO = BASE_DIR / "01_ingestao"
TRANSFORMACAO = BASE_DIR / "02_transformacao"
CARGA = BASE_DIR / "03_carga"


# =========================================================
# EXECUTOR
# =========================================================
def executar(nome, comando):
    print("\n" + "=" * 70)
    print(f"🚀 EXECUTANDO: {nome}")
    print("=" * 70)
    print("Comando:", " ".join(comando))
    print("-" * 70)

    resultado = subprocess.run(comando)

    if resultado.returncode != 0:
        print(f"\n❌ ERRO na etapa: {nome}")
        sys.exit(1)

    print(f"✅ OK: {nome}")


# =========================================================
# MAIN
# =========================================================
def main():

    if len(sys.argv) != 4:
        print("Uso: python3 run_pipeline_star.py YYYY MM caminho_servidores.csv")
        sys.exit(1)

    ano = sys.argv[1]
    mes = sys.argv[2]
    arquivo_servidores = sys.argv[3]

    # =====================================================
    # 1. INGESTÃO (tickets)
    # =====================================================
    executar(
        "EXTRAÇÃO TICKETS",
        ["python3", str(INGESTAO / "extrair_tickets_mes.py"), ano, mes]
    )

    # =====================================================
    # 2. STAGING
    # =====================================================
    executar(
        "JSON → STAGING",
        ["python3", str(TRANSFORMACAO / "json_to_staging_tickets.py"), ano, mes]
    )

    # =====================================================
    # 3. CURATED (STAR)
    # =====================================================
    executar(
        "STAGING → CURATED (STAR)",
        ["python3", str(TRANSFORMACAO / "staging_to_curated_tickets_star.py"), ano, mes]
    )

    # =====================================================
    # 4. DIMENSÕES
    # =====================================================
    executar(
        "DIM_TEMPO",
        ["python3", str(CARGA / "load_dim_tempo.py"), ano, mes]
    )

    executar(
        "DIM_CLIENTE",
        ["python3", str(CARGA / "load_dim_cliente.py"), ano, mes]
    )

    executar(
        "DIM_TIPO_TICKET",
        ["python3", str(CARGA / "load_dim_tipo_ticket.py"), ano, mes]
    )

    executar(
        "DIM_STATUS_TICKET",
        ["python3", str(CARGA / "load_dim_status_ticket.py"), ano, mes]
    )

    executar(
        "DIM_STATUS_CSI",
        ["python3", str(CARGA / "load_dim_status_csi.py"), ano, mes]
    )

    executar(
        "DIM_SERVIDOR",
        ["python3", str(CARGA / "load_dim_servidor.py"), ano, mes]
    )

    # =====================================================
    # 5. FATOS (tickets)
    # =====================================================
    executar(
        "FATO_TICKET",
        ["python3", str(CARGA / "load_fato_ticket.py"), ano, mes]
    )

    executar(
        "FATO_CSI",
        ["python3", str(CARGA / "load_fato_csi.py"), ano, mes]
    )

    # =====================================================
    # 6. SERVIDORES
    # =====================================================
    executar(
        "FATO_SERVIDOR",
        ["python3", str(CARGA / "load_fato_servidor.py"), arquivo_servidores]
    )

    print("\n" + "=" * 70)
    print("🎯 PIPELINE EXECUTADO COM SUCESSO")
    print("=" * 70)


if __name__ == "__main__":
    main()
