-- Migração para bancos já existentes (init_local.sql só roda automaticamente
-- na primeira criação do volume Docker). Aplique com:
--   docker exec -i controle-financeiro-db psql -U postgres -d controle_financeiro -f - < api/scripts/migration_002_orcamentos.sql
-- ou, de dentro do container:
--   docker exec controle-financeiro-db psql -U postgres -d controle_financeiro -c "<conteúdo abaixo>"

create table if not exists orcamentos (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  categoria text not null unique references categorias (nome) on delete cascade,
  valor_limite numeric not null check (valor_limite >= 0)
);
