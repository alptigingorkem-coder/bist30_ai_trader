"use client";

import { useMarketStore } from "@/store/marketStore";
import { ArrowUp, ArrowDown, Search } from "lucide-react";
import clsx from "clsx";
import { useState } from "react";

export default function Watchlist() {
    const { tickers, selectedTicker, setTicker } = useMarketStore();
    const [searchTerm, setSearchTerm] = useState("");

    const filteredTickers = tickers.filter((t) =>
        t.symbol.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="flex flex-col h-[350px] bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden backdrop-blur-sm">
            {/* Header & Search */}
            <div className="p-3 border-b border-slate-800 bg-slate-900/60">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="font-display font-bold text-slate-100 text-sm">PİYASA İZLEME</h3>
                    <span className="text-xs text-slate-500 font-mono">{tickers.length} Hisse</span>
                </div>
                <div className="relative">
                    <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input
                        type="text"
                        placeholder="Ara..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-slate-950/50 border border-slate-700/50 rounded-md py-1.5 pl-8 pr-2 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-cyan-500/50 transition-colors"
                    />
                </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
                <div className="flex flex-col">
                    {filteredTickers.map((ticker) => {
                        const isBullish = ticker.change >= 0;
                        const isSelected = selectedTicker === ticker.symbol;

                        return (
                            <div
                                key={ticker.symbol}
                                onClick={() => setTicker(ticker.symbol)}
                                className={clsx(
                                    "flex items-center justify-between p-3 border-b border-slate-800/50 cursor-pointer transition-colors hover:bg-slate-800/40",
                                    isSelected && "bg-cyan-950/20 border-l-2 border-l-cyan-500"
                                )}
                            >
                                <div className="flex flex-col">
                                    <span className={clsx("font-display font-bold text-sm", isSelected ? "text-cyan-400" : "text-slate-200")}>
                                        {ticker.symbol}
                                    </span>
                                    <span className="text-[10px] text-slate-500 font-mono">{ticker.volume}</span>
                                </div>

                                <div className="flex flex-col items-end">
                                    <span className="font-mono font-medium text-sm text-slate-200">
                                        {ticker.price.toFixed(2)}
                                    </span>
                                    <span
                                        className={clsx(
                                            "flex items-center gap-0.5 text-[10px] font-bold",
                                            isBullish ? "text-green-400" : "text-red-400"
                                        )}
                                    >
                                        {isBullish ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
                                        {Math.abs(ticker.change).toFixed(2)}%
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
