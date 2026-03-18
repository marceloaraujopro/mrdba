import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FRESHDESK_API_KEY")
DOMAIN = os.getenv("FRESHDESK_DOMAIN")

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

base_url = f"https://{DOMAIN}/api/v2/search/tickets"
raw_dir = Path("/dados/projetos/mrdba/data_lake/raw/tickets")
raw_dir.mkdir(parents=True, exist_ok=True)
arquivo_saida = raw_dir / f"mrdba_tickets_{ano}_{mes:02d}.json"

# primeiro dia do mês
inicio_mes = date(ano, mes, 1)

# primeiro dia do mês seguinte
if mes == 12:
    fim_mes_exclusivo = date(ano + 1, 1, 1)
else:
    fim_mes_exclusivo = date(ano, mes + 1, 1)

def gerar_janelas_semanais(data_inicio: date, data_fim_exclusivo: date):
    atual = data_inicio
    while atual < data_fim_exclusivo:
        proxima = min(atual + timedelta(days=7), data_fim_exclusivo)
        yield atual, proxima
        atual = proxima

todos_tickets = []
ids_vistos = set()

print("=" * 60)
print("EXTRAÇÃO DE TICKETS - FRESHDESK")
print("=" * 60)
print(f"Domínio: {DOMAIN}")
print(f"Mês solicitado: {ano}-{mes:02d}")
print(f"Arquivo de saída: {arquivo_saida}")
print("=" * 60)

for inicio_janela, fim_janela in gerar_janelas_semanais(inicio_mes, fim_mes_exclusivo):
    dia_anterior = inicio_janela - timedelta(days=1)

    query = (
        f"created_at:>'{dia_anterior.isoformat()}' "
        f"AND created_at:<'{fim_janela.isoformat()}'"
    )

    print(f"\nJanela: {inicio_janela} até {fim_janela} (fim exclusivo)")
    print(f"Query: {query}")

    for page in range(1, 11):
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
            print(f"Página {page}: sem resultados")
            break

        novos = 0
        for ticket in resultados:
            ticket_id = ticket.get("id")
            if ticket_id not in ids_vistos:
                ids_vistos.add(ticket_id)
                todos_tickets.append(ticket)
                novos += 1

        print(
            f"Página {page}: {len(resultados)} retornados | "
            f"{novos} novos | acumulado: {len(todos_tickets)}"
        )

        time.sleep(1)

with open(arquivo_saida, "w", encoding="utf-8") as f:
    json.dump(todos_tickets, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 60)
print("EXTRAÇÃO CONCLUÍDA")
print(f"Total de tickets extraídos: {len(todos_tickets)}")
print(f"JSON salvo em: {arquivo_saida}")
print("=" * 60)
