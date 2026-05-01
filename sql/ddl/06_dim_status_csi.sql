CREATE TABLE IF NOT EXISTS dw.dim_status_csi (
    sk_status_csi   BIGSERIAL PRIMARY KEY,
    nm_status_csi   VARCHAR(100) NOT NULL UNIQUE
);

COMMENT ON TABLE dw.dim_status_csi IS 
'Dimensão específica para classificação de status de tickets do tipo CSI.';

COMMENT ON COLUMN dw.dim_status_csi.nm_status_csi IS 
'Status do processo CSI (ex: Implementado, Concluído, Cancelado, NA).';
