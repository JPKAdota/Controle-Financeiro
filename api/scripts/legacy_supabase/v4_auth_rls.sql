-- Execute no Supabase SQL Editor depois de definir os usuários existentes.
-- Registros antigos com user_id NULL ficarão invisíveis pelas policies até serem associados.

alter table transacoes enable row level security;
alter table categorias enable row level security;

alter table categorias add column if not exists user_id uuid default auth.uid();
alter table categorias drop constraint if exists categorias_nome_key;

create unique index if not exists categorias_user_nome_key
  on categorias (user_id, nome)
  where user_id is not null;

drop policy if exists "Enable all for anon" on transacoes;
drop policy if exists "Enable all for anon" on categorias;
drop policy if exists "Users can read own transactions" on transacoes;
drop policy if exists "Users can insert own transactions" on transacoes;
drop policy if exists "Users can update own transactions" on transacoes;
drop policy if exists "Users can delete own transactions" on transacoes;
drop policy if exists "Users can read own categories" on categorias;
drop policy if exists "Users can insert own categories" on categorias;
drop policy if exists "Users can update own categories" on categorias;
drop policy if exists "Users can delete own categories" on categorias;

create policy "Users can read own transactions"
on transacoes for select to authenticated
using (auth.uid() = user_id);

create policy "Users can insert own transactions"
on transacoes for insert to authenticated
with check (auth.uid() = user_id);

create policy "Users can update own transactions"
on transacoes for update to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can delete own transactions"
on transacoes for delete to authenticated
using (auth.uid() = user_id);

create policy "Users can read own categories"
on categorias for select to authenticated
using (auth.uid() = user_id);

create policy "Users can insert own categories"
on categorias for insert to authenticated
with check (auth.uid() = user_id);

create policy "Users can update own categories"
on categorias for update to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can delete own categories"
on categorias for delete to authenticated
using (auth.uid() = user_id);

-- Depois de associar os dados antigos a um usuário, aplique:
-- alter table transacoes alter column user_id set not null;
-- alter table categorias alter column user_id set not null;
