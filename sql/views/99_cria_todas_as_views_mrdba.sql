CREATE OR REPLACE VIEW dw.vw_executiva_mrdba AS
SELECT
    dt.anomes,
    c.nm_cliente,

    COUNT(DISTINCT ft.id_ticket_origem) AS total_tickets,
    SUM(CASE WHEN tt.nm_tipo_ticket = 'Checklist' THEN 1 ELSE 0 END) AS qtd_checklists,
    SUM(CASE WHEN tt.nm_tipo_ticket = 'CSI' THEN 1 ELSE 0 END) AS qtd_csi,
    SUM(CASE WHEN tt.nm_tipo_ticket = 'CRISE' THEN 1 ELSE 0 END) AS qtd_crises,
    SUM(ft.foi_atuado) AS tickets_atuados,

    ROUND(AVG(ft.tempo_resolucao_horas), 2) AS tempo_medio_resolucao_horas,

    COUNT(DISTINCT fs.sk_servidor) AS qtd_servidores_monitorados,
    ROUND(AVG(fs.disponibilidade_pct), 2) AS disponibilidade_media_pct,
    SUM(fs.minutos_indisponiveis) AS total_minutos_indisponiveis,
    ROUND(SUM(fs.tamanho_gb), 2) AS volumetria_total_gb,
    ROUND(SUM(fs.delta_1_mes), 2) AS crescimento_total_mes_gb

FROM dw.dim_tempo dt

LEFT JOIN dw.fato_ticket ft
    ON ft.sk_tempo_criacao = dt.sk_tempo

LEFT JOIN dw.dim_cliente c
    ON ft.sk_cliente = c.sk_cliente

LEFT JOIN dw.dim_tipo_ticket tt
    ON ft.sk_tipo_ticket = tt.sk_tipo_ticket

LEFT JOIN dw.fato_servidor fs
    ON fs.sk_tempo_referencia = dt.sk_tempo

WHERE ft.id_ticket_origem IS NOT NULL
   OR fs.sk_fato_servidor IS NOT NULL

GROUP BY
    dt.anomes,
    c.nm_cliente

ORDER BY
    dt.anomes,
    c.nm_cliente;



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



CREATE OR REPLACE VIEW dw.vw_executiva_disponibilidade_capacity AS
SELECT
    dt.anomes,
    s.nk_servidor,
    s.instancia,
    s.host_name,
    s.nome_servidor,
    s.sgdb,
    s.ambiente,
    s.ambiente_macro,

    fs.tamanho_gb,
    fs.delta_1_mes,
    fs.delta_3_meses,
    fs.delta_6_meses,
    fs.delta_12_meses,
    fs.disponibilidade_pct,
    fs.minutos_indisponiveis,

    CASE
        WHEN fs.disponibilidade_pct < 98 THEN 'Crítico'
        WHEN fs.disponibilidade_pct < 99 THEN 'Atenção'
        ELSE 'Normal'
    END AS status_disponibilidade,

    CASE
        WHEN fs.delta_1_mes > 100 THEN 'Crescimento elevado'
        WHEN fs.delta_1_mes > 50 THEN 'Crescimento moderado'
        ELSE 'Crescimento normal'
    END AS status_capacity

FROM dw.fato_servidor fs

JOIN dw.dim_tempo dt
    ON fs.sk_tempo_referencia = dt.sk_tempo

JOIN dw.dim_servidor s
    ON fs.sk_servidor = s.sk_servidor

ORDER BY
    dt.anomes,
    s.nk_servidor;




CREATE OR REPLACE VIEW dw.vw_csi_melhorias AS
SELECT
    dt.anomes,
    fc.id_ticket_origem,
    c.nm_cliente,
    s.nk_servidor,
    s.instancia,
    s.nome_servidor,
    sc.nm_status_csi,
    fc.titulo_csi,
    fc.foi_atuado,
    fc.tempo_resolucao_horas,
    fc.data_carga

FROM dw.fato_csi fc

LEFT JOIN dw.dim_tempo dt
    ON fc.sk_tempo_criacao = dt.sk_tempo

LEFT JOIN dw.dim_cliente c
    ON fc.sk_cliente = c.sk_cliente

LEFT JOIN dw.dim_servidor s
    ON fc.sk_servidor = s.sk_servidor

LEFT JOIN dw.dim_status_csi sc
    ON fc.sk_status_csi = sc.sk_status_csi;



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
