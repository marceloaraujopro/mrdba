CREATE OR REPLACE VIEW dw.vw_tecnica_mrdba AS
SELECT
    dt.anomes,
    dt.data_completa,

    ft.id_ticket_origem,
    c.nm_cliente,
    tt.nm_tipo_ticket,
    st.nm_status_ticket,

    s.nk_servidor,
    s.nome_servidor,
    s.instancia,
    s.host_name,
    s.sgdb,
    s.ambiente,
    s.ambiente_macro,

    ft.foi_atuado,
    ft.tempo_resolucao_horas,
    ft.titulo_ticket,
    ft.data_carga

FROM dw.fato_ticket ft

LEFT JOIN dw.dim_tempo dt
    ON ft.sk_tempo_criacao = dt.sk_tempo

LEFT JOIN dw.dim_cliente c
    ON ft.sk_cliente = c.sk_cliente

LEFT JOIN dw.dim_tipo_ticket tt
    ON ft.sk_tipo_ticket = tt.sk_tipo_ticket

LEFT JOIN dw.dim_status_ticket st
    ON ft.sk_status_ticket = st.sk_status_ticket

LEFT JOIN dw.dim_servidor s
    ON ft.sk_servidor = s.sk_servidor;
