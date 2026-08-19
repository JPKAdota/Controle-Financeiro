"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setLoading(true);
        setError("");

        const { error: authError } = await supabase.auth.signInWithPassword({ email, password });

        if (authError) {
            setError(authError.message || "Não foi possível entrar.");
            setLoading(false);
            return;
        }

        router.replace("/");
    };

    return (
        <main className="min-h-screen flex items-center justify-center bg-gray-900 px-4">
            <form onSubmit={handleSubmit} className="w-full max-w-md space-y-5 rounded-lg bg-gray-800 p-8 shadow-xl">
                <div>
                    <h1 className="text-2xl font-bold text-white">Controle Financeiro</h1>
                    <p className="mt-1 text-sm text-gray-400">Entre para acessar suas finanças.</p>
                </div>

                <label className="block text-sm text-gray-300">
                    E-mail
                    <input
                        type="email"
                        value={email}
                        onChange={(event) => setEmail(event.target.value)}
                        required
                        autoComplete="email"
                        className="mt-1 w-full rounded-md border border-gray-600 bg-gray-700 p-2 text-white"
                    />
                </label>

                <label className="block text-sm text-gray-300">
                    Senha
                    <input
                        type="password"
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        required
                        autoComplete="current-password"
                        className="mt-1 w-full rounded-md border border-gray-600 bg-gray-700 p-2 text-white"
                    />
                </label>

                {error && <p className="text-sm text-red-400">{error}</p>}

                <button
                    type="submit"
                    disabled={loading}
                    className="w-full rounded-md bg-emerald-600 px-4 py-2 font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
                >
                    {loading ? "Entrando..." : "Entrar"}
                </button>
            </form>
        </main>
    );
}