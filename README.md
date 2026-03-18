# Projeto MRDBA

## 1. Descrição do Projeto
O projeto **mrDBA** tem como objetivo criar um ambiente de laboratório para práticas de **administração de banco de dados
e engenharia de dados**, utilizando containers para provisionamento da infraestrutura.

O ambiente utiliza **Docker** para execução dos serviços e **PostgreSQL** como sistema gerenciador de banco de dados.

Além disso, o projeto implementa uma arquitetura simplificada de **Data Lake + Data Warehouse**,
permitindo simular um pipeline completo de ingestão, tratamento e consumo de dados.

---

## 2. Tecnologias Utilizadas

- Docker
- PostgreSQL
- pgAdmin 4
- SQL
- Power BI
- JSON

---

## 3. Arquitetura do Ambiente


O projeto segue uma arquitetura simplificada de engenharia de dados:

Data Source 
↓
Data Lake (Filesystem)
↓
Transformação de Dados
↓
Data Warehouse (PostgreSQL)
↓
Dashboard Analítico

---

## 4. Estrutura do Repositório

mrdba
│
├── docker
│ └── docker-compose.yml
│
├── data_lake
│ ├── raw
│ ├── staging
│ └── curated
│
├── dashboard
│ └── powerbi
│
├── scripts
│ ├── ingestao
│ ├── transformacao
│ └── monitoramento
│
├── sql
│ ├── ddl
│ ├── dml
│ └── views
│
├── docs
│ ├── evidencias
│ ├── relatorios
│ └── diagramas
│
└── README.md

---

## 5. Camadas de Dados

O projeto implementa uma estrutura de **Data Lake no filesystem**, organizada nas seguintes camadas:

### RAW
Armazena dados brutos ingeridos de fontes externas, sem qualquer transformação.

Exemplo: data/raw/tickets_mrdba.json

### STAGING
Armazena dados temporariamente tratados

###CURATED
Armazena  dados limpos, estruturados e prontos para consumo analítico

---

## 6. Data Warehouse
O Data Warehouse do projeto é implementado utilizando **PostgreSQL**.

Banco principal:
db_mrdba

## 7. Adminstração do Banco
A administração do banco é realizada através do **pgAdmin 4**, executado em container.

## 8. Execução do Ambiente

### 1. Subir os containers
docker compose up -d

### 2. Verificar containers ativos
docker ps

### 3. Acessar o pgAdmin
http://localhost:5050

---

## 9. Dashboard Analítico
O projeto também prevê a construção de dashboards utilizando **Power BI**,
armazenados no diretório:

dashboard/powerbi

Esses dashboards poderão consumir dados diretamente do **PostgreSQL**.

---

## 10. Evidências do Projeto
As evidências das sprints estão armazenadas em:

docs/evidencias

Incluindo:

- execução dos containers
- criação do banco de dados
- configuração da rede Docker
- conexão com o banco via pgAdmin

---

## 11. Próximos Passos

- criação do modelo relacional do Data Warehouse
- desenvolvimento de pipelines de ingestão de dados
- automação de processos de transformação
- criação de dashboards analíticos
- monitoramento de cargas de dados

---

## 12. Autores

Marcelo Araújo
Breno Silveira

Projeto acadêmico desenvolvido no curso de graduação em Banco de Dados.
