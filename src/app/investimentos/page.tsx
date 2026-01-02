"use client";

import { useEffect, useState } from "react";
import { AlertCircle, Calendar } from "lucide-react";

interface Transaction {
    id: string;
    data: string;
    descricao: string;
    valor: number;
    categoria: string;
    tipo: string;
    data_vencimento?: string;
}

export default function InvestmentsPage() {
    const [data, setData] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedMonth, setSelectedMonth] = useState("Todos");

    // Form state
    const [formData, setFormData] = useState({
        data: new Date().toISOString().split('T')[0],
        descricao: "",
        valor: "",
        tipo: "Aporte",
        data_vencimento: ""
    });

    useEffect(() => {
        fetchInvestments();
    }, []);

    const fetchInvestments = () => {
        setLoading(true);
        fetch("/api/transactions")
            .then((res) => res.json())
            .then((data) => {
                const investments = data.filter(
                    (t: Transaction) => t.categoria === "Investimentos" || t.tipo === "Investimento"
                );
                setData(investments);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    };

    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        const tipoBackend = formData.tipo === "Aporte" ? "Despesa" : "Receita";
        const valorFloat = parseFloat(formData.valor.replace(',', '.'));

        const payload = {
            data: formData.data,
            descricao: formData.descricao,
            valor: Math.abs(valorFloat) * (tipoBackend === 'Despesa' ? -1 : 1),
            categoria: "Investimentos",
            tipo: tipoBackend,
            fonte: "Manual",
            data_vencimento: formData.data_vencimento || null
        };

        try {
            await fetch("/api/transactions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            setFormData({ ...formData, descricao: "", valor: "", data_vencimento: "" });
            fetchInvestments();
        } catch (error) {
            alert("Erro ao adicionar investimento");
        }
    };

    // --- FILTER & CALCULATIONS ---

    // 1. Get Unique Months
    const availableMonths = Array.from(new Set(data.map(t => {
        const date = new Date(t.data);
        const monthYear = date.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
        return monthYear.charAt(0).toUpperCase() + monthYear.slice(1);
    }))).sort((a, b) => {
        // Simple Sort relying on string for now or use finding ref
        const tA = data.find(t => {
            const d = new Date(t.data).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
            return (d.charAt(0).toUpperCase() + d.slice(1)) === a;
        });
        const tB = data.find(t => {
            const d = new Date(t.data).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
            return (d.charAt(0).toUpperCase() + d.slice(1)) === b;
        });
        if (!tA || !tB) return 0;
        return new Date(tB.data).getTime() - new Date(tA.data).getTime();
    });

    // 2. Filter Transactions by Month
    const filteredData = data.filter(t => {
        if (selectedMonth === "Todos") return true;
        const date = new Date(t.data);
        const monthYear = date.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
        const formatted = monthYear.charAt(0).toUpperCase() + monthYear.slice(1);
        return formatted === selectedMonth;
    });

    // 3. Calc Total Invested
    const totalInvestido = filteredData.reduce((acc, curr) => {
        return acc + (curr.tipo === 'Despesa' ? Math.abs(curr.valor) : -1 * Math.abs(curr.valor));
    }, 0);

    // 4. Notification Logic (Vencimento Check)
    const checkApproachingMaturity = (dateStr?: string) => {
        if (!dateStr) return false;
        const today = new Date();
        const due = new Date(dateStr);
        const diffTime = due.getTime() - today.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        // Alert if within 30 days and not passed too long ago? Or just future?
        // Let's say: Alert if between -1 (just expired) and 30 days.
        return diffDays >= -1 && diffDays <= 30;
    };


    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Investimentos</h1>

                <div className="flex items-center gap-4">
                    <select
                        value={selectedMonth}
                        onChange={(e) => setSelectedMonth(e.target.value)}
                        className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
                    >
                        <option value="Todos">Todos os Meses</option>
                        {availableMonths.map(m => (
                            <option key={m} value={m}>{m}</option>
                        ))}
                    </select>

                    <div className="bg-green-100 text-green-800 px-4 py-2 rounded-lg font-bold border border-green-200">
                        Total: {totalInvestido.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </div>
                </div>
            </div>

            {/* Add Form */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <h2 className="text-lg font-medium mb-4 text-gray-900 dark:text-gray-100">Novo Aporte / Resgate</h2>
                <form onSubmit={handleAdd} className="grid grid-cols-1 md:grid-cols-6 gap-4 items-end">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Data Aporte</label>
                        <input
                            type="date"
                            value={formData.data}
                            onChange={(e) => setFormData({ ...formData, data: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
                            required
                        />
                    </div>
                    <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Descrição</label>
                        <input
                            type="text"
                            placeholder="Ex: Tesouro Selic 2029"
                            value={formData.descricao}
                            onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Tipo</label>
                        <select
                            value={formData.tipo}
                            onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
                        >
                            <option value="Aporte">Aporte (Investir)</option>
                            <option value="Resgate">Resgate (Sacar)</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Vencimento (Opcional)</label>
                        <input
                            type="date"
                            value={formData.data_vencimento}
                            onChange={(e) => setFormData({ ...formData, data_vencimento: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Valor (R$)</label>
                        <input
                            type="number"
                            step="0.01"
                            value={formData.valor}
                            onChange={(e) => setFormData({ ...formData, valor: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
                            required
                        />
                    </div>
                    <button
                        type="submit"
                        className="md:col-span-6 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition"
                    >
                        Salvar
                    </button>
                </form>
            </div>

            {/* List */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-900">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrição</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vencimento</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Valor</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                            {filteredData.map((transaction) => {
                                const isApproaching = checkApproachingMaturity(transaction.data_vencimento);
                                return (
                                    <tr key={transaction.id} className={isApproaching ? "bg-orange-50 dark:bg-orange-900/10" : ""}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                            {new Date(transaction.data).toLocaleDateString('pt-BR')}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                                            {transaction.descricao}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                                            {transaction.data_vencimento ? (
                                                <div className={`flex items-center ${isApproaching ? "text-orange-600 font-bold" : ""}`}>
                                                    <Calendar className="w-4 h-4 mr-2" />
                                                    {new Date(transaction.data_vencimento).toLocaleDateString("pt-BR")}
                                                    {isApproaching && <AlertCircle className="w-4 h-4 ml-2" />}
                                                </div>
                                            ) : (
                                                <span className="text-gray-400">-</span>
                                            )}
                                        </td>
                                        <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${transaction.tipo === 'Despesa' ? 'text-green-600' : 'text-red-600'}`}>
                                            {transaction.tipo === 'Despesa' ? '+' : '-'} {Math.abs(transaction.valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                        </td>
                                    </tr>
                                )
                            })}

                            {filteredData.length === 0 && !loading && (
                                <tr>
                                    <td colSpan={4} className="px-6 py-4 text-center text-gray-500">Nenhum investimento encontrado para este período.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
