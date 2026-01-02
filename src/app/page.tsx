"use client";
import { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend
} from "recharts";

interface DashboardData {
  expenses_by_category: { name: string; value: number }[];
  investments_evolution: { data: string; valor: number }[];
  metrics?: {
    receitas: number;
    despesas: number;
    saldo: number;
    investido: number;
  };
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8", "#82ca9d"];

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    fetch("/api/dashboard-charts")
      .then((res) => res.json())
      .then((data) => setData(data));
  }, []);

  if (!data) return <div className="text-center p-10">Carregando gráficos...</div>;

  const metrics = data.metrics || { receitas: 0, despesas: 0, saldo: 0, investido: 0 };

  // Helper para formatar moeda
  const formatMoney = (val: number) =>
    val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Relatório Financeiro</h1>

      {/* Cards de Métricas (Restaurados) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow border-l-4 border-green-500">
          <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400">Receitas</h2>
          <p className="text-2xl font-bold text-green-600">{formatMoney(metrics.receitas)}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow border-l-4 border-red-500">
          <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400">Despesas</h2>
          <p className="text-2xl font-bold text-red-600">{formatMoney(metrics.despesas)}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow border-l-4 border-blue-500">
          <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400">Saldo (Caixa)</h2>
          <p className={`text-2xl font-bold ${metrics.saldo >= 0 ? 'text-blue-600' : 'text-red-500'}`}>
            {formatMoney(metrics.saldo)}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Gráfico de Pizza - Despesas */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow h-96">
          <h2 className="text-lg font-medium mb-4 text-gray-900 dark:text-gray-100">Despesas por Categoria</h2>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data.expenses_by_category}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {data.expenses_by_category.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number | undefined) => formatMoney(value ?? 0)} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Gráfico de Linha - Investimentos */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow h-96">
          <h2 className="text-lg font-medium mb-4 text-gray-900 dark:text-gray-100">Evolução dos Investimentos</h2>
          <p className="text-sm text-gray-500 mb-2">Total Acumulado: {formatMoney(metrics.investido)}</p>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data.investments_evolution}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="data" />
              <YAxis />
              <Tooltip formatter={(value: number | undefined) => formatMoney(value ?? 0)} />
              <Legend />
              <Line type="monotone" dataKey="valor" stroke="#82ca9d" name="Investido" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
}
