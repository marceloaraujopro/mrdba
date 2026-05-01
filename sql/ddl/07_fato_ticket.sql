CREATE TABLE IF NOT EXISTS dw.fato_ticket (
    sk_ticket               BIGSERIAL PRIMARY KEY,
    id_ticket_origem        BIGINT NOT NULL UNIQUE,

    sk_cliente              BIGINT NOT NULL,
    sk_servidor             BIGINT,
    sk_tipo_ticket          BIGINT NOT NULL,
    sk_status_ticket        BIGINT,
    sk_tempo_criacao        INTEGER NOT NULL,
    sk_tempo_ultima_alt     INTEGER,

    foi_atuado              SMALLINT,
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
'Indica se houve atuação da equipe no ticket (1 - SIM, 2 - NÃO).';

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
