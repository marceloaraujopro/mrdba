import os
import sys
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FRESHDESK_API_KEY")
DOMAIN = os.getenv("FRESHDESK_DOMAIN")  # ex: mrdba-help.freshdesk.com

if not API_KEY or not DOMAIN:
    raise ValueError(
        "Variáveis FRESHDESK_API_KEY e FRESHDESK_DOMAIN não encontradas no arquivo .env"
    )

if len(sys.argv) != 3:
    print("Uso: python3 extrair_tickets_mes.py <ano> <mes>")
    print("Exemplo: python3 extrair_tickets_mes.py 2026 01")
    sys.exit(1)

ano = int(sys.argv[1])
mes = int(sys.argv[2])

if mes < 1 or mes > 12:
    raise ValueError("O mês deve estar entre 1 e 12.")

# monta a data inicial do mês
data_inicio = f"{ano}-{mes:02d}-01"

# monta o primeiro dia do mês seguinte
if mes == 12:
    proximo_ano = ano + 1
    proximo_mes = 1
else:
    proximo_ano = ano
    proximo_mes = mes + 1

data_fim_exclusiva = f"{proximo_ano}-{proximo_mes:02d}-01"

# para query do Freshdesk, usamos:
# created_at > dia anterior ao início do mês
# created_at < primeiro dia do mês seguinte
if mes == 1:
    data_anterior = f"{ano-1}-12-31"
else:
    data_anterior = f"{ano}-{mes-1:02d}-31"

base_url = f"https://{DOMAIN}/api/v2/search/tickets"

raw_dir = Path("/dados/projetos/mrdba/data_lake/raw/tickets")
raw_dir.mkdir(parents=True, exist_ok=True)

arquivo_saida = raw_dir / f"mrdba_tickets_{ano}_{mes:02d}.json"

query = f"created_at:>'{data_anterior}' AND created_at:<'{data_fim_exclusiva}'"

print("=" * 60)
print("EXTRAÇÃO DE TICKETS - FRESHDESK")
print("=" * 60)
print(f"Domínio: {DOMAIN}")
print(f"Período de abertura: {data_inicio} até {data_fim_exclusiva} (limite final exclusivo)")
print(f"Query: {query}")
print(f"Arquivo de saída: {arquivo_saida}")
print("=" * 60)

todos_tickets = []
page = 1

while True:
    params = {
        "query": f"\"{query}\"",
        "page": page
    }

    response = requests.get(
        base_url,
        auth=(API_KEY, "X"),
        params=params,
        headers={"Content-Type": "application/json"},
        timeout=60
    )

    if response.status_code == 401:
        raise RuntimeError("Erro 401: API key inválida ou sem permissão.")

    if response.status_code == 404:
        raise RuntimeError("Erro 404: domínio ou endpoint inválido.")

    if response.status_code == 429:
        raise RuntimeError("Erro 429: limite de requisições da API excedido.")

    if response.status_code != 200:
        raise RuntimeError(f"Erro {response.status_code}: {response.text}")

    payload = response.json()
    resultados = payload.get("results", [])

    if not resultados:
        print(f"Nenhum resultado na página {page}.")
        break

    todos_tickets.extend(resultados)
    print(f"Página {page}: {len(resultados)} tickets coletados | Acumulado: {len(todos_tickets)}")

    # quando a página vem vazia, encerra; como proteção adicional,
    # se vier muito pouco, seguimos até a próxima página vazia
    page += 1
    time.sleep(1)

with open(arquivo_saida, "w", encoding="utf-8") as f:
    json.dump(todos_tickets, f, ensure_ascii=False, indent=2)

print("=" * 60)
print("EXTRAÇÃO CONCLUÍDA")
print(f"Total de tickets extraídos: {len(todos_tickets)}")
print(f"JSON salvo em: {arquivo_saida}")
print("=" * 60)
