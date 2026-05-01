CREATE TABLE IF NOT EXISTS dw.dim_status_ticket (
    sk_status_ticket BIGSERIAL PRIMARY KEY,
    nm_status_ticket VARCHAR(50) NOT NULL UNIQUE
);

COMMENT ON TABLE dw.dim_status_ticket IS 
'Dimensão de status operacional dos tickets.';

COMMENT ON COLUMN dw.dim_status_ticket.nm_status_ticket IS 
'Status do ticket (Aberto, Resolvido, Fechado, etc.).';
