CREATE TABLE IF NOT EXISTS dw.dim_tempo (
    sk_tempo            INTEGER PRIMARY KEY,
    data_completa       DATE NOT NULL UNIQUE,
    ano                 SMALLINT NOT NULL,
    mes                 SMALLINT NOT NULL,
    dia                 SMALLINT NOT NULL,
    anomes              INTEGER NOT NULL,
    nome_mes            VARCHAR(20) NOT NULL,
    trimestre           SMALLINT NOT NULL,
    semestre            SMALLINT NOT NULL
);

COMMENT ON TABLE dw.dim_tempo IS
'Dimensão de tempo com granularidade diária utilizada para análise temporal das fatos.';

COMMENT ON COLUMN dw.dim_tempo.sk_tempo IS
'Chave substituta no formato YYYYMMDD.';

COMMENT ON COLUMN dw.dim_tempo.data_completa IS
'Data calendário correspondente à chave substituta.';

COMMENT ON COLUMN dw.dim_tempo.anomes IS
'Representação do ano e mês no formato YYYYMM.';

COMMENT ON COLUMN dw.dim_tempo.nome_mes IS
'Nome do mês em português.';

COMMENT ON COLUMN dw.dim_tempo.trimestre IS
'Trimestre da data.';

COMMENT ON COLUMN dw.dim_tempo.semestre IS
'Semestre da data.';
