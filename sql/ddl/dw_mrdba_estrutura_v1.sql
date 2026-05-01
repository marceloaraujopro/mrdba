BEGIN;

-- =========================================================
-- DW MRDBA - ESTRUTURA FINAL CONSOLIDADA
-- Modelo estrela
-- =========================================================

-- =========================================================
-- 1) SCHEMA
-- =========================================================
CREATE SCHEMA IF NOT EXISTS dw;

COMMENT ON SCHEMA dw IS
'Schema destinado ao Data Warehouse do projeto mrdba, estruturado em modelo estrela.';

-- =========================================================
-- 2) DIMENSOES
-- =========================================================

-- ---------------------------------------------------------
-- DIM TEMPO
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_tempo (
    sk_tempo            INTEGER PRIMARY KEY,
    data_completa       DATE NOT NULL UNIQUE,
    ano                 SMALLINT NOT NULL,
    mes                 SMALLINT NOT NULL,
    dia                 SMALLINT NOT NULL,
    anomes              CHAR(7) NOT NULL,
    nome_mes            VARCHAR(20) NOT NULL,
    trimestre           SMALLINT NOT NULL,
    semestre            SMALLINT NOT NULL
);

COMMENT ON TABLE dw.dim_tempo IS
'Dimensão de tempo com granularidade diária utilizada para análise temporal das fatos.';

COMMENT ON COLUMN dw.dim_tempo.sk_tempo IS
'Chave substituta no formato YYYYMMDD.';

COMMENT ON COLUMN dw.dim_tempo.data_completa IS
'Data calendário correspondente à chave substituta.';

COMMENT ON COLUMN dw.dim_tempo.anomes IS
'Representação do ano e mês no formato YYYY-MM.';

COMMENT ON COLUMN dw.dim_tempo.nome_mes IS
'Nome do mês em português.';

COMMENT ON COLUMN dw.dim_tempo.trimestre IS
'Trimestre da data.';

COMMENT ON COLUMN dw.dim_tempo.semestre IS
'Semestre da data.';

-- ---------------------------------------------------------
-- DIM CLIENTE
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_cliente (
    sk_cliente          BIGSERIAL PRIMARY KEY,
    nm_cliente          VARCHAR(100) NOT NULL UNIQUE,
    ativo               BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE dw.dim_cliente IS
'Dimensão de clientes (empresas) atendidos pelos serviços monitorados no projeto.';

COMMENT ON COLUMN dw.dim_cliente.sk_cliente IS
'Chave substituta do cliente.';

COMMENT ON COLUMN dw.dim_cliente.nm_cliente IS
'Nome da empresa cliente, como SENAC, MILLS, AND e SES.';

COMMENT ON COLUMN dw.dim_cliente.ativo IS
'Indica se o cliente permanece ativo no contexto analítico.';

-- ---------------------------------------------------------
-- DIM SERVIDOR
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_servidor (
    sk_servidor         BIGSERIAL PRIMARY KEY,
    nk_servidor         VARCHAR(200) NOT NULL UNIQUE,
    instancia           VARCHAR(100),
    host_name           VARCHAR(200),
    nome_servidor       VARCHAR(200),
    ambiente            VARCHAR(50),
    ambiente_macro      VARCHAR(30),
    sgdb                VARCHAR(100),
    sk_cliente          BIGINT REFERENCES dw.dim_cliente(sk_cliente),
    ativo               BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE dw.dim_servidor IS
'Dimensão de servidores e instâncias monitoradas, consolidando dados técnicos e nomes oriundos dos tickets.';

COMMENT ON COLUMN dw.dim_servidor.nk_servidor IS
'Chave natural padronizada do servidor, derivada de host_name, instancia ou nome_servidor tratado.';

COMMENT ON COLUMN dw.dim_servidor.instancia IS
'Nome da instância lógica do banco de dados conforme fonte técnica estruturada.';

COMMENT ON COLUMN dw.dim_servidor.host_name IS
'Nome do host físico ou virtual.';

COMMENT ON COLUMN dw.dim_servidor.nome_servidor IS
'Nome do servidor conforme identificado nos tickets, sujeito a variações de preenchimento.';

COMMENT ON COLUMN dw.dim_servidor.ambiente IS
'Detalhamento do ambiente, como Produção, Homologação, QA, DEV ou Teste.';

COMMENT ON COLUMN dw.dim_servidor.ambiente_macro IS
'Classificação analítica resumida do ambiente: Produção ou Não Produção.';

COMMENT ON COLUMN dw.dim_servidor.sgdb IS
'Sistema gerenciador de banco de dados associado ao servidor.';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_dim_servidor_ambiente_macro'
    ) THEN
        ALTER TABLE dw.dim_servidor
        ADD CONSTRAINT ck_dim_servidor_ambiente_macro
        CHECK (
            ambiente_macro IS NULL
            OR ambiente_macro IN ('Produção', 'Não Produção')
        );
    END IF;
END $$;

-- ---------------------------------------------------------
-- DIM TIPO TICKET
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_tipo_ticket (
    sk_tipo_ticket      BIGSERIAL PRIMARY KEY,
    nm_tipo_ticket      VARCHAR(50) NOT NULL UNIQUE
);

COMMENT ON TABLE dw.dim_tipo_ticket IS
'Dimensão que classifica o tipo de ticket, como Checklist, Incidente, CSI e Crise.';

COMMENT ON COLUMN dw.dim_tipo_ticket.nm_tipo_ticket IS
'Nome do tipo de ticket conforme regra de classificação do projeto.';

-- ---------------------------------------------------------
-- DIM STATUS TICKET
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_status_ticket (
    sk_status_ticket    BIGSERIAL PRIMARY KEY,
    nm_status_ticket    VARCHAR(100) NOT NULL UNIQUE
);

COMMENT ON TABLE dw.dim_status_ticket IS
'Dimensão de status operacional dos tickets.';

COMMENT ON COLUMN dw.dim_status_ticket.nm_status_ticket IS
'Status do ticket, como Aberto, Em Execução, Resolvido ou Fechado.';

-- ---------------------------------------------------------
-- DIM STATUS CSI
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.dim_status_csi (
    sk_status_csi       BIGSERIAL PRIMARY KEY,
    nm_status_csi       VARCHAR(100) NOT NULL UNIQUE
);

COMMENT ON TABLE dw.dim_status_csi IS
'Dimensão específica para status do processo CSI.';

COMMENT ON COLUMN dw.dim_status_csi.nm_status_csi IS
'Status do CSI, como Em execução, Implementado ou Encerrado.';

-- =========================================================
-- 3) FATOS
-- =========================================================

-- ---------------------------------------------------------
-- FATO TICKET
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.fato_ticket (
    sk_ticket               BIGSERIAL PRIMARY KEY,
    id_ticket_origem        BIGINT NOT NULL UNIQUE,

    sk_cliente              BIGINT NOT NULL,
    sk_servidor             BIGINT,
    sk_tipo_ticket          BIGINT NOT NULL,
    sk_status_ticket        BIGINT,
    sk_tempo_criacao        INTEGER NOT NULL,
    sk_tempo_ultima_alt     INTEGER,

    foi_atuado              BOOLEAN,
    tempo_resolucao_horas   NUMERIC(12,2),
    titulo_ticket           TEXT,
    data_carga              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fato_ticket_cliente
        FOREIGN KEY (sk_cliente) REFERENCES dw.dim_cliente(sk_cliente),

    CONSTRAINT fk_fato_ticket_servidor
        FOREIGN KEY (sk_servidor) REFERENCES dw.dim_servidor(sk_servidor),

    CONSTRAINT fk_fato_ticket_tipo
        FOREIGN KEY (sk_tipo_ticket) REFERENCES dw.dim_tipo_ticket(sk_tipo_ticket),

    CONSTRAINT fk_fato_ticket_status
        FOREIGN KEY (sk_status_ticket) REFERENCES dw.dim_status_ticket(sk_status_ticket),

    CONSTRAINT fk_fato_ticket_tempo_criacao
        FOREIGN KEY (sk_tempo_criacao) REFERENCES dw.dim_tempo(sk_tempo),

    CONSTRAINT fk_fato_ticket_tempo_ultima_alt
        FOREIGN KEY (sk_tempo_ultima_alt) REFERENCES dw.dim_tempo(sk_tempo)
);

COMMENT ON TABLE dw.fato_ticket IS
'Tabela fato com granularidade de 1 linha por ticket do Freshdesk.';

COMMENT ON COLUMN dw.fato_ticket.id_ticket_origem IS
'Identificador único do ticket no sistema de origem.';

COMMENT ON COLUMN dw.fato_ticket.foi_atuado IS
'Indica se houve atuação da equipe no ticket.';

COMMENT ON COLUMN dw.fato_ticket.tempo_resolucao_horas IS
'Tempo entre criação e última atualização do ticket, em horas.';

COMMENT ON COLUMN dw.fato_ticket.titulo_ticket IS
'Título original do ticket, mantido como atributo textual.';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_fato_ticket_tempo_resolucao'
    ) THEN
        ALTER TABLE dw.fato_ticket
        ADD CONSTRAINT ck_fato_ticket_tempo_resolucao
        CHECK (
            tempo_resolucao_horas IS NULL
            OR tempo_resolucao_horas >= 0
        );
    END IF;
END $$;

-- ---------------------------------------------------------
-- FATO SERVIDOR
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.fato_servidor (
    sk_fato_servidor        BIGSERIAL PRIMARY KEY,

    sk_servidor             BIGINT NOT NULL,
    sk_tempo_referencia     INTEGER NOT NULL,

    tamanho_gb              NUMERIC(14,2),
    delta_1_mes             NUMERIC(14,2),
    delta_2_meses           NUMERIC(14,2),
    delta_3_meses           NUMERIC(14,2),
    delta_6_meses           NUMERIC(14,2),
    delta_12_meses          NUMERIC(14,2),
    disponibilidade_pct     NUMERIC(7,2),
    minutos_indisponiveis   INTEGER,

    arquivo_origem          TEXT,
    data_carga              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_fato_servidor UNIQUE (sk_servidor, sk_tempo_referencia),

    CONSTRAINT fk_fato_servidor_servidor
        FOREIGN KEY (sk_servidor) REFERENCES dw.dim_servidor(sk_servidor),

    CONSTRAINT fk_fato_servidor_tempo
        FOREIGN KEY (sk_tempo_referencia) REFERENCES dw.dim_tempo(sk_tempo)
);

COMMENT ON TABLE dw.fato_servidor IS
'Tabela fato mensal com métricas de capacidade e disponibilidade dos servidores. Granularidade: 1 linha por servidor por mês.';

COMMENT ON COLUMN dw.fato_servidor.tamanho_gb IS
'Volume total armazenado em gigabytes no mês de referência.';

COMMENT ON COLUMN dw.fato_servidor.delta_1_mes IS
'Variação volumétrica em relação ao mês anterior.';

COMMENT ON COLUMN dw.fato_servidor.delta_2_meses IS
'Variação volumétrica em relação a dois meses anteriores.';

COMMENT ON COLUMN dw.fato_servidor.delta_3_meses IS
'Variação volumétrica em relação a três meses anteriores.';

COMMENT ON COLUMN dw.fato_servidor.delta_6_meses IS
'Variação volumétrica em relação a seis meses anteriores.';

COMMENT ON COLUMN dw.fato_servidor.delta_12_meses IS
'Variação volumétrica em relação a doze meses anteriores.';

COMMENT ON COLUMN dw.fato_servidor.disponibilidade_pct IS
'Percentual de disponibilidade do servidor no período.';

COMMENT ON COLUMN dw.fato_servidor.minutos_indisponiveis IS
'Total de minutos de indisponibilidade no mês.';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_fato_servidor_disponibilidade'
    ) THEN
        ALTER TABLE dw.fato_servidor
        ADD CONSTRAINT ck_fato_servidor_disponibilidade
        CHECK (
            disponibilidade_pct IS NULL
            OR (disponibilidade_pct >= 0 AND disponibilidade_pct <= 100)
        );
    END IF;
END $$;

-- ---------------------------------------------------------
-- FATO CSI
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS dw.fato_csi (
    sk_fato_csi             BIGSERIAL PRIMARY KEY,
    id_ticket_origem        BIGINT NOT NULL UNIQUE,

    sk_cliente              BIGINT,
    sk_servidor             BIGINT,
    sk_status_csi           BIGINT,
    sk_tempo_criacao        INTEGER NOT NULL,
    sk_tempo_fechamento     INTEGER,

    titulo_csi              TEXT,
    foi_atuado              BOOLEAN,
    tempo_resolucao_horas   NUMERIC(12,2),
    data_carga              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fato_csi_cliente
        FOREIGN KEY (sk_cliente) REFERENCES dw.dim_cliente(sk_cliente),

    CONSTRAINT fk_fato_csi_servidor
        FOREIGN KEY (sk_servidor) REFERENCES dw.dim_servidor(sk_servidor),

    CONSTRAINT fk_fato_csi_status
        FOREIGN KEY (sk_status_csi) REFERENCES dw.dim_status_csi(sk_status_csi),

    CONSTRAINT fk_fato_csi_tempo_criacao
        FOREIGN KEY (sk_tempo_criacao) REFERENCES dw.dim_tempo(sk_tempo),

    CONSTRAINT fk_fato_csi_tempo_fechamento
        FOREIGN KEY (sk_tempo_fechamento) REFERENCES dw.dim_tempo(sk_tempo)
);

COMMENT ON TABLE dw.fato_csi IS
'Tabela fato específica para tickets do tipo CSI. Granularidade: 1 linha por ticket CSI.';

COMMENT ON COLUMN dw.fato_csi.titulo_csi IS
'Título original do ticket CSI, preservado para análise.';

COMMENT ON COLUMN dw.fato_csi.tempo_resolucao_horas IS
'Tempo entre criação e fechamento ou última atualização do ticket CSI, em horas.';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_fato_csi_tempo_resolucao'
    ) THEN
        ALTER TABLE dw.fato_csi
        ADD CONSTRAINT ck_fato_csi_tempo_resolucao
        CHECK (
            tempo_resolucao_horas IS NULL
            OR tempo_resolucao_horas >= 0
        );
    END IF;
END $$;

-- =========================================================
-- 4) INDICES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_fato_ticket_sk_cliente
    ON dw.fato_ticket (sk_cliente);

CREATE INDEX IF NOT EXISTS idx_fato_ticket_sk_servidor
    ON dw.fato_ticket (sk_servidor);

CREATE INDEX IF NOT EXISTS idx_fato_ticket_sk_tipo_ticket
    ON dw.fato_ticket (sk_tipo_ticket);

CREATE INDEX IF NOT EXISTS idx_fato_ticket_sk_status_ticket
    ON dw.fato_ticket (sk_status_ticket);

CREATE INDEX IF NOT EXISTS idx_fato_ticket_sk_tempo_criacao
    ON dw.fato_ticket (sk_tempo_criacao);

CREATE INDEX IF NOT EXISTS idx_fato_ticket_sk_tempo_ultima_alt
    ON dw.fato_ticket (sk_tempo_ultima_alt);

CREATE INDEX IF NOT EXISTS idx_fato_servidor_sk_servidor
    ON dw.fato_servidor (sk_servidor);

CREATE INDEX IF NOT EXISTS idx_fato_servidor_sk_tempo_referencia
    ON dw.fato_servidor (sk_tempo_referencia);

CREATE INDEX IF NOT EXISTS idx_fato_csi_sk_cliente
    ON dw.fato_csi (sk_cliente);

CREATE INDEX IF NOT EXISTS idx_fato_csi_sk_servidor
    ON dw.fato_csi (sk_servidor);

CREATE INDEX IF NOT EXISTS idx_fato_csi_sk_status_csi
    ON dw.fato_csi (sk_status_csi);

CREATE INDEX IF NOT EXISTS idx_fato_csi_sk_tempo_criacao
    ON dw.fato_csi (sk_tempo_criacao);

CREATE INDEX IF NOT EXISTS idx_fato_csi_sk_tempo_fechamento
    ON dw.fato_csi (sk_tempo_fechamento);

-- =========================================================
-- 5) CARGA INICIAL DE DIMENSOES DE DOMINIO
-- =========================================================

INSERT INTO dw.dim_cliente (nm_cliente)
VALUES
    ('SENAC'),
    ('MILLS'),
    ('AND'),
    ('SES')
ON CONFLICT (nm_cliente) DO NOTHING;

INSERT INTO dw.dim_tipo_ticket (nm_tipo_ticket)
VALUES
    ('Checklist'),
    ('Incidente'),
    ('CSI'),
    ('Crise'),
    ('Outro')
ON CONFLICT (nm_tipo_ticket) DO NOTHING;

INSERT INTO dw.dim_status_ticket (nm_status_ticket)
VALUES
    ('Aberto'),
    ('Em Execução'),
    ('Aguardando o cliente'),
    ('Resolvido'),
    ('Fechado'),
    ('Encerrado')
ON CONFLICT (nm_status_ticket) DO NOTHING;

INSERT INTO dw.dim_status_csi (nm_status_csi)
VALUES
    ('Aberto'),
    ('Em execução'),
    ('Implementado'),
    ('Aguardando resposta do cliente'),
    ('Encerrado - falta de contato'),
    ('Encerrado - recusado pelo cliente'),
    ('NA')
ON CONFLICT (nm_status_csi) DO NOTHING;

COMMIT;
