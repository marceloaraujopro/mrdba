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
