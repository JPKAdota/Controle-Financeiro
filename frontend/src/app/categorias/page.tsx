"use client";

import { useEffect, useState } from "react";

interface Category {
    id: string;
    nome: string;
    tipo: string;
}

export default function CategoriesPage() {
    const [categories, setCategories] = useState<Category[]>([]);
    const [formData, setFormData] = useState({ nome: "", tipo: "Despesa" });
    const [editingId, setEditingId] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchCategories();
    }, []);

    const fetchCategories = async () => {
        try {
            const res = await fetch("/api/categories");
            if (res.ok) {
                const data = await res.json();
                setCategories(data || []);
            }
        } catch (error) {
            console.error("Erro ao buscar categorias", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            if (editingId) {
                // Update
                await fetch(`/api/categories/${editingId}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(formData),
                });
            } else {
                // Create
                await fetch("/api/categories", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(formData),
                });
            }

            setFormData({ nome: "", tipo: "Despesa" });
            setEditingId(null);
            fetchCategories();
        } catch (error) {
            alert("Erro ao salvar categoria");
        }
    };

    const handleEdit = (cat: Category) => {
        setFormData({ nome: cat.nome, tipo: cat.tipo });
        setEditingId(cat.id);
    };

    const handleCancelEdit = () => {
        setFormData({ nome: "", tipo: "Despesa" });
        setEditingId(null);
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Tem certeza?")) return;
        try {
            await fetch(`/api/categories/${id}`, { method: "DELETE" });
            fetchCategories();
        } catch (error) {
            alert("Erro ao deletar");
        }
    };

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Gerenciar Categorias</h1>

            {/* Form */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <h2 className="text-lg font-medium mb-4 text-gray-900 dark:text-gray-100">
                    {editingId ? "Editar Categoria" : "Nova Categoria"}
                </h2>
                <form onSubmit={handleSubmit} className="flex gap-4 items-end flex-wrap">
                    <div className="flex-1 min-w-[200px]">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Nome</label>
                        <input
                            type="text"
                            value={formData.nome}
                            onChange={(e) => setFormData({ ...formData, nome: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
                            required
                        />
                    </div>
                    <div className="w-[200px]">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Tipo</label>
                        <select
                            value={formData.tipo}
                            onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2"
                        >
                            <option value="Despesa">Despesa</option>
                            <option value="Receita">Receita</option>
                            <option value="Investimento">Investimento</option>
                        </select>
                    </div>
                    <div className="flex gap-2">
                        <button
                            type="submit"
                            className={`text-white px-4 py-2 rounded-md transition ${editingId ? 'bg-orange-600 hover:bg-orange-700' : 'bg-indigo-600 hover:bg-indigo-700'}`}
                        >
                            {editingId ? "Atualizar" : "Adicionar"}
                        </button>
                        {editingId && (
                            <button
                                type="button"
                                onClick={handleCancelEdit}
                                className="bg-gray-500 text-white px-4 py-2 rounded-md hover:bg-gray-600 transition"
                            >
                                Cancelar
                            </button>
                        )}
                    </div>
                </form>
            </div>

            {/* List */}
            <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                    {categories.map((cat) => (
                        <li key={cat.id} className="px-6 py-4 flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-indigo-600 truncate">{cat.nome}</p>
                                <p className="text-sm text-gray-500">{cat.tipo}</p>
                            </div>
                            <div className="flex gap-4">
                                <button
                                    onClick={() => handleEdit(cat)}
                                    className="text-orange-600 hover:text-orange-900 text-sm font-medium"
                                >
                                    Editar
                                </button>
                                <button
                                    onClick={() => handleDelete(cat.id)}
                                    className="text-red-600 hover:text-red-900 text-sm font-medium"
                                >
                                    Excluir
                                </button>
                            </div>
                        </li>
                    ))}
                    {categories.length === 0 && !loading && (
                        <li className="px-6 py-4 text-center text-gray-500">Nenhuma categoria encontrada.</li>
                    )}
                </ul>
            </div>
        </div>
    );
}
