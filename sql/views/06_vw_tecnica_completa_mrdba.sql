CREATE OR REPLACE VIEW dw.vw_tecnica_completa_mrdba AS
SELECT
    dt_ticket.anomes,
    dt_ticket.data_completa,

    ft.id_ticket_origem,
    c.nm_cliente,
    tt.nm_tipo_ticket,
    st.nm_status_ticket,

    s_ticket.nk_servidor,
    s_ticket.instancia,
    s_ticket.host_name,
    s_ticket.sgdb,
    s_ticket.ambiente,

    ft.foi_atuado,
    ft.tempo_resolucao_horas,
    ft.titulo_ticket,

    fs.tamanho_gb,
    fs.delta_1_mes,
    fs.delta_3_meses,
    fs.delta_6_meses,
    fs.delta_12_meses,
    fs.disponibilidade_pct,
    fs.minutos_indisponiveis

FROM dw.fato_ticket ft

LEFT JOIN dw.dim_tempo dt_ticket
    ON ft.sk_tempo_criacao = dt_ticket.sk_tempo

LEFT JOIN dw.dim_cliente c
    ON ft.sk_cliente = c.sk_cliente

LEFT JOIN dw.dim_tipo_ticket tt
    ON ft.sk_tipo_ticket = tt.sk_tipo_ticket

LEFT JOIN dw.dim_status_ticket st
    ON ft.sk_status_ticket = st.sk_status_ticket

LEFT JOIN dw.dim_servidor s_ticket
    ON ft.sk_servidor = s_ticket.sk_servidor

-- 🔥 MAPEAMENTO (AQUI ESTÁ A MÁGICA)
LEFT JOIN dw.map_servidor_instancia m
    ON s_ticket.instancia = m.instancia

-- servidor físico (infra)
LEFT JOIN dw.dim_servidor s_infra
    ON m.host_name = s_infra.host_name

LEFT JOIN dw.fato_servidor fs
    ON fs.sk_servidor = s_infra.sk_servidor

LEFT JOIN dw.dim_tempo dt_servidor
    ON fs.sk_tempo_referencia = dt_servidor.sk_tempo
   AND dt_servidor.anomes = dt_ticket.anomes;
