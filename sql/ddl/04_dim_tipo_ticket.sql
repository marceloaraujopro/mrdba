CREATE TABLE IF NOT EXISTS dw.dim_tipo_ticket (
	sk_tipo_ticket BIGSERIAL PRIMARY KEY,
	nm_tipo_ticket VARCHAR(50) NOT NULL UNIQUE
);

COMMENT ON TABLE dw.dim_tipo_ticket IS
'Dimensão que classifica o tipo de ticket (Incidente, Checklist, CSI, etc)';

COMMENT ON COLUMN dw.dim_tipo_ticket.nm_tipo_ticket IS
'Nome do tipo de ticket conforme classificacão do sistema de origem.';
