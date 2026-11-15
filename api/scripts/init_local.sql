-- Schema local (Postgres via Docker), sem Supabase Auth/RLS.
-- Executado automaticamente pelo container na primeira inicialização
-- (docker-entrypoint-initdb.d), ou manualmente com:
--   psql "$DATABASE_URL" -f api/scripts/init_local.sql

create extension if not exists pgcrypto;

create table if not exists transacoes (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  data date not null,
  descricao text not null,
  valor numeric not null,
  categoria text not null,
  tipo text not null, -- 'Receita', 'Despesa' ou 'Investimento'
  fonte text default 'Manual', -- 'PDF', 'CSV', 'Manual'
  data_vencimento date
);

create table if not exists categorias (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  nome text not null unique,
  tipo text not null -- 'Despesa', 'Receita' ou 'Investimento'
);

-- Orçamento mensal recorrente por categoria (opcional). Ao ser removida a
-- categoria, o orçamento associado também é removido.
create table if not exists orcamentos (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  categoria text not null unique references categorias (nome) on delete cascade,
  valor_limite numeric not null check (valor_limite >= 0)
);

-- Regras de categorização aprendidas: quando o usuário corrige manualmente a
-- categoria de uma transação, o nome do PIX/TED/DOC extraído da descrição é
-- salvo aqui e aplicado automaticamente em transações futuras (e retroativas)
-- com o mesmo remetente/destinatário.
create table if not exists regras_categorizacao (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  padrao text not null unique,
  categoria text not null
);

insert into categorias (nome, tipo) values
  ('Comida', 'Despesa'),
  ('Transporte', 'Despesa'),
  ('Moradia', 'Despesa'),
  ('Lazer', 'Despesa'),
  ('Saúde', 'Despesa'),
  ('Educação', 'Despesa'),
  ('Investimentos', 'Investimento'),
  ('Salário', 'Receita'),
  ('Outros', 'Despesa')
on conflict (nome) do nothing;
