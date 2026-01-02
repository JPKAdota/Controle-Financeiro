"use client";

import { useEffect, useState } from "react";

interface Transaction {
  data: string;
  descricao: string;
  valor: number;
  categoria: string;
  tipo: string;
}

export default function Home() {
  const [data, setData] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/transactions")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setData(data);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const totalReceitas = data
    .filter((t) => t.tipo === "Receita")
    .reduce((acc, curr) => acc + curr.valor, 0);

  const totalDespesas = data
    .filter((t) => t.tipo === "Despesa")
    .reduce((acc, curr) => acc + Math.abs(curr.valor), 0);

  const saldo = totalReceitas - totalDespesas;

  return (
    <div className="space-y-6 px-4">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>

      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
          <h3 className="text-gray-500 text-sm font-medium">Receitas</h3>
          <p className="text-2xl font-bold text-green-600">
            R$ {totalReceitas.toFixed(2)}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border-l-4 border-red-500">
          <h3 className="text-gray-500 text-sm font-medium">Despesas</h3>
          <p className="text-2xl font-bold text-red-600">
            R$ {totalDespesas.toFixed(2)}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500">
          <h3 className="text-gray-500 text-sm font-medium">Saldo</h3>
          <p className={`text-2xl font-bold ${saldo >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
            R$ {saldo.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Últimas Transações</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrição</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Categoria</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Valor</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan={4} className="px-6 py-4 text-center">Carregando...</td></tr>
              ) : data.length === 0 ? (
                <tr><td colSpan={4} className="px-6 py-4 text-center">Nenhuma transação encontrada.</td></tr>
              ) : (
                data.map((t, idx) => (
                  <tr key={idx}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{t.data}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{t.descricao}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                        {t.categoria}
                      </span>
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${t.tipo === 'Receita' ? 'text-green-600' : 'text-red-600'}`}>
                      {t.valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
