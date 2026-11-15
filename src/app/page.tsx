"use client";
import { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend
} from "recharts";
import { apiFetch } from "@/lib/api";

interface DashboardData {
  expenses_by_category: { name: string; value: number }[];
  investments_evolution: { data: string; valor: number }[];
  monthly_evolution?: { mes: string; receita: number; despesa: number }[];
  contas_a_vencer?: {
    id: string;
    descricao: string;
    valor: number;
    categoria: string;
    data_vencimento: string;
  }[];
  orcamentos?: {
    categoria: string;
    limite: number;
    gasto: number;
    percentual: number;
    estourado: boolean;
  }[];
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
  const [selectedMonth, setSelectedMonth] = useState<string>("");

  useEffect(() => {
    const url = selectedMonth ? `/api/dashboard-charts?month=${selectedMonth}` : "/api/dashboard-charts";
    apiFetch<DashboardData>(url)
      .then(setData)
      .catch(() => setData({ expenses_by_category: [], investments_evolution: [] }));
  }, [selectedMonth]);

  if (!data) return <div className="text-center p-10">Carregando gráficos...</div>;

  const metrics = data.metrics || { receitas: 0, despesas: 0, saldo: 0, investido: 0 };
  const availableMonths = [...(data.monthly_evolution?.map(m => m.mes) || [])].sort().reverse();

  // Helper para formatar moeda
  const formatMoney = (val: number) =>
    val.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  // Helper para formatar "YYYY-MM" como "set/26"
  const formatMonth = (mes: string) => {
    const [ano, m] = mes.split('-');
    const date = new Date(Number(ano), Number(m) - 1, 1);
    return date.toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' }).replace('.', '');
  };

  // Helper para formatar "YYYY-MM-DD" como "07 set"
  const formatDate = (iso: string) => {
    const date = new Date(iso + 'T00:00:00');
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }).replace('.', '');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Relatório Financeiro</h1>
        <select
          value={selectedMonth}
          onChange={(e) => setSelectedMonth(e.target.value)}
          className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
        >
          <option value="">Todos os Meses</option>
          {availableMonths.map((m) => (
            <option key={m} value={m}>{formatMonth(m)}</option>
          ))}
        </select>
      </div>
      <p className="text-sm text-gray-500 -mt-4">
        {selectedMonth
          ? "Receitas, despesas e saldo do mês selecionado. Os gráficos de evolução continuam mostrando o histórico completo."
          : "Receitas, despesas e saldo de todo o histórico."}
      </p>

      {/* Contas a Vencer (próximos 7 dias) */}
      {data.contas_a_vencer && data.contas_a_vencer.length > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-6 rounded-lg shadow">
          <h2 className="text-lg font-medium mb-3 text-yellow-900 dark:text-yellow-200">⏰ Contas a Vencer (próximos 7 dias)</h2>
          <ul className="divide-y divide-yellow-200 dark:divide-yellow-800">
            {data.contas_a_vencer.map((c) => {
              const hoje = new Date();
              hoje.setHours(0, 0, 0, 0);
              const vencimento = new Date(c.data_vencimento + "T00:00:00");
              const dias = Math.round((vencimento.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24));
              const urgente = dias <= 2;
              return (
                <li key={c.id} className="py-2 flex justify-between items-center">
                  <div>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{c.descricao}</span>
                    <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">({c.categoria})</span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">{formatMoney(c.valor)}</span>
                    <span className={`ml-3 text-xs font-medium ${urgente ? 'text-red-600' : 'text-yellow-700 dark:text-yellow-400'}`}>
                      {dias === 0 ? 'vence hoje' : dias === 1 ? 'vence amanhã' : `vence em ${dias} dias`}
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}

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

      {/* Receita vs Despesa mês a mês */}
      {data.monthly_evolution && data.monthly_evolution.length > 0 && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow h-80">
          <h2 className="text-lg font-medium mb-4 text-gray-900 dark:text-gray-100">Receita x Despesa por Mês</h2>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.monthly_evolution} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="mes" tickFormatter={formatMonth} />
              <YAxis />
              <Tooltip formatter={(value: number | undefined) => formatMoney(value ?? 0)} labelFormatter={formatMonth} />
              <Legend />
              <Bar dataKey="receita" name="Receita" fill="#22c55e" />
              <Bar dataKey="despesa" name="Despesa" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Orçamentos do Mês */}
      {data.orcamentos && data.orcamentos.length > 0 && (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h2 className="text-lg font-medium mb-4 text-gray-900 dark:text-gray-100">Orçamentos do Mês</h2>
          <div className="space-y-4">
            {data.orcamentos.map((o) => {
              const pct = Math.min(o.percentual, 100);
              const barColor = o.estourado ? 'bg-red-500' : o.percentual >= 80 ? 'bg-yellow-500' : 'bg-green-500';
              return (
                <div key={o.categoria}>
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {o.categoria} {o.estourado && <span className="text-red-600">⚠️ acima do limite</span>}
                    </span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {formatMoney(o.gasto)} / {formatMoney(o.limite)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full ${barColor}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Gráfico de Pizza - Despesas */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow h-96">
          <h2 className="text-lg font-medium mb-4 text-gray-900 dark:text-gray-100">Despesas por Categoria</h2>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart margin={{ top: 10, right: 40, bottom: 10, left: 40 }}>
              <Pie
                data={data.expenses_by_category}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  (percent ?? 0) >= 0.05 ? `${name} ${((percent ?? 0) * 100).toFixed(0)}%` : ''
                }
                outerRadius="65%"
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

        {/* Gráfico de Área - Investimentos */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow h-96">
          <h2 className="text-lg font-medium mb-4 text-gray-900 dark:text-gray-100">Evolução dos Investimentos</h2>
          <p className="text-sm text-gray-500 mb-2">Total Acumulado: {formatMoney(metrics.investido)}</p>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data.investments_evolution}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <defs>
                <linearGradient id="investidoGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.5} />
                  <stop offset="95%" stopColor="#82ca9d" stopOpacity={0.03} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="data" tickFormatter={formatDate} minTickGap={40} />
              <YAxis
                domain={[0, (dataMax: number) => Math.ceil((dataMax * 1.05) / 25000) * 25000]}
                tickFormatter={(v: number) => v.toLocaleString('pt-BR')}
                allowDataOverflow
              />
              <Tooltip formatter={(value: number | undefined) => formatMoney(value ?? 0)} labelFormatter={formatDate} />
              <Legend />
              <Area
                type="monotone"
                dataKey="valor"
                stroke="#2f9e6e"
                strokeWidth={2}
                fill="url(#investidoGradient)"
                name="Investido"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
}
