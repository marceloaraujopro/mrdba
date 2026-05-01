CREATE OR REPLACE VIEW dw.vw_freshdesk_indicadores AS
SELECT
    dt.anomes,
    c.nm_cliente,
    tt.nm_tipo_ticket,
    st.nm_status_ticket,

    COUNT(*) AS total_tickets,
    SUM(ft.foi_atuado) AS tickets_atuados,
    COUNT(*) - SUM(ft.foi_atuado) AS tickets_nao_atuados,
    ROUND(AVG(ft.tempo_resolucao_horas), 2) AS tempo_medio_resolucao_horas

FROM dw.fato_ticket ft

JOIN dw.dim_tempo dt
    ON ft.sk_tempo_criacao = dt.sk_tempo

JOIN dw.dim_cliente c
    ON ft.sk_cliente = c.sk_cliente

JOIN dw.dim_tipo_ticket tt
    ON ft.sk_tipo_ticket = tt.sk_tipo_ticket

LEFT JOIN dw.dim_status_ticket st
    ON ft.sk_status_ticket = st.sk_status_ticket

GROUP BY
    dt.anomes,
    c.nm_cliente,
    tt.nm_tipo_ticket,
    st.nm_status_ticket

ORDER BY
    dt.anomes,
    c.nm_cliente,
    tt.nm_tipo_ticket;
