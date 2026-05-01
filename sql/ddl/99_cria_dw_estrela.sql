BEGIN;

\i /dados/projetos/mrdba/sql/ddl/00_schema_dw.sql
\i /dados/projetos/mrdba/sql/ddl/01_dim_tempo.sql
\i /dados/projetos/mrdba/sql/ddl/02_dim_cliente.sql
\i /dados/projetos/mrdba/sql/ddl/03_dim_servidor.sql
\i /dados/projetos/mrdba/sql/ddl/04_dim_tipo_ticket.sql
\i /dados/projetos/mrdba/sql/ddl/05_dim_status_ticket.sql
\i /dados/projetos/mrdba/sql/ddl/06_dim_status_csi.sql
\i /dados/projetos/mrdba/sql/ddl/07_fato_ticket.sql
\i /dados/projetos/mrdba/sql/ddl/08_fato_servidor.sql
\i /dados/projetos/mrdba/sql/ddl/09_fato_csi.sql
\i /dados/projetos/mrdba/sql/ddl/90_indices.sql
\i /dados/projetos/mrdba/sql/ddl/95_carga_inicial_dimensoes.sql

COMMIT;
