CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE IF NOT EXISTS dw.fato_servidores_mensal (
    instancia               VARCHAR(100)   NOT NULL,
    host_name               VARCHAR(200),
    anomes                  VARCHAR(7)     NOT NULL,
    data_referencia         DATE           NOT NULL,
    tamanho_gb              NUMERIC(14,2),
    delta_1_mes             NUMERIC(14,2),
    delta_2_meses           NUMERIC(14,2),
    delta_3_meses           NUMERIC(14,2),
    delta_6_meses           NUMERIC(14,2),
    delta_12_meses          NUMERIC(14,2),
    disponibilidade_pct     NUMERIC(7,2),
    minutos_indisponiveis   INTEGER
);
