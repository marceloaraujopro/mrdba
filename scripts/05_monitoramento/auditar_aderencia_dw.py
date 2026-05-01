import os
import sys
import pandas as pd

BASE_DIR = "/dados/projetos/mrdba"

def caminho_arquivo(camada, ano, mes):
    if camada == "staging":
        return f"{BASE_DIR}/data_lake/staging/tickets/mrdba_tickets_staging_{ano}_{mes}.csv"
    elif camada == "curated":
        return f"{BASE_DIR}/data_lake/curated/tickets/mrdba_tickets_curated_{ano}_{mes}.csv"
    else:
        raise ValueError("Camada inválida")

def analisar_dataframe(df, nome):
    print("\n" + "="*70)
    print(f"ANÁLISE: {nome}")
    print("="*70)

    print(f"Total de linhas: {len(df)}")
    print(f"Total de colunas: {len(df.columns)}")

    print("\nColunas:")
    for col in df.columns:
        print(f"- {col}")

    if "ticket_id" in df.columns:
        duplicados = df["ticket_id"].duplicated().sum()
        print(f"\nDuplicados em ticket_id: {duplicados}")
    else:
        print("\nColuna ticket_id não encontrada")

    print("\nPercentual de nulos por coluna:")
    nulos = (df.isnull().mean() * 100).round(2).sort_values(ascending=False)
    print(nulos)

def validar_dominios(df):
    print("\n" + "="*70)
    print("VALIDAÇÃO DE DOMÍNIOS")
    print("="*70)

    dominios_esperados = {
        "prioridade": ["Baixa", "Média", "Alta", "Urgente"],
        "status": ["Aberto", "Em Execução", "Aguardando o cliente", "Resolvido", "Fechado", "Encerrado"],
        "tipo_ticket": ["Checklist", "Incidente", "CSI", "Crise", "Outro"]
    }

    for coluna, dominio in dominios_esperados.items():
        if coluna in df.columns:
            encontrados = sorted(df[coluna].dropna().astype(str).unique().tolist())
            invalidos = [v for v in encontrados if v not in dominio]

            print(f"\nColuna: {coluna}")
            print(f"Valores encontrados: {encontrados}")
            print(f"Valores fora do domínio esperado: {invalidos if invalidos else 'Nenhum'}")
        else:
            print(f"\nColuna {coluna} não encontrada no curated")

def comparar_staging_curated(df_stg, df_cur):
    print("\n" + "="*70)
    print("COMPARAÇÃO STAGING x CURATED")
    print("="*70)

    print(f"Linhas no staging: {len(df_stg)}")
    print(f"Linhas no curated: {len(df_cur)}")

    if "ticket_id" in df_stg.columns and "ticket_id" in df_cur.columns:
        stg_ids = set(df_stg["ticket_id"].dropna().astype(str))
        cur_ids = set(df_cur["ticket_id"].dropna().astype(str))

        so_staging = stg_ids - cur_ids
        so_curated = cur_ids - stg_ids

        print(f"IDs apenas no staging: {len(so_staging)}")
        print(f"IDs apenas no curated: {len(so_curated)}")

        if so_staging:
            print("Exemplos apenas no staging:", list(sorted(so_staging))[:10])
        if so_curated:
            print("Exemplos apenas no curated:", list(sorted(so_curated))[:10])

def validar_campos_dw(df):
    print("\n" + "="*70)
    print("ADERÊNCIA ÀS COLUNAS DO DW")
    print("="*70)

    colunas_dw_esperadas = [
        "ticket_id",
        "data_abertura",
        "data_encerramento",
        "servidor",
        "tipo_ticket",
        "status",
        "prioridade",
        "tempo_resolucao_horas",
        "sgdb",
        "ambiente_macro",
        "ambiente_detalhe",
        "classificacao_ticket",
        "titulo_csi",
        "link_csi",
        "status_csi",
        "auto_resolvido"
    ]

    for col in colunas_dw_esperadas:
        if col in df.columns:
            perc_nulos = round(df[col].isnull().mean() * 100, 2)
            print(f"[OK] {col} | nulos: {perc_nulos}%")
        else:
            print(f"[FALTANDO] {col}")

def main():
    if len(sys.argv) != 3:
        print("Uso: python3 auditar_aderencia_dw.py ANO MES")
        sys.exit(1)

    ano = sys.argv[1]
    mes = sys.argv[2]

    path_stg = caminho_arquivo("staging", ano, mes)
    path_cur = caminho_arquivo("curated", ano, mes)

    if not os.path.exists(path_stg):
        print(f"Arquivo não encontrado: {path_stg}")
        sys.exit(1)

    if not os.path.exists(path_cur):
        print(f"Arquivo não encontrado: {path_cur}")
        sys.exit(1)

    df_stg = pd.read_csv(path_stg)
    df_cur = pd.read_csv(path_cur)

    analisar_dataframe(df_stg, "STAGING")
    analisar_dataframe(df_cur, "CURATED")
    comparar_staging_curated(df_stg, df_cur)
    validar_dominios(df_cur)
    validar_campos_dw(df_cur)

if __name__ == "__main__":
    main()
