"use client";

import { useMarketStore } from "@/store/marketStore";
import TechnicalPanel from "@/components/dashboard/TechnicalPanel";
import { getTickerMeta, getVolatilityLevel } from "@/lib/tickerMeta";
import clsx from "clsx";
import { ArrowLeft, Search } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo } from "react";

export default function AnalysisPage() {
    const { tickers, selectedTicker, setTicker, connectWebSocket, isConnected } = useMarketStore();

    useEffect(() => {
        connectWebSocket();
    }, []);

    // Seçili hissenin meta bilgilerini ve volatilitesini hesapla
    const tickerInfo = useMemo(() => {
        const meta = getTickerMeta(selectedTicker);
        const tickerData = tickers.find(t => t.symbol === selectedTicker);
        const change = tickerData?.change || 0;
        const volatility = getVolatilityLevel(change);

        // Volatilite renk kodları (Tailwind JIT ile uyumluluk için inline)
        const volatilityColors: Record<string, string> = {
            "DÜŞÜK": "#4ade80",      // green-400
            "NORMAL": "#22d3ee",     // cyan-400
            "YÜKSEK": "#fb923c",     // orange-400
            "ÇOK YÜKSEK": "#f87171"  // red-400
        };
        const volatilityColor = volatilityColors[volatility];

        return { meta, volatility, volatilityColor };
    }, [selectedTicker, tickers]);

    return (
        <div className="flex w-full h-full gap-6">

            {/* 1. Left Sidebar: Watchlist / Ticker Selector */}
            <div className="w-80 flex flex-col gap-4">
                <div className="flex items-center gap-2 mb-2">
                    <Link href="/" className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors">
                        <ArrowLeft size={20} />
                    </Link>
                    <h1 className="text-2xl font-display font-bold text-white">ANALİZ</h1>
                </div>

                <div className="relative">
                    <Search className="absolute left-3 top-3 text-slate-500" size={18} />
                    <input
                        type="text"
                        placeholder="Hisse Ara..."
                        className="w-full bg-slate-900 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-cyan-500 transition-colors"
                    />
                </div>

                <div className="flex-1 overflow-y-auto space-y-2 pr-2 scrollbar-thin scrollbar-thumb-slate-800">
                    {tickers.map((t) => (
                        <div
                            key={t.symbol}
                            onClick={() => setTicker(t.symbol)}
                            className={clsx(
                                "p-3 rounded-xl border cursor-pointer transition-all flex justify-between items-center group",
                                selectedTicker === t.symbol
                                    ? "border-cyan-500/50 bg-cyan-950/20 shadow-lg shadow-cyan-900/10"
                                    : "border-slate-800 bg-slate-900/40 hover:bg-slate-800"
                            )}
                        >
                            <div>
                                <div className="font-bold text-white group-hover:text-cyan-400 transition-colors">{t.symbol}</div>
                                <div className="text-xs text-slate-500">Hacim: {t.volume}</div>
                            </div>
                            <div className="text-right">
                                <div className="font-mono text-slate-200">{t.price.toFixed(2)}</div>
                                <div className={clsx("text-xs font-bold", t.change >= 0 ? "text-green-400" : "text-red-400")}>
                                    {t.change > 0 ? "+" : ""}{t.change}%
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* 2. Main Content: Technical Details */}
            <div className="flex-1 flex flex-col gap-6 overflow-y-auto">

                {/* Top Summary Bar */}
                <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 to-slate-900/50 border border-slate-800 flex justify-between items-center relative overflow-hidden">
                    {/* Background Decoration */}
                    <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>

                    <div>
                        <div className="flex items-baseline gap-4">
                            <h2 className="text-4xl font-display font-bold text-white">{selectedTicker}</h2>
                            <span className="text-2xl font-mono text-white">
                                {tickers.find(t => t.symbol === selectedTicker)?.price.toFixed(2)}
                            </span>
                            <span className={clsx(
                                "text-lg font-bold",
                                (tickers.find(t => t.symbol === selectedTicker)?.change || 0) >= 0 ? "text-green-400" : "text-red-400"
                            )}>
                                {(tickers.find(t => t.symbol === selectedTicker)?.change || 0) > 0 ? "+" : ""}
                                {tickers.find(t => t.symbol === selectedTicker)?.change}%
                            </span>
                        </div>
                        <div className="text-slate-400 text-sm mt-1">
                            BIST 30 • {tickerInfo.meta.sector} • {tickerInfo.volatility} VOLATİLİTE
                        </div>
                    </div>

                    <div className="flex gap-4 z-10">
                        <div className="text-right">
                            <div className="text-xs text-slate-500 uppercase tracking-wider">AI Sinyali</div>
                            <div className="text-xl font-bold text-green-400 animate-pulse">GÜÇLÜ AL</div>
                        </div>
                        <div className="w-px h-10 bg-slate-800"></div>
                        <div className="text-right">
                            <div className="text-xs text-slate-500 uppercase tracking-wider">Güven</div>
                            <div className="text-xl font-bold text-white font-mono">87%</div>
                        </div>
                    </div>
                </div>

                {/* Technical Panel Component */}
                <TechnicalPanel ticker={selectedTicker} />

            </div>
        </div>
    );
}
