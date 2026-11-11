INSERT INTO public.usuarios (
    nome,
    tipo_usuario_id,
    niveis_acesso_id,
    matricula,
    setor_solicitante_id,
    cargo_id,
    cpf,
    email,
    telefone,
    password,
    ativo,
    updated_by
)
VALUES (
    'Administrador Docker',
    6,
    3,
    'admin-docker',
    1,
    1,
    '99999999999',
    'admin.public@gmail.com',
    '61999999999',
    '$argon2id$v=19$m=65536,t=3,p=4$/9VoZpTzqze8wS+RInM7nQ$dnaJ5tW1O8dY6gxv+vuec/IoCZhDpmJdvXFPLezX2IA',
    true,
    0
)
ON CONFLICT (email) DO UPDATE SET
    nome = EXCLUDED.nome,
    tipo_usuario_id = EXCLUDED.tipo_usuario_id,
    niveis_acesso_id = EXCLUDED.niveis_acesso_id,
    matricula = EXCLUDED.matricula,
    setor_solicitante_id = EXCLUDED.setor_solicitante_id,
    cargo_id = EXCLUDED.cargo_id,
    cpf = EXCLUDED.cpf,
    telefone = EXCLUDED.telefone,
    password = EXCLUDED.password,
    ativo = true,
    updated_by = EXCLUDED.updated_by,
    updated_at = date_trunc('second', now() AT TIME ZONE 'America/Sao_Paulo');
