CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS dw.dim_cliente (
    sk_cliente      BIGSERIAL PRIMARY KEY,
    nm_cliente      VARCHAR(100) NOT NULL UNIQUE,
    ativo           BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS dw.dim_tipo_ticket (
    sk_tipo_ticket  BIGSERIAL PRIMARY KEY,
    nm_tipo_ticket  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dw.dim_status_ticket (
    sk_status_ticket BIGSERIAL PRIMARY KEY,
    nm_status_ticket VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dw.dim_status_csi (
    sk_status_csi   BIGSERIAL PRIMARY KEY,
    nm_status_csi   VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dw.dim_tempo (
    sk_tempo        INTEGER PRIMARY KEY,
    data_completa   DATE NOT NULL UNIQUE,
    ano             SMALLINT NOT NULL,
    mes             SMALLINT NOT NULL,
    dia             SMALLINT NOT NULL,
    anomes          CHAR(7) NOT NULL,
    nome_mes        VARCHAR(20) NOT NULL,
    trimestre       SMALLINT NOT NULL,
    semestre        SMALLINT NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.dim_servidor (
    sk_servidor     BIGSERIAL PRIMARY KEY,
    nk_servidor     VARCHAR(200) NOT NULL UNIQUE,
    instancia       VARCHAR(100),
    host_name       VARCHAR(200),
    nome_servidor   VARCHAR(200),
    tipo_servidor   VARCHAR(100),
    ambiente        VARCHAR(50),
    sgdb            VARCHAR(50),
    sk_cliente      BIGINT REFERENCES dw.dim_cliente(sk_cliente),
    ativo           BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS dw.fato_ticket (
    sk_ticket               BIGSERIAL PRIMARY KEY,
    id_ticket_origem        BIGINT NOT NULL UNIQUE,
    sk_cliente              BIGINT NOT NULL REFERENCES dw.dim_cliente(sk_cliente),
    sk_servidor             BIGINT REFERENCES dw.dim_servidor(sk_servidor),
    sk_tipo_ticket          BIGINT NOT NULL REFERENCES dw.dim_tipo_ticket(sk_tipo_ticket),
    sk_status_ticket        BIGINT REFERENCES dw.dim_status_ticket(sk_status_ticket),
    sk_prioridade           BIGINT REFERENCES dw.dim_prioridade(sk_prioridade),
    sk_tempo_criacao        INTEGER NOT NULL REFERENCES dw.dim_tempo(sk_tempo),
    sk_tempo_ultima_alt     INTEGER REFERENCES dw.dim_tempo(sk_tempo),
    foi_atuado              BOOLEAN,
    tempo_resolucao_horas   NUMERIC(12,2),
    titulo_ticket           TEXT
);

CREATE TABLE IF NOT EXISTS dw.fato_servidor (
    sk_fato_servidor        BIGSERIAL PRIMARY KEY,
    sk_servidor             BIGINT NOT NULL REFERENCES dw.dim_servidor(sk_servidor),
    sk_tempo_referencia     INTEGER NOT NULL REFERENCES dw.dim_tempo(sk_tempo),
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
    CONSTRAINT uq_fato_servidor UNIQUE (sk_servidor, sk_tempo_referencia)
);

CREATE TABLE IF NOT EXISTS dw.fato_csi (
    sk_fato_csi             BIGSERIAL PRIMARY KEY,
    id_ticket_origem        BIGINT NOT NULL UNIQUE,
    sk_cliente              BIGINT REFERENCES dw.dim_cliente(sk_cliente),
    sk_servidor             BIGINT REFERENCES dw.dim_servidor(sk_servidor),
    sk_status_csi           BIGINT REFERENCES dw.dim_status_csi(sk_status_csi),
    sk_tempo_criacao        INTEGER NOT NULL REFERENCES dw.dim_tempo(sk_tempo),
    sk_tempo_fechamento     INTEGER REFERENCES dw.dim_tempo(sk_tempo),
    titulo_csi              TEXT,
    foi_atuado              BOOLEAN,
    tempo_resolucao_horas   NUMERIC(12,2)
);
