"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import {
    MessageSquare,
    BarChart3,
    Calculator,
    Send,
    RefreshCw,
    Sparkles,
    TrendingUp,
    DollarSign,
    Percent,
    Clock,
    ArrowRight,
} from "lucide-react";
import {
    AreaChart,
    Area,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from "recharts";
import ChatMessage from "@/components/ChatMessage";
import MarketCard from "@/components/MarketCard";

// ============ TYPES ============

type Tab = "chat" | "mercado" | "simulador";

interface Message {
    role: "user" | "assistant";
    content: string;
}

interface Quote {
    symbol: string;
    shortName: string;
    longName: string;
    price: number;
    change: number;
    changePercent: number;
}

interface Indicator {
    name: string;
    value: number;
    change: number;
    changePercent: number;
    type: string;
}

interface HistoryPoint {
    date: number;
    close: number;
}

interface SimResult {
    parametros: {
        aporteInicial: number;
        aporteMensal: number;
        taxaAnual: number;
        taxaEfetivaAnual: number;
        taxaMensal: number;
        meses: number;
        indexador: string;
    };
    resultado: {
        valorFinal: number;
        totalInvestido: number;
        rendimentoTotal: number;
        rentabilidadePct: number;
    };
    serie: {
        mes: number;
        saldo: number;
        totalInvestido: number;
        rendimentoMes: number;
        rendimentoAcumulado: number;
    }[];
}

// ============ HELPERS ============

const formatMoney = (val: number) =>
    val.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: "chat", label: "Assistente IA", icon: MessageSquare },
    { id: "mercado", label: "Mercado", icon: BarChart3 },
    { id: "simulador", label: "Simulador", icon: Calculator },
];

// ============ MAIN PAGE ============

export default function AgentePage() {
    const [activeTab, setActiveTab] = useState<Tab>("chat");

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400">
                        🤖 Agente de Investimentos
                    </h1>
                    <p className="text-gray-400 text-sm mt-1">
                        IA + Mercado + Simulador — tudo em um lugar
                    </p>
                </div>
            </div>

            {/* Tab Bar */}
            <div className="flex gap-1 bg-gray-800/50 p-1 rounded-xl border border-gray-700/50">
                {TABS.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                                isActive
                                    ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-500/20"
                                    : "text-gray-400 hover:text-white hover:bg-gray-700/50"
                            }`}
                        >
                            <Icon className="w-4 h-4" />
                            <span className="hidden sm:inline">{tab.label}</span>
                        </button>
                    );
                })}
            </div>

            {/* Content */}
            <div className="min-h-[600px]">
                {activeTab === "chat" && <ChatTab />}
                {activeTab === "mercado" && <MercadoTab />}
                {activeTab === "simulador" && <SimuladorTab />}
            </div>
        </div>
    );
}

// ============ TAB: CHAT ============

function ChatTab() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, []);

    useEffect(() => {
        // Carregar sugestões
        fetch("/api/agent/suggestions")
            .then((r) => r.json())
            .then((data) => setSuggestions(data.suggestions || []))
            .catch(() => {});
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading, scrollToBottom]);

    const sendMessage = async (text?: string) => {
        const messageText = text || input.trim();
        if (!messageText || isLoading) return;

        const userMessage: Message = { role: "user", content: messageText };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const response = await fetch("/api/agent/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: messageText,
                    history: messages.slice(-10),
                }),
            });

            const data = await response.json();
            const assistantMessage: Message = {
                role: "assistant",
                content: data.response || "Erro ao processar resposta.",
            };
            setMessages((prev) => [...prev, assistantMessage]);
        } catch {
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: "❌ Erro de conexão. Verifique se o backend está rodando.",
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className="bg-gray-800/30 border border-gray-700/50 rounded-2xl overflow-hidden flex flex-col h-[650px]">
            {/* Disclaimer bar */}
            <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2">
                <p className="text-xs text-amber-300/80 text-center">
                    ⚠️ Assistente educacional — NÃO constitui recomendação de investimento
                </p>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center">
                        <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-emerald-500/20">
                            <Sparkles className="w-8 h-8 text-white" />
                        </div>
                        <h3 className="text-lg font-semibold text-white mb-2">
                            Olá! Sou seu Assistente de Investimentos
                        </h3>
                        <p className="text-gray-400 text-sm max-w-md mb-6">
                            Posso analisar suas finanças, explicar investimentos,
                            comparar opções e ajudar no seu planejamento financeiro.
                        </p>

                        {/* Suggestions */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
                            {suggestions.slice(0, 4).map((q, i) => (
                                <button
                                    key={i}
                                    onClick={() => sendMessage(q)}
                                    className="text-left px-3 py-2.5 bg-gray-700/50 hover:bg-gray-700 border border-gray-600/50 rounded-xl text-sm text-gray-300 hover:text-white transition-all duration-200 flex items-center gap-2"
                                >
                                    <ArrowRight className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                                    <span className="line-clamp-2">{q}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    messages.map((msg, i) => (
                        <ChatMessage key={i} role={msg.role} content={msg.content} />
                    ))
                )}

                {isLoading && (
                    <ChatMessage role="assistant" content="" isLoading />
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-gray-700/50 p-4 bg-gray-800/50">
                <div className="flex gap-2">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Pergunte sobre investimentos..."
                        rows={1}
                        className="flex-1 bg-gray-700/50 border border-gray-600/50 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50"
                    />
                    <button
                        onClick={() => sendMessage()}
                        disabled={isLoading || !input.trim()}
                        className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-40 disabled:cursor-not-allowed text-white px-4 py-3 rounded-xl transition-all duration-200 shadow-lg shadow-emerald-500/20"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    );
}

// ============ TAB: MERCADO ============

function MercadoTab() {
    const [activeSubTab, setActiveSubTab] = useState<"stocks" | "fiis" | "crypto" | "search">("stocks");
    const [quotes, setQuotes] = useState<Quote[]>([]);
    const [fiis, setFiis] = useState<Quote[]>([]);
    const [crypto, setCrypto] = useState<Quote[]>([]);
    const [customQuotes, setCustomQuotes] = useState<Quote[]>([]);
    
    const [indicators, setIndicators] = useState<Record<string, Indicator>>({});
    const [history, setHistory] = useState<HistoryPoint[]>([]);
    const [selectedSymbol, setSelectedSymbol] = useState("PETR4");
    const [historyRange, setHistoryRange] = useState("1mo");
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<string>("");

    // Search state
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState<{ symbol: string; name: string; type: string }[]>([]);
    const [searching, setSearching] = useState(false);

    const fetchMarketData = useCallback(async () => {
        setLoading(true);
        try {
            const [stocksRes, fiisRes, cryptoRes, indicatorsRes] = await Promise.all([
                fetch("/api/market/quotes?symbols=PETR4,VALE3,ITUB4,MGLU3"),
                fetch("/api/market/quotes?symbols=MXRF11,HGLG11,XPML11,KNRI11"),
                fetch("/api/market/crypto?symbols=BTC,ETH,SOL"),
                fetch("/api/market/indicators"),
            ]);

            const stocksData = await stocksRes.json();
            const fiisData = await fiisRes.json();
            const cryptoData = await cryptoRes.json();
            const indicatorsData = await indicatorsRes.json();

            setQuotes(stocksData.quotes || []);
            setFiis(fiisData.quotes || []);
            
            // Map crypto coins to the Quote interface structure
            const mappedCrypto = (cryptoData.coins || []).map((c: any) => ({
                symbol: c.symbol,
                shortName: c.name,
                longName: c.name,
                price: c.price,
                change: c.change,
                changePercent: c.changePercent
            }));
            setCrypto(mappedCrypto);

            setIndicators(indicatorsData.indicators || {});
            setLastUpdate(
                new Date().toLocaleTimeString("pt-BR", {
                    hour: "2-digit",
                    minute: "2-digit",
                })
            );
        } catch {
            // silently fail
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchHistory = useCallback(async () => {
        try {
            const res = await fetch(
                `/api/market/history/${selectedSymbol}?range=${historyRange}`
            );
            const data = await res.json();
            setHistory(data.history || []);
        } catch {
            setHistory([]);
        }
    }, [selectedSymbol, historyRange]);

    useEffect(() => {
        fetchMarketData();
        const interval = setInterval(fetchMarketData, 5 * 60 * 1000);
        return () => clearInterval(interval);
    }, [fetchMarketData]);

    useEffect(() => {
        fetchHistory();
    }, [fetchHistory]);

    // Handle ticker search
    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;
        setSearching(true);
        try {
            const res = await fetch(`/api/market/tickers?search=${searchQuery}`);
            const data = await res.json();
            setSearchResults(data.tickers || []);
        } catch {
            setSearchResults([]);
        } finally {
            setSearching(false);
        }
    };

    // Add searched ticker to customized watch list
    const selectSearchedTicker = async (symbol: string) => {
        setLoading(true);
        try {
            // Verify if it is a crypto symbol or standard stock/FII
            const isCrypto = searchResults.find(t => t.symbol === symbol)?.type === "crypto";
            let res;
            if (isCrypto) {
                res = await fetch(`/api/market/crypto?symbols=${symbol}`);
                const data = await res.json();
                if (data.coins && data.coins.length > 0) {
                    const c = data.coins[0];
                    const quote: Quote = {
                        symbol: c.symbol,
                        shortName: c.name,
                        longName: c.name,
                        price: c.price,
                        change: c.change,
                        changePercent: c.changePercent
                    };
                    setCustomQuotes(prev => {
                        if (prev.some(q => q.symbol === quote.symbol)) return prev;
                        return [quote, ...prev];
                    });
                    setSelectedSymbol(quote.symbol);
                }
            } else {
                res = await fetch(`/api/market/quotes?symbols=${symbol}`);
                const data = await res.json();
                if (data.quotes && data.quotes.length > 0) {
                    const quote = data.quotes[0];
                    setCustomQuotes(prev => {
                        if (prev.some(q => q.symbol === quote.symbol)) return prev;
                        return [quote, ...prev];
                    });
                    setSelectedSymbol(quote.symbol);
                }
            }
        } catch {
            alert("Erro ao buscar detalhes do ativo.");
        } finally {
            setLoading(false);
            setSearchQuery("");
            setSearchResults([]);
        }
    };

    const historyChartData = history.map((p) => ({
        date: new Date(p.date * 1000).toLocaleDateString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
        }),
        preco: p.close,
    }));

    // Decide which quotes list to show
    const getActiveQuotes = () => {
        switch (activeSubTab) {
            case "fiis":
                return fiis;
            case "crypto":
                return crypto;
            case "search":
                return customQuotes;
            case "stocks":
            default:
                return quotes;
        }
    };

    const activeQuotes = getActiveQuotes();

    return (
        <div className="space-y-6">
            {/* Controls */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Clock className="w-4 h-4" />
                    {lastUpdate ? `Atualizado às ${lastUpdate}` : "Carregando..."}
                </div>
                <button
                    onClick={fetchMarketData}
                    disabled={loading}
                    className="flex items-center gap-2 px-3 py-1.5 bg-gray-700/50 hover:bg-gray-700 border border-gray-600/50 rounded-lg text-sm text-gray-300 hover:text-white transition-all"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                    Atualizar
                </button>
            </div>

            {/* Indicators Row */}
            <div>
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                    Indicadores Econômicos
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                    {Object.entries(indicators).map(([key, ind]) => (
                        <MarketCard
                            key={key}
                            symbol={key.toUpperCase()}
                            name={ind.name}
                            price={ind.value}
                            change={ind.change}
                            changePercent={ind.changePercent}
                            type={ind.type as "stock" | "index" | "currency" | "rate"}
                        />
                    ))}
                    {Object.keys(indicators).length === 0 && !loading && (
                        <p className="text-gray-500 text-sm col-span-full">
                            Nenhum indicador disponível. Verifique a conexão com a API.
                        </p>
                    )}
                </div>
            </div>

            {/* Sub-tabs Selection */}
            <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-4 space-y-4">
                <div className="flex flex-wrap gap-2 border-b border-gray-700/50 pb-3">
                    {[
                        { id: "stocks", label: "Ações" },
                        { id: "fiis", label: "Fundos Imobiliários (FIIs)" },
                        { id: "crypto", label: "Criptomoedas" },
                        { id: "search", label: "Buscar Ativo B3" }
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveSubTab(tab.id as any)}
                            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                                activeSubTab === tab.id
                                    ? "bg-emerald-600 text-white"
                                    : "bg-gray-750 text-gray-400 hover:text-white hover:bg-gray-700"
                            }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Search Area */}
                {activeSubTab === "search" && (
                    <div className="space-y-3">
                        <form onSubmit={handleSearch} className="flex gap-2">
                            <input
                                type="text"
                                placeholder="Digite o código ou nome (Ex: WEGE3, ALZR11, BTC)..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="flex-1 bg-gray-700/50 border border-gray-650 rounded-lg px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            />
                            <button
                                type="submit"
                                disabled={searching}
                                className="bg-emerald-600 text-white px-4 py-2 rounded-lg text-xs font-bold hover:bg-emerald-500 transition-all"
                            >
                                {searching ? "Buscando..." : "Pesquisar"}
                            </button>
                        </form>

                        {/* Search Results */}
                        {searchResults.length > 0 && (
                            <div className="bg-gray-850 border border-gray-700 rounded-lg max-h-48 overflow-y-auto divide-y divide-gray-700/50">
                                {searchResults.map((t) => (
                                    <button
                                        key={t.symbol}
                                        onClick={() => selectSearchedTicker(t.symbol)}
                                        className="w-full text-left px-4 py-2.5 hover:bg-gray-700/50 text-xs flex justify-between items-center transition-all"
                                    >
                                        <div>
                                            <span className="font-bold text-white mr-2">{t.symbol}</span>
                                            <span className="text-gray-400">{t.name}</span>
                                        </div>
                                        <span className="text-[10px] bg-gray-750 px-2 py-0.5 rounded text-gray-400 uppercase font-semibold">
                                            {t.type}
                                        </span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Display Grid of Current Cards */}
                <div>
                    {activeQuotes.length > 0 ? (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            {activeQuotes.map((q) => (
                                <button
                                    key={q.symbol}
                                    onClick={() => setSelectedSymbol(q.symbol)}
                                    className={`text-left rounded-xl transition-all ${
                                        selectedSymbol === q.symbol ? "ring-2 ring-emerald-500" : ""
                                    }`}
                                >
                                    <MarketCard
                                        symbol={q.symbol}
                                        name={q.shortName || q.longName}
                                        price={q.price}
                                        change={q.change}
                                        changePercent={q.changePercent}
                                        type="stock"
                                    />
                                </button>
                            ))}
                        </div>
                    ) : (
                        <p className="text-gray-500 text-xs text-center py-4">
                            {activeSubTab === "search" 
                                ? "Use a barra de pesquisa acima para adicionar ativos a este painel personalizado!"
                                : "Carregando cotações..."}
                        </p>
                    )}
                </div>
            </div>

            {/* History Chart */}
            <div className="bg-gray-800/30 border border-gray-700/50 rounded-2xl p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                    <h2 className="text-lg font-semibold text-white">
                        📈 Histórico — {selectedSymbol}
                    </h2>
                    <div className="flex gap-1 bg-gray-700/50 p-1 rounded-lg">
                        {[
                            { label: "1S", value: "5d" },
                            { label: "1M", value: "1mo" },
                            { label: "3M", value: "3mo" },
                            { label: "6M", value: "6mo" },
                            { label: "1A", value: "1y" },
                        ].map((r) => (
                            <button
                                key={r.value}
                                onClick={() => setHistoryRange(r.value)}
                                className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                                    historyRange === r.value
                                        ? "bg-emerald-600 text-white"
                                        : "text-gray-400 hover:text-white"
                                }`}
                            >
                                {r.label}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="h-72">
                    {historyChartData.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={historyChartData}>
                                <defs>
                                    <linearGradient id="colorPreco" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                <XAxis dataKey="date" stroke="#6b7280" tick={{ fontSize: 11 }} />
                                <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: "#1f2937",
                                        border: "1px solid #374151",
                                        borderRadius: "8px",
                                        color: "#fff",
                                    }}
                                    formatter={(value: number | undefined) => [formatMoney(value ?? 0), "Preço"]}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="preco"
                                    stroke="#10b981"
                                    strokeWidth={2}
                                    fillOpacity={1}
                                    fill="url(#colorPreco)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                            {loading ? "Carregando histórico..." : "Nenhum dado histórico disponível"}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// ============ TAB: SIMULADOR ============

function SimuladorTab() {
    const [form, setForm] = useState({
        aporte_inicial: "1000",
        aporte_mensal: "500",
        taxa_anual: "12",
        meses: "60",
        indexador: "pre",
        taxa_indexador: "0",
    });
    const [result, setResult] = useState<SimResult | null>(null);
    const [loading, setLoading] = useState(false);

    const handleSimulate = async () => {
        setLoading(true);
        try {
            const res = await fetch("/api/agent/simulate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    aporte_inicial: parseFloat(form.aporte_inicial) || 0,
                    aporte_mensal: parseFloat(form.aporte_mensal) || 0,
                    taxa_anual: parseFloat(form.taxa_anual) || 0,
                    meses: parseInt(form.meses) || 12,
                    indexador: form.indexador,
                    taxa_indexador: parseFloat(form.taxa_indexador) || 0,
                }),
            });

            const data = await res.json();
            if (data.serie) {
                setResult(data);
            }
        } catch {
            alert("Erro ao simular. Verifique o backend.");
        } finally {
            setLoading(false);
        }
    };

    const indexadorLabels: Record<string, string> = {
        pre: "Pré-fixado (% a.a.)",
        cdi: "% do CDI",
        ipca: "IPCA + (% a.a.)",
    };

    // Amostragem para gráfico (mostrar no máximo 60 pontos)
    const chartData = result
        ? result.serie.filter((_, i) => {
              if (result.serie.length <= 60) return true;
              const step = Math.ceil(result.serie.length / 60);
              return i % step === 0 || i === result.serie.length - 1;
          })
        : [];

    return (
        <div className="space-y-6">
            {/* Form */}
            <div className="bg-gray-800/30 border border-gray-700/50 rounded-2xl p-6">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Calculator className="w-5 h-5 text-emerald-400" />
                    Simulador de Investimentos
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Aporte Inicial */}
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1.5">
                            <DollarSign className="w-3.5 h-3.5 inline mr-1" />
                            Aporte Inicial (R$)
                        </label>
                        <input
                            type="number"
                            value={form.aporte_inicial}
                            onChange={(e) => setForm({ ...form, aporte_inicial: e.target.value })}
                            className="w-full bg-gray-700/50 border border-gray-600/50 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                            min="0"
                            step="100"
                        />
                    </div>

                    {/* Aporte Mensal */}
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1.5">
                            <DollarSign className="w-3.5 h-3.5 inline mr-1" />
                            Aporte Mensal (R$)
                        </label>
                        <input
                            type="number"
                            value={form.aporte_mensal}
                            onChange={(e) => setForm({ ...form, aporte_mensal: e.target.value })}
                            className="w-full bg-gray-700/50 border border-gray-600/50 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                            min="0"
                            step="50"
                        />
                    </div>

                    {/* Indexador */}
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1.5">
                            <TrendingUp className="w-3.5 h-3.5 inline mr-1" />
                            Indexador
                        </label>
                        <select
                            value={form.indexador}
                            onChange={(e) => setForm({ ...form, indexador: e.target.value })}
                            className="w-full bg-gray-700/50 border border-gray-600/50 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                        >
                            <option value="pre">Pré-fixado</option>
                            <option value="cdi">% do CDI</option>
                            <option value="ipca">IPCA +</option>
                        </select>
                    </div>

                    {/* Taxa */}
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1.5">
                            <Percent className="w-3.5 h-3.5 inline mr-1" />
                            {indexadorLabels[form.indexador] || "Taxa (% a.a.)"}
                        </label>
                        <input
                            type="number"
                            value={form.taxa_anual}
                            onChange={(e) => setForm({ ...form, taxa_anual: e.target.value })}
                            className="w-full bg-gray-700/50 border border-gray-600/50 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                            step="0.25"
                        />
                    </div>

                    {/* Taxa Indexador (se CDI ou IPCA) */}
                    {form.indexador !== "pre" && (
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-1.5">
                                <Percent className="w-3.5 h-3.5 inline mr-1" />
                                {form.indexador === "cdi" ? "CDI atual (% a.a.)" : "IPCA atual (% a.a.)"}
                            </label>
                            <input
                                type="number"
                                value={form.taxa_indexador}
                                onChange={(e) => setForm({ ...form, taxa_indexador: e.target.value })}
                                className="w-full bg-gray-700/50 border border-gray-600/50 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                                step="0.25"
                            />
                        </div>
                    )}

                    {/* Prazo */}
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1.5">
                            <Clock className="w-3.5 h-3.5 inline mr-1" />
                            Prazo (meses)
                        </label>
                        <input
                            type="number"
                            value={form.meses}
                            onChange={(e) => setForm({ ...form, meses: e.target.value })}
                            className="w-full bg-gray-700/50 border border-gray-600/50 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                            min="1"
                            max="600"
                        />
                    </div>
                </div>

                <button
                    onClick={handleSimulate}
                    disabled={loading}
                    className="mt-6 w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-all duration-200 shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
                >
                    {loading ? (
                        <RefreshCw className="w-5 h-5 animate-spin" />
                    ) : (
                        <>
                            <Calculator className="w-5 h-5" />
                            Simular Investimento
                        </>
                    )}
                </button>
            </div>

            {/* Results */}
            {result && (
                <>
                    {/* Summary Cards */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-4">
                            <p className="text-xs text-gray-400 mb-1">Valor Final</p>
                            <p className="text-lg font-bold text-emerald-400">
                                {formatMoney(result.resultado.valorFinal)}
                            </p>
                        </div>
                        <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-4">
                            <p className="text-xs text-gray-400 mb-1">Total Investido</p>
                            <p className="text-lg font-bold text-blue-400">
                                {formatMoney(result.resultado.totalInvestido)}
                            </p>
                        </div>
                        <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-4">
                            <p className="text-xs text-gray-400 mb-1">Rendimento</p>
                            <p className="text-lg font-bold text-yellow-400">
                                {formatMoney(result.resultado.rendimentoTotal)}
                            </p>
                        </div>
                        <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-4">
                            <p className="text-xs text-gray-400 mb-1">Rentabilidade</p>
                            <p className="text-lg font-bold text-purple-400">
                                {result.resultado.rentabilidadePct}%
                            </p>
                        </div>
                    </div>

                    {/* Chart */}
                    <div className="bg-gray-800/30 border border-gray-700/50 rounded-2xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4">
                            📈 Projeção de Patrimônio
                        </h3>
                        <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData}>
                                    <defs>
                                        <linearGradient id="colorSaldo" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                                            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                        </linearGradient>
                                        <linearGradient id="colorInvestido" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                    <XAxis
                                        dataKey="mes"
                                        stroke="#6b7280"
                                        tick={{ fontSize: 11 }}
                                        label={{
                                            value: "Meses",
                                            position: "insideBottom",
                                            offset: -5,
                                            style: { fill: "#6b7280", fontSize: 11 },
                                        }}
                                    />
                                    <YAxis
                                        stroke="#6b7280"
                                        tick={{ fontSize: 11 }}
                                        tickFormatter={(v) =>
                                            `R$${(v / 1000).toFixed(0)}k`
                                        }
                                    />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: "#1f2937",
                                            border: "1px solid #374151",
                                            borderRadius: "8px",
                                            color: "#fff",
                                        }}
                                        formatter={(value: number | undefined, name?: string) => [
                                            formatMoney(value ?? 0),
                                            name === "saldo"
                                                ? "Saldo Total"
                                                : "Total Investido",
                                        ]}
                                        labelFormatter={(label) => `Mês ${label}`}
                                    />
                                    <Legend
                                        formatter={(value: string) =>
                                            value === "saldo"
                                                ? "Saldo Total"
                                                : "Total Investido"
                                        }
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="totalInvestido"
                                        stroke="#3b82f6"
                                        strokeWidth={2}
                                        fillOpacity={1}
                                        fill="url(#colorInvestido)"
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="saldo"
                                        stroke="#10b981"
                                        strokeWidth={2}
                                        fillOpacity={1}
                                        fill="url(#colorSaldo)"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Parâmetros usados */}
                        <div className="mt-4 pt-4 border-t border-gray-700/50">
                            <p className="text-xs text-gray-500">
                                Parâmetros: {form.indexador === "pre" ? "Pré-fixado" : form.indexador === "cdi" ? "% CDI" : "IPCA+"}{" "}
                                {result.parametros.taxaEfetivaAnual}% a.a. | Taxa mensal: {result.parametros.taxaMensal}% | {result.parametros.meses} meses
                            </p>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
