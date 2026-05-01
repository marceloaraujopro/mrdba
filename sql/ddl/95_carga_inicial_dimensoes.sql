INSERT INTO dw.dim_cliente (nm_cliente)
VALUES
    ('SENAC'),
    ('MILLS'),
    ('AND'),
    ('SES')
ON CONFLICT (nm_cliente) DO NOTHING;

INSERT INTO dw.dim_tipo_ticket (nm_tipo_ticket)
VALUES
    ('Checklist'),
    ('Incidente'),
    ('CSI'),
    ('Crise'),
    ('Outro')
ON CONFLICT (nm_tipo_ticket) DO NOTHING;

INSERT INTO dw.dim_status_ticket (nm_status_ticket)
VALUES
    ('Aberto'),
    ('Em Execução'),
    ('Aguardando o cliente'),
    ('Resolvido'),
    ('Fechado'),
    ('Encerrado')
ON CONFLICT (nm_status_ticket) DO NOTHING;

INSERT INTO dw.dim_status_csi (nm_status_csi)
VALUES
    ('Aberto'),
    ('Em execução'),
    ('Implementado'),
    ('Aguardando resposta do cliente'),
    ('Encerrado - falta de contato'),
    ('Encerrado - recusado pelo cliente'),
    ('NA')
ON CONFLICT (nm_status_csi) DO NOTHING;
