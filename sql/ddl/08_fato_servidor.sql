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
