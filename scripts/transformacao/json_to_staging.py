import sys
import pandas as pd
import json

ano = sys.argv[1]
mes = sys.argv[2]

arquivo_json = f"/dados/projetos/mrdba/data_lake/raw/tickets/mrdba_tickets_{ano}_{mes}.json"
arquivo_saida = f"/dados/projetos/mrdba/data_lake/staging/mrdba_tickets_staging_{ano}_{mes}.csv"

with open(arquivo_json) as f:
    dados = json.load(f)

# Normalização
df = pd.json_normalize(dados)

# Seleciona as colunas principais

df = df[
[
'id',
'subject',
'status',
'priority',
'type',
'created_at',
'updated_at',
'custom_fields.cf_sgdb',
'custom_fields.cf_ambiente',
'custom_fields.cf_csi_status'
]
]

df.to_csv(arquivo_saida, index=False)

print("STAGING criado")
