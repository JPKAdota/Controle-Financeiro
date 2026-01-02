-- Create categories table
create table if not exists categorias (
  id uuid default gen_random_uuid() primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  nome text not null unique,
  tipo text not null, -- 'Despesa', 'Receita', 'Investimento'
  user_id uuid default auth.uid()
);

-- Enable RLS
alter table categorias enable row level security;

-- Public access policy (Temporary, same as transactions)
create policy "Enable all for anon"
on categorias for all
to anon
using (true)
with check (true);

-- Insert default categories
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
