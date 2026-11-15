"use client";

import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface Transaction {
    id: string;
    data: string;
    descricao: string;
    valor: number;
    categoria: string;
    tipo: string;
    data_vencimento?: string | null;
}

interface Category {
    id: string;
    nome: string;
    tipo: string;
}

export default function TransactionsPage() {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [categories, setCategories] = useState<Category[]>([]);
    const [loading, setLoading] = useState(true);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editCategory, setEditCategory] = useState<string>("");

    // Search & Filter state
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedMonth, setSelectedMonth] = useState("Todos");
    const [viewMode, setViewMode] = useState<"Todas" | "Despesas" | "Receitas" | "Investimentos">("Todas");
    const [selectedCategory, setSelectedCategory] = useState("Todas");
    const [selectedType, setSelectedType] = useState("Todos");

    // New manual transaction form state
    const [showNewForm, setShowNewForm] = useState(false);
    const [savingNew, setSavingNew] = useState(false);
    const todayIso = new Date().toISOString().slice(0, 10);
    const [newTx, setNewTx] = useState({
        data: todayIso,
        descricao: "",
        valor: "",
        categoria: "",
        tipo: "Despesa",
        data_vencimento: "",
    });

    useEffect(() => {
        fetchData();
        fetchCategories();
    }, []);

    const fetchData = async () => {
        try {
            const data = await apiFetch<Transaction[]>("/api/transactions");
            setTransactions(data || []);
        } catch (e) { console.error(e) } finally { setLoading(false) }
    };

    const fetchCategories = async () => {
        try {
            const data = await apiFetch<Category[]>("/api/categories");
            setCategories(data || []);
        } catch (e) { console.error(e) }
    };

    const handleCategoryChange = (nome: string) => {
        const cat = categories.find((c) => c.nome === nome);
        setNewTx({ ...newTx, categoria: nome, tipo: cat?.tipo || newTx.tipo });
    };

    const handleAddTransaction = async (e: React.FormEvent) => {
        e.preventDefault();
        const valorNum = parseFloat(newTx.valor.replace(",", "."));
        if (!newTx.categoria) { alert("Selecione uma categoria"); return; }
        if (isNaN(valorNum) || valorNum <= 0) { alert("Informe um valor válido"); return; }

        const valorComSinal = newTx.tipo === "Receita" ? Math.abs(valorNum) : -Math.abs(valorNum);

        setSavingNew(true);
        try {
            await apiFetch("/api/transactions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    data: newTx.data,
                    descricao: newTx.descricao,
                    valor: valorComSinal,
                    categoria: newTx.categoria,
                    tipo: newTx.tipo,
                    fonte: "Manual",
                    data_vencimento: newTx.data_vencimento || null,
                }),
            });
            setNewTx({ data: todayIso, descricao: "", valor: "", categoria: "", tipo: "Despesa", data_vencimento: "" });
            setShowNewForm(false);
            fetchData();
        } catch (e) {
            alert("Erro ao adicionar transação");
        } finally {
            setSavingNew(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Excluir transação?")) return;
        try {
            await apiFetch(`/api/transactions/${id}`, { method: "DELETE" });
            setTransactions(transactions.filter(t => t.id !== id));
        } catch (e) { alert("Erro ao excluir") }
    };

    const handleDeleteAll = async () => {
        if (!confirm("TEM CERTEZA? Isso apagará TODAS as transações do sistema permanentemente.")) return;
        if (!confirm("Sério mesmo? Não tem volta.")) return;

        try {
            setLoading(true);
            await apiFetch("/api/transactions-all", { method: "DELETE" });
            setTransactions([]);
        } catch (e) {
            alert("Erro ao excluir tudo");
        } finally {
            setLoading(false);
        }
    };

    const startEdit = (t: Transaction) => {
        setEditingId(t.id);
        setEditCategory(t.categoria || "");
    };

    const saveEdit = async (id: string) => {
        try {
            await apiFetch(`/api/transactions/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ categoria: editCategory })
            });
            setTransactions(transactions.map(t => t.id === id ? { ...t, categoria: editCategory } : t));
            setEditingId(null);
            setEditingId(null);
        } catch (e) { alert("Erro ao salvar") }
    };

    // --- Search & Grouping Logic ---

    // 1. Get Unique Months for Selector
    const availableMonths = Array.from(new Set(transactions.map(t => {
        const date = new Date(t.data);
        const monthYear = date.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
        return monthYear.charAt(0).toUpperCase() + monthYear.slice(1);
    }))).sort((a, b) => {
        const tA = transactions.find(t => {
            const d = new Date(t.data).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
            return (d.charAt(0).toUpperCase() + d.slice(1)) === a;
        });
        const tB = transactions.find(t => {
            const d = new Date(t.data).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
            return (d.charAt(0).toUpperCase() + d.slice(1)) === b;
        });
        if (!tA || !tB) return 0;
        return new Date(tB.data).getTime() - new Date(tA.data).getTime();
    });

    // 2. Filter
    const filteredTransactions = transactions.filter(t => {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch = (
            t.descricao.toLowerCase().includes(searchLower) ||
            (t.categoria || "").toLowerCase().includes(searchLower) ||
            t.data.includes(searchLower) ||
            t.valor.toString().includes(searchLower)
        );

        let matchesMonth = true;
        if (selectedMonth !== "Todos") {
            const date = new Date(t.data);
            const monthYear = date.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
            const formatted = monthYear.charAt(0).toUpperCase() + monthYear.slice(1);
            if (formatted !== selectedMonth) matchesMonth = false;
        }

        const matchesCategory = selectedCategory === "Todas" || (t.categoria || "A Categorizar") === selectedCategory;
        const matchesType = selectedType === "Todos" || t.tipo === selectedType;

        let matchesViewMode = true;
        if (viewMode === "Despesas") matchesViewMode = t.tipo === "Despesa" && t.categoria !== "Investimentos";
        else if (viewMode === "Receitas") matchesViewMode = t.tipo === "Receita" && t.categoria !== "Investimentos";
        else if (viewMode === "Investimentos") matchesViewMode = t.categoria === "Investimentos";

        return matchesSearch && matchesMonth && matchesCategory && matchesType && matchesViewMode;
    });

    // 3. Group by Month
    const groupedTransactions: Record<string, Transaction[]> = {};

    filteredTransactions.forEach(t => {
        const date = new Date(t.data);
        const monthYear = date.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
        const formattedGroup = monthYear.charAt(0).toUpperCase() + monthYear.slice(1);

        if (!groupedTransactions[formattedGroup]) {
            groupedTransactions[formattedGroup] = [];
        }
        groupedTransactions[formattedGroup].push(t);
    });

    const sortedGroupKeys = Object.keys(groupedTransactions).sort((a, b) => {
        const dateA = new Date(groupedTransactions[a][0].data);
        const dateB = new Date(groupedTransactions[b][0].data);
        return dateB.getTime() - dateA.getTime(); // Descending
    });

    // --- Totals Calculation ---
    // Investimentos (aportes/resgates) não entram aqui - são movimentação de
    // patrimônio, não "receita"/"despesa" de consumo, e já têm seu próprio
    // total na aba Investimentos.
    const totalReceitas = filteredTransactions
        .filter(t => t.tipo === 'Receita' && t.categoria !== 'Investimentos')
        .reduce((acc, t) => acc + Math.abs(Number(t.valor)), 0);

    const totalDespesas = filteredTransactions
        .filter(t => t.tipo === 'Despesa' && t.categoria !== 'Investimentos')
        .reduce((acc, t) => acc + Math.abs(Number(t.valor)), 0);

    const saldo = totalReceitas - totalDespesas;

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Gerenciar Transações</h1>
                    <span className="text-gray-500 text-sm">{filteredTransactions.length} registros exibidos</span>
                </div>

                {/* Quick view tabs */}
                <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
                    {(["Todas", "Receitas", "Despesas", "Investimentos"] as const).map((mode) => (
                        <button
                            key={mode}
                            onClick={() => setViewMode(mode)}
                            className={`px-3 py-1.5 text-sm font-medium rounded-md transition ${
                                viewMode === mode
                                    ? "bg-indigo-600 text-white shadow"
                                    : "text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
                            }`}
                        >
                            {mode}
                        </button>
                    ))}
                </div>
            </div>

            <div className="flex flex-col md:flex-row justify-end items-center gap-4">
                <div className="flex flex-col md:flex-row gap-4 w-full md:w-auto items-center">

                    {/* Month Selector */}
                    <select
                        value={selectedMonth}
                        onChange={(e) => setSelectedMonth(e.target.value)}
                        className="block w-full md:w-48 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
                    >
                        <option value="Todos">Todos os Meses</option>
                        {availableMonths.map(m => (
                            <option key={m} value={m}>{m}</option>
                        ))}
                    </select>

                    {/* Type Filter */}
                    <select
                        value={selectedType}
                        onChange={(e) => setSelectedType(e.target.value)}
                        className="block w-full md:w-40 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
                    >
                        <option value="Todos">Todos os Tipos</option>
                        <option value="Receita">Receita</option>
                        <option value="Despesa">Despesa</option>
                        <option value="Investimento">Investimento</option>
                    </select>

                    {/* Category Filter */}
                    <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="block w-full md:w-48 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
                    >
                        <option value="Todas">Todas as Categorias</option>
                        <option value="A Categorizar">A Categorizar</option>
                        {categories.map(c => (
                            <option key={c.id} value={c.nome}>{c.nome}</option>
                        ))}
                    </select>

                    {/* Search Input */}
                    <div className="relative flex-1 md:w-64 w-full">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <Search className="h-5 w-5 text-gray-400" />
                        </div>
                        <input
                            type="text"
                            placeholder="Buscar..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="pl-10 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-white dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
                        />
                    </div>

                    <button
                        onClick={() => setShowNewForm(!showNewForm)}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md font-semibold text-sm shadow-md transition whitespace-nowrap"
                    >
                        {showNewForm ? "Cancelar" : "+ Nova Transação"}
                    </button>

                    <button
                        onClick={handleDeleteAll}
                        className="bg-red-600 hover:bg-red-800 text-white px-4 py-2 rounded-md font-bold text-sm shadow-md transition whitespace-nowrap hidden md:block"
                        title="Excluir tudo"
                    >
                        🗑️
                    </button>
                </div>
            </div>

            {/* New Transaction Form */}
            {showNewForm && (
                <form onSubmit={handleAddTransaction} className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow flex flex-wrap gap-4 items-end">
                    <div className="w-40">
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Data</label>
                        <input
                            type="date"
                            required
                            value={newTx.data}
                            onChange={(e) => setNewTx({ ...newTx, data: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2 text-sm"
                        />
                    </div>
                    <div className="flex-1 min-w-[200px]">
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Descrição</label>
                        <input
                            type="text"
                            required
                            value={newTx.descricao}
                            onChange={(e) => setNewTx({ ...newTx, descricao: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2 text-sm"
                        />
                    </div>
                    <div className="w-36">
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Valor (R$)</label>
                        <input
                            type="number"
                            step="0.01"
                            min="0.01"
                            required
                            value={newTx.valor}
                            onChange={(e) => setNewTx({ ...newTx, valor: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2 text-sm"
                        />
                    </div>
                    <div className="w-44">
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Categoria</label>
                        <select
                            required
                            value={newTx.categoria}
                            onChange={(e) => handleCategoryChange(e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2 text-sm"
                        >
                            <option value="">Selecione...</option>
                            {categories.map((c) => (
                                <option key={c.id} value={c.nome}>{c.nome}</option>
                            ))}
                        </select>
                    </div>
                    <div className="w-36">
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Tipo</label>
                        <select
                            value={newTx.tipo}
                            onChange={(e) => setNewTx({ ...newTx, tipo: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2 text-sm"
                        >
                            <option value="Despesa">Despesa</option>
                            <option value="Receita">Receita</option>
                            <option value="Investimento">Investimento</option>
                        </select>
                    </div>
                    <div className="w-40">
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">Vencimento (opcional)</label>
                        <input
                            type="date"
                            value={newTx.data_vencimento}
                            onChange={(e) => setNewTx({ ...newTx, data_vencimento: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2 text-sm"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={savingNew}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md font-semibold text-sm shadow-md transition disabled:opacity-50"
                    >
                        {savingNew ? "Salvando..." : "Adicionar"}
                    </button>
                </form>
            )}

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-green-100 dark:bg-green-900/30 p-4 rounded-lg border border-green-200 dark:border-green-800">
                    <h3 className="text-green-800 dark:text-green-300 text-sm font-semibold uppercase tracking-wider">Receitas</h3>
                    <p className="text-2xl font-bold text-green-900 dark:text-white">
                        {totalReceitas.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </p>
                </div>
                <div className="bg-red-100 dark:bg-red-900/30 p-4 rounded-lg border border-red-200 dark:border-red-800">
                    <h3 className="text-red-800 dark:text-red-300 text-sm font-semibold uppercase tracking-wider">Despesas</h3>
                    <p className="text-2xl font-bold text-red-900 dark:text-white">
                        {totalDespesas.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </p>
                </div>
                <div className={`p-4 rounded-lg border ${saldo >= 0 ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800' : 'bg-orange-100 dark:bg-orange-900/30 border-orange-200 dark:border-orange-800'}`}>
                    <h3 className={`${saldo >= 0 ? 'text-blue-800 dark:text-blue-300' : 'text-orange-800 dark:text-orange-300'} text-sm font-semibold uppercase tracking-wider`}>Saldo do Período</h3>
                    <p className={`text-2xl font-bold ${saldo >= 0 ? 'text-blue-900 dark:text-white' : 'text-orange-900 dark:text-white'}`}>
                        {saldo.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </p>
                </div>
            </div>

            <div className="bg-white dark:bg-gray-800 shadow overflow-hidden rounded-lg">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead className="bg-gray-50 dark:bg-gray-900">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrição</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Categoria</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Valor</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                            {sortedGroupKeys.map(group => (
                                <>
                                    {/* Date Group Header */}
                                    <tr className="bg-indigo-50 dark:bg-indigo-900/30">
                                        <td colSpan={5} className="px-6 py-2 text-sm font-bold text-indigo-900 dark:text-indigo-100">
                                            {group}
                                        </td>
                                    </tr>
                                    {/* Transactions for this group */}
                                    {groupedTransactions[group].map(t => (
                                        <tr key={t.id} className="bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                                                {new Date(t.data).toLocaleDateString('pt-BR')}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                                                {t.descricao}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                                                {editingId === t.id ? (
                                                    <div className="flex gap-2">
                                                        <select
                                                            value={editCategory}
                                                            onChange={(e) => setEditCategory(e.target.value)}
                                                            className="bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded px-2 py-1 text-xs"
                                                        >
                                                            <option value="">Selecione...</option>
                                                            {categories.map(c => (
                                                                <option key={c.id} value={c.nome}>{c.nome}</option>
                                                            ))}
                                                        </select>
                                                        <button onClick={() => saveEdit(t.id)} className="text-green-600 hover:text-green-800">✅</button>
                                                        <button onClick={() => setEditingId(null)} className="text-gray-500 hover:text-gray-700">❌</button>
                                                    </div>
                                                ) : (
                                                    <div
                                                        onClick={() => startEdit(t)}
                                                        className={`cursor-pointer border-b border-dashed border-gray-300 hover:border-indigo-500 ${!t.categoria ? 'text-red-400 italic' : ''}`}
                                                    >
                                                        {t.categoria || "A Categorizar"}
                                                    </div>
                                                )}
                                            </td>
                                            <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${t.tipo === 'Despesa' ? 'text-red-600' : 'text-green-600'}`}>
                                                {Math.abs(t.valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                <button
                                                    onClick={() => handleDelete(t.id)}
                                                    className="text-red-600 hover:text-red-900 ml-4"
                                                >
                                                    Excluir
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </>
                            ))}

                            {sortedGroupKeys.length === 0 && !loading && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-10 text-center text-gray-500">
                                        {searchTerm ? "Nenhuma transação encontrada com esse filtro." : "Nenhuma transação cadastrada."}
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
