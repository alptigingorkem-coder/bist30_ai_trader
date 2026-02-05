"use client";

import { useMarketStore } from "@/store/marketStore";
import { Activity } from "lucide-react";
import clsx from "clsx";

export default function AiConfidenceWidget() {
    const { selectedTicker, tickers } = useMarketStore();
    const currentTickerData = tickers.find((t) => t.symbol === selectedTicker);

    // Mock AI Logic based on Ticker Name & Price Movement
    // In real app, this comes from backend API
    const getAiPrediction = (symbol: string) => {
        // Deterministic mock based on symbol
        const seed = symbol.charCodeAt(0) + symbol.charCodeAt(symbol.length - 1);

        const confidence = 60 + (seed % 35); // 60-95%
        const sentiment = confidence > 80 ? "GÜÇLÜ AL" : confidence > 70 ? "AL" : "NÖTR";
        const color = confidence > 80 ? "green" : confidence > 70 ? "cyan" : "yellow";

        // Predicted Range Mock
        const currentPrice = currentTickerData?.price || 100;
        const lowRange = (currentPrice * 0.98).toFixed(2);
        const highRange = (currentPrice * 1.02).toFixed(2);

        return { confidence, sentiment, color, lowRange, highRange };
    };

    const { confidence, sentiment, color, lowRange, highRange } = getAiPrediction(selectedTicker);

    return (
        <div className="flex-1 p-6 rounded-2xl border border-slate-800 bg-slate-900/60 glass flex flex-col justify-between">
            <div className="flex items-center gap-2 mb-4 text-cyan-400 font-display font-bold">
                <Activity size={18} /> AI MODEL GÜVENİ • {selectedTicker}
            </div>

            <div className="flex flex-col items-center justify-center h-[160px] relative">
                <div className="text-5xl font-mono font-bold text-white mb-2">{confidence}%</div>
                <div
                    className={clsx(
                        "text-sm font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700",
                        color === "green" ? "text-green-400" : color === "cyan" ? "text-cyan-400" : "text-yellow-400"
                    )}
                >
                    {sentiment}
                </div>

                {/* Circular Indicator BG */}
                <svg className="absolute w-full h-full pointer-events-none">
                    <circle cx="50%" cy="50%" r="65" stroke="#1e293b" strokeWidth="8" fill="none" />
                    {/* Dynamic Stroke based on confidence */}
                    <circle
                        cx="50%" cy="50%" r="65"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="none"
                        strokeDasharray={`${(confidence / 100) * 408} 408`}
                        className={clsx(
                            "transition-all duration-1000 ease-out origin-center -rotate-90",
                            color === "green" ? "text-green-500/30" : color === "cyan" ? "text-cyan-500/30" : "text-yellow-500/30"
                        )}
                    />
                </svg>
            </div>

            <div className="space-y-3 mt-4">
                <div className="flex justify-between text-sm border-b border-slate-800 pb-2">
                    <span className="text-slate-400">Tahmini Aralık (24s)</span>
                    <span className="font-mono text-white">{lowRange} - {highRange}</span>
                </div>
                <div className="flex justify-between text-sm border-b border-slate-800 pb-2">
                    <span className="text-slate-400">Trend Gücü</span>
                    <span className={clsx("font-mono", color === "green" ? "text-green-400" : "text-slate-300")}>
                        {confidence > 75 ? "Yüksek (Boğa)" : "Orta"}
                    </span>
                </div>
                <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Model Sürümü</span>
                    <span className="font-mono text-cyan-500">v2.1-Alpha</span>
                </div>
            </div>
        </div>
    );
}
