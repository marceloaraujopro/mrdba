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
