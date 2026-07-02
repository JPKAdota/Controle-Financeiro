"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";

interface MarketCardProps {
    symbol: string;
    name: string;
    price: number;
    change: number;
    changePercent: number;
    type?: "stock" | "index" | "currency" | "rate";
}

export default function MarketCard({
    symbol,
    name,
    price,
    change,
    changePercent,
    type = "stock",
}: MarketCardProps) {
    const isPositive = change > 0;
    const isNeutral = change === 0;
    const isRate = type === "rate";

    const formatValue = (val: number) => {
        if (isRate) return `${val.toFixed(2)}%`;
        return val.toLocaleString("pt-BR", {
            style: "currency",
            currency: "BRL",
            minimumFractionDigits: 2,
        });
    };

    const formatChange = (val: number) => {
        const sign = val > 0 ? "+" : "";
        return `${sign}${val.toFixed(2)}`;
    };

    const TrendIcon = isNeutral ? Minus : isPositive ? TrendingUp : TrendingDown;
    const trendColor = isNeutral
        ? "text-gray-400"
        : isPositive
        ? "text-emerald-400"
        : "text-red-400";
    const trendBg = isNeutral
        ? "bg-gray-500/10"
        : isPositive
        ? "bg-emerald-500/10"
        : "bg-red-500/10";
    const borderColor = isNeutral
        ? "border-gray-700"
        : isPositive
        ? "border-emerald-500/30"
        : "border-red-500/30";

    return (
        <div
            className={`relative overflow-hidden bg-gray-800/60 backdrop-blur-sm border ${borderColor} rounded-xl p-4 hover:bg-gray-800/80 transition-all duration-300 group`}
        >
            {/* Glow effect on hover */}
            <div
                className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${
                    isPositive
                        ? "bg-gradient-to-br from-emerald-500/5 to-transparent"
                        : isNeutral
                        ? ""
                        : "bg-gradient-to-br from-red-500/5 to-transparent"
                }`}
            />

            <div className="relative z-10">
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                    <div>
                        <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                            {symbol}
                        </span>
                        <p className="text-sm text-gray-300 truncate max-w-[140px]" title={name}>
                            {name}
                        </p>
                    </div>
                    <div className={`p-2 rounded-lg ${trendBg}`}>
                        <TrendIcon className={`w-4 h-4 ${trendColor}`} />
                    </div>
                </div>

                {/* Price */}
                <p className="text-xl font-bold text-white mb-1">
                    {formatValue(price)}
                </p>

                {/* Change */}
                {!isRate && (
                    <div className="flex items-center gap-2">
                        <span className={`text-sm font-medium ${trendColor}`}>
                            {formatChange(change)}
                        </span>
                        <span
                            className={`text-xs px-1.5 py-0.5 rounded-md font-medium ${trendBg} ${trendColor}`}
                        >
                            {changePercent > 0 ? "+" : ""}
                            {changePercent.toFixed(2)}%
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}
