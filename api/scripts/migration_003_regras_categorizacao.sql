-- Migração para bancos já existentes. Aplique com:
--   docker exec -i controle-financeiro-db psql -U postgres -d controle_financeiro < api/scripts/migration_003_regras_categorizacao.sql

create table if not exists regras_categorizacao (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  padrao text not null unique,
  categoria text not null
);
