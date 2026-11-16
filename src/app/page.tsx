"use client";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
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

// Categorias além do top N viram "Outras" para o ranking continuar legível.
const MAX_CATEGORIAS = 7;
const CATEGORIA_PENDENTE = "A Categorizar";

const AXIS_TICK = { fill: "var(--viz-muted)", fontSize: 12 };

const compactMoney = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  notation: "compact",
  maximumFractionDigits: 0,
});

function ChartTooltip({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-3 py-2 shadow-lg text-sm">
      <p className="font-medium text-gray-900 dark:text-gray-100 mb-1">{title}</p>
      {children}
    </div>
  );
}

function TooltipRow({ color, label, value }: { color?: string; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-6">
      <span className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
        {color ? (
          <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: color }} />
        ) : (
          <span className="inline-block w-2.5" />
        )}
        {label}
      </span>
      <span className="tabular-nums font-medium text-gray-900 dark:text-gray-100">{value}</span>
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-300">
      <span className="inline-block w-3 h-3 rounded-sm" style={{ background: color }} />
      {label}
    </span>
  );
}

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

  // Helper para formatar "YYYY-MM-DD" como "set/26" no eixo do tempo
  const formatDateAxis = (iso: string) => {
    const date = new Date(iso + 'T00:00:00');
    return date.toLocaleDateString('pt-BR', { month: 'short', year: '2-digit' }).replace('.', '').replace(' de ', '/');
  };

  // Ranking de despesas: maiores primeiro, cauda longa somada em "Outras"
  const categoriasOrdenadas = [...data.expenses_by_category]
    .filter((c) => c.value > 0)
    .sort((a, b) => b.value - a.value);
  const totalDespesasCategorias = categoriasOrdenadas.reduce((s, c) => s + c.value, 0);
  const categoriasRanking = categoriasOrdenadas.length > MAX_CATEGORIAS
    ? [
        ...categoriasOrdenadas.slice(0, MAX_CATEGORIAS - 1),
        {
          name: `Outras (${categoriasOrdenadas.length - MAX_CATEGORIAS + 1})`,
          value: categoriasOrdenadas.slice(MAX_CATEGORIAS - 1).reduce((s, c) => s + c.value, 0),
        },
      ]
    : categoriasOrdenadas;
  const maiorCategoria = categoriasRanking[0]?.value || 1;

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
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">Receita x Despesa por Mês</h2>
            <div className="flex items-center gap-4">
              <LegendItem color="var(--viz-receita)" label="Receita" />
              <LegendItem color="var(--viz-despesa)" label="Despesa" />
            </div>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data.monthly_evolution}
                margin={{ top: 8, right: 4, left: 0, bottom: 0 }}
                barGap={2}
                barCategoryGap="24%"
              >
                <CartesianGrid vertical={false} stroke="var(--viz-grid)" />
                <XAxis
                  dataKey="mes"
                  tickFormatter={formatMonth}
                  tick={AXIS_TICK}
                  tickLine={false}
                  axisLine={{ stroke: "var(--viz-axis)" }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tickFormatter={(v: number) => compactMoney.format(v)}
                  tick={AXIS_TICK}
                  tickLine={false}
                  axisLine={false}
                  width={76}
                />
                <Tooltip
                  cursor={{ fill: "var(--viz-hover)" }}
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null;
                    const ponto = payload[0].payload as { receita: number; despesa: number };
                    const saldo = ponto.receita - ponto.despesa;
                    return (
                      <ChartTooltip title={formatMonth(String(label))}>
                        <TooltipRow color="var(--viz-receita)" label="Receita" value={formatMoney(ponto.receita)} />
                        <TooltipRow color="var(--viz-despesa)" label="Despesa" value={formatMoney(ponto.despesa)} />
                        <div className="mt-1 pt-1 border-t border-gray-200 dark:border-gray-700">
                          <TooltipRow label={saldo >= 0 ? "Sobrou" : "Faltou"} value={formatMoney(Math.abs(saldo))} />
                        </div>
                      </ChartTooltip>
                    );
                  }}
                />
                <Bar dataKey="receita" name="Receita" fill="var(--viz-receita)" radius={[4, 4, 0, 0]} maxBarSize={32} />
                <Bar dataKey="despesa" name="Despesa" fill="var(--viz-despesa)" radius={[4, 4, 0, 0]} maxBarSize={32} />
              </BarChart>
            </ResponsiveContainer>
          </div>
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

        {/* Ranking de Despesas por Categoria */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-baseline justify-between gap-3 mb-5">
            <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">Despesas por Categoria</h2>
            <span className="text-sm text-gray-500 dark:text-gray-400 tabular-nums">
              {formatMoney(totalDespesasCategorias)}
            </span>
          </div>
          {categoriasRanking.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400">Nenhuma despesa no período.</p>
          ) : (
            <ul className="space-y-3.5">
              {categoriasRanking.map((c) => {
                const pendente = c.name === CATEGORIA_PENDENTE;
                const pct = totalDespesasCategorias ? (c.value / totalDespesasCategorias) * 100 : 0;
                return (
                  <li
                    key={c.name}
                    className="group"
                    title={`${c.name}: ${formatMoney(c.value)} (${pct.toFixed(1).replace('.', ',')}%)`}
                  >
                    <div className="flex items-baseline justify-between gap-3 mb-1.5 text-sm">
                      <span className="text-gray-700 dark:text-gray-200 truncate">
                        {c.name}
                        {pendente && (
                          <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">revisar</span>
                        )}
                      </span>
                      <span className="shrink-0 tabular-nums">
                        <span className="font-medium text-gray-900 dark:text-gray-100">{formatMoney(c.value)}</span>
                        <span className="ml-2 inline-block w-10 text-right text-gray-500 dark:text-gray-400">
                          {pct < 1 ? '<1' : pct.toFixed(0)}%
                        </span>
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-gray-100 dark:bg-gray-700/60">
                      <div
                        className="h-2 rounded-full transition-[filter] group-hover:brightness-110"
                        style={{
                          width: `${Math.max((c.value / maiorCategoria) * 100, 1.5)}%`,
                          background: pendente ? "var(--viz-pending)" : "var(--viz-despesa)",
                        }}
                      />
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        {/* Gráfico de Área - Investimentos */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow flex flex-col">
          <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">Evolução dos Investimentos</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Total acumulado</p>
          <p className="text-2xl font-semibold tabular-nums text-gray-900 dark:text-gray-100 mb-4">
            {formatMoney(metrics.investido)}
          </p>
          <div className="h-64 mt-auto">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={data.investments_evolution}
                margin={{ top: 8, right: 4, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="investidoGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--viz-invest)" stopOpacity={0.22} />
                    <stop offset="100%" stopColor="var(--viz-invest)" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="var(--viz-grid)" />
                <XAxis
                  dataKey="data"
                  tickFormatter={formatDateAxis}
                  tick={AXIS_TICK}
                  tickLine={false}
                  axisLine={{ stroke: "var(--viz-axis)" }}
                  minTickGap={48}
                />
                <YAxis
                  domain={[0, (dataMax: number) => Math.ceil((dataMax * 1.05) / 25000) * 25000]}
                  tickFormatter={(v: number) => compactMoney.format(v)}
                  tick={AXIS_TICK}
                  tickLine={false}
                  axisLine={false}
                  width={76}
                  allowDataOverflow
                />
                <Tooltip
                  cursor={{ stroke: "var(--viz-axis)", strokeWidth: 1 }}
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null;
                    return (
                      <ChartTooltip title={formatDate(String(label))}>
                        <TooltipRow
                          color="var(--viz-invest)"
                          label="Investido"
                          value={formatMoney(Number(payload[0].value) || 0)}
                        />
                      </ChartTooltip>
                    );
                  }}
                />
                {/* stepAfter: o saldo só muda quando há aporte/resgate, sem curvas inventadas entre pontos */}
                <Area
                  type="stepAfter"
                  dataKey="valor"
                  stroke="var(--viz-invest)"
                  strokeWidth={2}
                  fill="url(#investidoGradient)"
                  name="Investido"
                  dot={false}
                  activeDot={{ r: 5, strokeWidth: 2, stroke: "var(--viz-surface)", fill: "var(--viz-invest)" }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}
