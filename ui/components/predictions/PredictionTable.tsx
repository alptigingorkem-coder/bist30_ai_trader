"use client";

import clsx from "clsx";
import { TrendingUp, TrendingDown, Minus, Target } from "lucide-react";
import { useMarketStore } from "@/store/marketStore";

// Mock AI Predictions Data
// In real app, this comes from backend ML model
const PREDICTIONS = [
    { symbol: "THYAO", signal: "GÜÇLÜ AL", confidence: 92, target: 310.50, stop: 285.00, timeframe: "24 Saat" },
    { symbol: "GARAN", signal: "AL", confidence: 78, target: 82.40, stop: 75.50, timeframe: "4 Saat" },
    { symbol: "AKBNK", signal: "SAT", confidence: 65, target: 39.50, stop: 44.20, timeframe: "24 Saat" },
    { symbol: "ASELS", signal: "NÖTR", confidence: 45, target: 66.00, stop: 64.00, timeframe: "1 Saat" },
    { symbol: "TUPRS", signal: "GÜÇLÜ AL", confidence: 88, target: 185.00, stop: 165.00, timeframe: "48 Saat" },
    { symbol: "KCHOL", signal: "AL", confidence: 72, target: 195.00, stop: 178.00, timeframe: "24 Saat" },
    { symbol: "EREGL", signal: "SAT", confidence: 81, target: 42.00, stop: 48.00, timeframe: "24 Saat" },
    { symbol: "ISCTR", signal: "NÖTR", confidence: 55, target: 12.50, stop: 11.80, timeframe: "4 Saat" },
    { symbol: "SISE", signal: "AL", confidence: 76, target: 52.00, stop: 48.50, timeframe: "24 Saat" },
    { symbol: "BIMAS", signal: "GÜÇLÜ AL", confidence: 94, target: 510.00, stop: 480.00, timeframe: "1 Hafta" },
];

export default function PredictionTable() {
    const { setTicker } = useMarketStore();

    return (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 glass overflow-hidden flex flex-col h-full">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/30">
                <h3 className="font-display font-bold text-white flex items-center gap-2">
                    <Target size={18} className="text-cyan-400" />
                    AI TAHMİN MOTORU
                </h3>
                <div className="text-xs text-slate-500 font-mono">
                    MODEL: <span className="text-cyan-400">XGB-Hybrid-v2.1</span>
                </div>
            </div>

            <div className="overflow-y-auto flex-1 scrollbar-thin scrollbar-thumb-slate-800">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-slate-500 uppercase bg-slate-950/50 sticky top-0 backdrop-blur-md">
                        <tr>
                            <th className="px-6 py-3">Hisse</th>
                            <th className="px-6 py-3">Sinyal</th>
                            <th className="px-6 py-3">Güven</th>
                            <th className="px-6 py-3 text-right">Hedef Fiyat</th>
                            <th className="px-6 py-3 text-right">Stop Loss</th>
                            <th className="px-6 py-3 text-center">Vade</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                        {PREDICTIONS.map((item) => (
                            <tr
                                key={item.symbol}
                                onClick={() => setTicker(item.symbol)}
                                className="group hover:bg-slate-800/40 cursor-pointer transition-colors"
                            >
                                <td className="px-6 py-4 font-bold text-white group-hover:text-cyan-400 transition-colors">
                                    {item.symbol}
                                </td>
                                <td className="px-6 py-4">
                                    <div className={clsx("flex items-center gap-2 font-bold text-xs px-2 py-1 w-fit rounded-lg",
                                        item.signal.includes("AL") ? "bg-green-500/10 text-green-400 border border-green-500/20" :
                                            item.signal.includes("SAT") ? "bg-red-500/10 text-red-400 border border-red-500/20" :
                                                "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                                    )}>
                                        {item.signal.includes("AL") ? <TrendingUp size={14} /> :
                                            item.signal.includes("SAT") ? <TrendingDown size={14} /> :
                                                <Minus size={14} />}
                                        {item.signal}
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                            <div
                                                className={clsx("h-full rounded-full",
                                                    item.confidence > 80 ? "bg-green-500" :
                                                        item.confidence > 60 ? "bg-cyan-500" : "bg-yellow-500"
                                                )}
                                                style={{ width: `${item.confidence}%` }}
                                            ></div>
                                        </div>
                                        <span className="text-xs font-mono text-slate-400">{item.confidence}%</span>
                                    </div>
                                </td>
                                <td className="px-6 py-4 text-right font-mono font-bold text-green-400">
                                    {item.target.toFixed(2)}
                                </td>
                                <td className="px-6 py-4 text-right font-mono text-red-400">
                                    {item.stop.toFixed(2)}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <span className="text-xs font-mono text-slate-500 border border-slate-700 rounded px-1.5 py-0.5">
                                        {item.timeframe}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

