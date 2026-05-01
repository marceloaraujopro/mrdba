CREATE TABLE IF NOT EXISTS dw.dim_servidor (
    sk_servidor         BIGSERIAL PRIMARY KEY,
    nk_servidor         VARCHAR(200) NOT NULL UNIQUE,
    instancia           VARCHAR(100),
    host_name           VARCHAR(200),
    nome_servidor       VARCHAR(200),
    ambiente            VARCHAR(50),
    ambiente_macro      VARCHAR(30),
    sgdb                VARCHAR(100),
    sk_cliente          BIGINT REFERENCES dw.dim_cliente(sk_cliente),
    ativo               BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE dw.dim_servidor IS
'Dimensão de servidores e instâncias monitoradas, consolidando dados técnicos e nomes oriundos dos tickets.';

COMMENT ON COLUMN dw.dim_servidor.nk_servidor IS
'Chave natural padronizada do servidor, derivada de host_name, instancia ou nome_servidor tratado.';

COMMENT ON COLUMN dw.dim_servidor.instancia IS
'Nome da instância lógica do banco de dados conforme fonte técnica estruturada.';

COMMENT ON COLUMN dw.dim_servidor.host_name IS
'Nome do host físico ou virtual.';

COMMENT ON COLUMN dw.dim_servidor.nome_servidor IS
'Nome do servidor conforme identificado nos tickets, sujeito a variações de preenchimento.';

COMMENT ON COLUMN dw.dim_servidor.ambiente IS
'Detalhamento do ambiente, como Produção, Homologação, QA, DEV ou Teste.';

COMMENT ON COLUMN dw.dim_servidor.ambiente_macro IS
'Classificação analítica resumida do ambiente: Produção ou Não Produção.';

COMMENT ON COLUMN dw.dim_servidor.sgdb IS
'Sistema gerenciador de banco de dados associado ao servidor.';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_dim_servidor_ambiente_macro'
    ) THEN
        ALTER TABLE dw.dim_servidor
        ADD CONSTRAINT ck_dim_servidor_ambiente_macro
        CHECK (
            ambiente_macro IS NULL
            OR ambiente_macro IN ('Produção', 'Não Produção')
        );
    END IF;
END $$;
