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
