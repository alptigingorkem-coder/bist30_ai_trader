"use client";

import { useState, useMemo } from "react";
import { useMarketStore } from "@/store/marketStore";
import clsx from "clsx";
import { Filter, ArrowUp, ArrowDown, Search } from "lucide-react";

interface FilterState {
    changeMin: number | null;
    changeMax: number | null;
    volumeMin: number | null;
    // RSI filter would require backend - we'll simulate later
}

export default function StockScreener() {
    const { tickers, setTicker, selectedTicker } = useMarketStore();
    const [searchTerm, setSearchTerm] = useState("");
    const [filters, setFilters] = useState<FilterState>({
        changeMin: null,
        changeMax: null,
        volumeMin: null,
    });
    const [showFilters, setShowFilters] = useState(false);

    // Apply Filters
    const filteredTickers = useMemo(() => {
        let result = [...tickers];

        // Search filter
        if (searchTerm) {
            result = result.filter(t =>
                t.symbol.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        // Change filters
        if (filters.changeMin !== null) {
            result = result.filter(t => t.change >= filters.changeMin!);
        }
        if (filters.changeMax !== null) {
            result = result.filter(t => t.change <= filters.changeMax!);
        }

        // Volume filter (using volume_raw)
        if (filters.volumeMin !== null) {
            result = result.filter(t =>
                ((t as any).volume_raw || 0) >= filters.volumeMin! * 1_000_000
            );
        }

        return result;
    }, [tickers, searchTerm, filters]);

    return (
        <div className="flex flex-col h-full bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <h3 className="font-display font-bold text-white">HİSSE TARAMA</h3>
                <button
                    onClick={() => setShowFilters(!showFilters)}
                    className={clsx(
                        "p-2 rounded-lg transition-colors",
                        showFilters ? "bg-cyan-500/20 text-cyan-400" : "bg-slate-800 text-slate-400 hover:text-white"
                    )}
                >
                    <Filter size={16} />
                </button>
            </div>

            {/* Search */}
            <div className="p-3 border-b border-slate-800">
                <div className="relative">
                    <Search className="absolute left-3 top-2.5 text-slate-500" size={16} />
                    <input
                        type="text"
                        placeholder="Hisse ara..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg py-2 pl-9 pr-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                    />
                </div>
            </div>

            {/* Filter Panel (Collapsible) */}
            {showFilters && (
                <div className="p-3 border-b border-slate-800 bg-slate-900/80 space-y-3">
                    <div className="text-xs font-bold text-slate-400 mb-2">FİLTRELER</div>

                    {/* Change Range */}
                    <div className="flex gap-2 items-center">
                        <span className="text-xs text-slate-500 w-16">Değişim %</span>
                        <input
                            type="number"
                            placeholder="Min"
                            className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                            onChange={(e) => setFilters(f => ({ ...f, changeMin: e.target.value ? parseFloat(e.target.value) : null }))}
                        />
                        <span className="text-slate-600">—</span>
                        <input
                            type="number"
                            placeholder="Max"
                            className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                            onChange={(e) => setFilters(f => ({ ...f, changeMax: e.target.value ? parseFloat(e.target.value) : null }))}
                        />
                    </div>

                    {/* Volume Min */}
                    <div className="flex gap-2 items-center">
                        <span className="text-xs text-slate-500 w-16">Hacim</span>
                        <input
                            type="number"
                            placeholder="Min (M)"
                            className="w-24 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                            onChange={(e) => setFilters(f => ({ ...f, volumeMin: e.target.value ? parseFloat(e.target.value) : null }))}
                        />
                        <span className="text-xs text-slate-500">Milyon</span>
                    </div>

                    {/* Clear Button */}
                    <button
                        onClick={() => setFilters({ changeMin: null, changeMax: null, volumeMin: null })}
                        className="text-xs text-red-400 hover:text-red-300"
                    >
                        Filtreleri Temizle
                    </button>
                </div>
            )}

            {/* Results List */}
            <div className="flex-1 overflow-y-auto scrollbar-thin">
                {filteredTickers.length === 0 ? (
                    <div className="p-4 text-center text-slate-500 text-sm">Sonuç bulunamadı</div>
                ) : (
                    filteredTickers.map((t) => (
                        <div
                            key={t.symbol}
                            onClick={() => setTicker(t.symbol)}
                            className={clsx(
                                "flex justify-between items-center px-4 py-3 border-b border-slate-800/50 cursor-pointer transition-colors",
                                selectedTicker === t.symbol
                                    ? "bg-cyan-950/30 border-l-2 border-l-cyan-500"
                                    : "hover:bg-slate-800/50"
                            )}
                        >
                            <div>
                                <div className="font-bold text-white text-sm">{t.symbol}</div>
                                <div className="text-xs text-slate-500">Vol: {t.volume}</div>
                            </div>
                            <div className="text-right">
                                <div className="font-mono text-white text-sm">{t.price.toFixed(2)}</div>
                                <div className={clsx(
                                    "flex items-center justify-end gap-0.5 text-xs font-bold",
                                    t.change >= 0 ? "text-green-400" : "text-red-400"
                                )}>
                                    {t.change >= 0 ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
                                    {Math.abs(t.change).toFixed(2)}%
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Footer Stats */}
            <div className="p-3 border-t border-slate-800 text-xs text-slate-500 flex justify-between">
                <span>{filteredTickers.length} / {tickers.length} gösteriliyor</span>
                <span className="text-cyan-400 font-bold">CANLI</span>
            </div>
        </div>
    );
}
