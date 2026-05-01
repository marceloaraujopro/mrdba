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
