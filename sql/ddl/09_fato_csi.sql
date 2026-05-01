CREATE TABLE IF NOT EXISTS dw.fato_csi (
    sk_fato_csi             BIGSERIAL PRIMARY KEY,
    id_ticket_origem        BIGINT NOT NULL UNIQUE,

    sk_cliente              BIGINT,
    sk_servidor             BIGINT,
    sk_status_csi           BIGINT,
    sk_tempo_criacao        INTEGER NOT NULL,
    sk_tempo_fechamento     INTEGER,

    titulo_csi              TEXT,
    foi_atuado              SMALLINT,
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
