-- Create table for transactions
create table if not exists transacoes (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  data date not null,
  descricao text not null,
  valor numeric not null,
  categoria text not null,
  tipo text not null, -- 'Receita' or 'Despesa'
  fonte text default 'Manual', -- 'PDF', 'CSV', 'Manual'
  user_id uuid default auth.uid() -- RLS: only the owner can see
);

-- Enable Row Level Security (RLS)
alter table transacoes enable row level security;

-- (Opcional - Para testes sem Auth) Permitir acesso a todos
-- REMOVA ISSO EM PRODUÇÃO SE TIVER AUTH:
drop policy if exists "Enable all for anon" on transacoes;

create policy "Enable all for anon"
on transacoes for all
to anon
using (true)
with check (true);

-- (Caso use Auth depois)
-- create policy "Users can limit usage to their own rows"
-- on transacoes for all
-- using (auth.uid() = user_id);
