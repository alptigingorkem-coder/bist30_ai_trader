"use client";

import { TrendingUp } from "lucide-react";
import { useMarketStore } from "@/store/marketStore";
import { useEffect, useState } from "react";
import clsx from "clsx";

interface Signal {
    id: number;
    symbol: string;
    type: "AL" | "SAT";
    price: number;
    time: string;
}

export default function SignalFeed() {
    const { selectedTicker, tickers } = useMarketStore();
    const [signals, setSignals] = useState<Signal[]>([]);

    useEffect(() => {
        // Generate mock signals based on selected ticker
        // In real app, this would come from WS or API history
        const generateSignals = () => {
            const newSignals: Signal[] = [];
            const currentPrice = tickers.find(t => t.symbol === selectedTicker)?.price || 100;

            for (let i = 0; i < 5; i++) {
                // Deterministic variation
                const offset = i * 0.15;
                newSignals.push({
                    id: i,
                    symbol: selectedTicker,
                    type: (i % 2 === 0) ? "AL" : "SAT",
                    price: currentPrice - offset,
                    time: `10:${45 - i}:${12 + i}`
                });
            }
            return newSignals;
        };

        setSignals(generateSignals());
    }, [selectedTicker, tickers]);

    return (
        <div className="flex-1 p-4 rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden flex flex-col">
            <h3 className="text-sm font-bold text-slate-300 mb-3 flex items-center gap-2">
                <TrendingUp size={16} /> CANLI SİNYALLER
            </h3>
            <div className="space-y-2 overflow-y-auto max-h-[220px] scrollbar-thin scrollbar-thumb-slate-700 pr-1">
                {signals.map((signal) => (
                    <div
                        key={signal.id}
                        className="flex justify-between items-center text-xs p-2 rounded bg-slate-800/40 border border-slate-800/50 hover:bg-slate-800 transition-colors animate-in fade-in slide-in-from-right-2 duration-300"
                    >
                        <span className="font-bold text-white w-12">{signal.symbol}</span>
                        <span className={clsx("font-bold w-20 text-center rounded px-1", signal.type === "AL" ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400")}>
                            {signal.type} @ {signal.price.toFixed(2)}
                        </span>
                        <span className="text-slate-500 font-mono text-right flex-1">{signal.time}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
