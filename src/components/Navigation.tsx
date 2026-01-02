"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navigation() {
    const pathname = usePathname();

    const isActive = (path: string) => {
        return pathname === path ? "bg-gray-900 text-white" : "text-gray-300 hover:bg-gray-700 hover:text-white";
    };

    return (
        <nav className="bg-gray-800">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="flex h-16 items-center justify-between">
                    <div className="flex items-center">
                        <div className="flex-shrink-0">
                            <span className="text-white font-bold text-xl">💰 Controle Financeiro</span>
                        </div>
                        <div className="hidden md:block">
                            <div className="ml-10 flex items-baseline space-x-4">
                                <Link
                                    href="/"
                                    className={`rounded-md px-3 py-2 text-sm font-medium ${isActive("/")}`}
                                >
                                    Dashboard
                                </Link>
                                <Link
                                    href="/upload"
                                    className={`rounded-md px-3 py-2 text-sm font-medium ${isActive("/upload")}`}
                                >
                                    Upload Extratos
                                </Link>
                                <Link
                                    href="/investimentos"
                                    className={`rounded-md px-3 py-2 text-sm font-medium ${isActive("/investimentos")}`}
                                >
                                    Investimentos
                                </Link>
                                <Link
                                    href="/categorias"
                                    className={`rounded-md px-3 py-2 text-sm font-medium ${isActive("/categorias")}`}
                                >
                                    Categorias
                                </Link>
                                <Link
                                    href="/transacoes"
                                    className={`rounded-md px-3 py-2 text-sm font-medium ${isActive("/transacoes")}`}
                                >
                                    Transações
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    );
}
