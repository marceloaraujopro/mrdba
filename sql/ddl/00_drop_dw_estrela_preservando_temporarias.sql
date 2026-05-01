BEGIN;

DROP TABLE IF EXISTS dw.fato_csi;
DROP TABLE IF EXISTS dw.fato_servidor;
DROP TABLE IF EXISTS dw.fato_ticket;

DROP TABLE IF EXISTS dw.dim_status_csi;
DROP TABLE IF EXISTS dw.dim_status_ticket;
DROP TABLE IF EXISTS dw.dim_tipo_ticket;
DROP TABLE IF EXISTS dw.dim_servidor;
DROP TABLE IF EXISTS dw.dim_cliente;
DROP TABLE IF EXISTS dw.dim_tempo;

COMMIT;
