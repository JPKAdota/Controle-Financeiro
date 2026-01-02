-- Add data_vencimento column to transacoes table
alter table transacoes 
add column if not exists data_vencimento date;
