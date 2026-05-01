CREATE TABLE IF NOT EXISTS dw.dim_cliente (
	sk_cliente  BIGSERIAL PRIMARY KEY,
	nm_cliente  VARCHAR(100) NOT NULL UNIQUE,
	ativo       BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE dw.dim_cliente IS
'Dimensão de clientes (empresas) atendidos pelos servicos monitorados';

COMMENT ON COLUMN dw.dim_cliente.sk_cliente IS
'Chave substituta do cliente';

COMMENT ON COLUMN dw.dim_cliente.nm_cliente IS
'Nome da empresa cliente (ex: SENAC, MILLS, AND, SES...)';

COMMENT ON COLUMN dw.dim_cliente.ativo IS
'Indica se o cliente permanece ativo no contexto analítico.';
