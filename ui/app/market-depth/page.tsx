"use client";

import { useState, useEffect } from "react";
import OrderBook from "@/components/market-depth/OrderBook";
import DepthChart from "@/components/market-depth/DepthChart";
import { useMarketStore } from "@/store/marketStore";
import clsx from "clsx";
import { ArrowLeft, Search, Clock, ArrowUp, ArrowDown } from "lucide-react";

// Mock Recent Trades (Time & Sales)
const RecentTrades = ({ ticker }: { ticker: string }) => {
    const [trades, setTrades] = useState<{ p: number, q: number, t: string, side: 'buy' | 'sell' }[]>([]);

    useEffect(() => {
        // Init trades
        const initial = Array.from({ length: 20 }, (_, i) => ({
            p: 100 + (Math.random() - 0.5),
            q: Math.floor(Math.random() * 1000) + 10,
            t: `10:${59 - i}:${Math.floor(Math.random() * 60)}`,
            side: Math.random() > 0.5 ? 'buy' : 'sell' as 'buy' | 'sell'
        }));
        setTrades(initial);

        // Simulate live feed
        const interval = setInterval(() => {
            const newTrade = {
                p: 100 + (Math.random() - 0.5),
                q: Math.floor(Math.random() * 500) + 10,
                t: new Date().toLocaleTimeString('tr-TR'),
                side: Math.random() > 0.5 ? 'buy' : 'sell' as 'buy' | 'sell'
            };
            setTrades(prev => [newTrade, ...prev.slice(0, 19)]);
        }, 800);

        return () => clearInterval(interval);
    }, [ticker]);

    return (
        <div className="flex flex-col h-full rounded-xl border border-slate-800 bg-slate-900/60 glass overflow-hidden">
            <div className="bg-slate-950/50 p-3 border-b border-slate-800 flex justify-between items-center text-xs font-bold text-slate-400">
                <span className="flex items-center gap-1"><Clock size={12} /> ZAMAN</span>
                <span>FİYAT</span>
                <span>MİKTAR</span>
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-thin">
                {trades.map((t, i) => (
                    <div key={i} className="flex justify-between items-center px-3 py-1 text-xs hover:bg-slate-800/50 transition-colors code-font border-b border-slate-800/30 last:border-0">
                        <span className="text-slate-500 font-mono">{t.t}</span>
                        <span className={clsx("font-bold font-mono", t.side === 'buy' ? "text-green-400" : "text-red-400")}>
                            {t.p.toFixed(2)}
                        </span>
                        <span className="text-slate-300 font-mono">{t.q}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}


export default function MarketDepthPage() {
    const { tickers, selectedTicker, setTicker } = useMarketStore();
    const currentTicker = tickers.find((t) => t.symbol === selectedTicker) || tickers[0];

    return (
        <div className="flex flex-col gap-6 w-full h-full text-white overflow-hidden">

            {/* 1. Header with Ticker Selector */}
            <div className="flex justify-between items-center flex-shrink-0">
                <div className="flex items-center gap-4">
                    <h1 className="text-3xl font-display font-bold tracking-tight text-white/90">
                        PİYASA DERİNLİĞİ
                    </h1>
                    <div className="h-8 w-px bg-slate-800"></div>

                    {/* Ticker Dropdown / Info */}
                    <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2">
                        <span className="font-bold text-xl text-white">{selectedTicker}</span>
                        <div className="flex flex-col items-end leading-none">
                            <span className="text-sm font-mono text-white font-bold">{currentTicker.price.toFixed(2)}</span>
                            <span className={clsx("text-xs font-bold", currentTicker.change >= 0 ? "text-green-400" : "text-red-400")}>
                                {currentTicker.change}%
                            </span>
                        </div>
                    </div>

                    {/* Quick Switcher */}
                    <div className="flex gap-2">
                        {tickers.filter(t => t.symbol !== selectedTicker).slice(0, 3).map(t => (
                            <button
                                key={t.symbol}
                                onClick={() => setTicker(t.symbol)}
                                className="px-3 py-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-800 text-xs font-bold text-slate-400 hover:text-white transition-colors"
                            >
                                {t.symbol}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="text-xs font-mono text-slate-500 flex gap-4">
                    <span>Level 2 Data</span>
                    <span className="text-green-400 animate-pulse">● BAĞLI</span>
                </div>
            </div>

            {/* 2. Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0 flex-1 pb-2">

                {/* Order Book (Left - 3 cols) */}
                <div className="lg:col-span-3 h-full min-h-0 flex flex-col">
                    <OrderBook />
                </div>

                {/* Depth Chart & Stats (Center - 6 cols) */}
                <div className="lg:col-span-6 h-full min-h-0 flex flex-col gap-6">
                    <div className="flex-1 min-h-0">
                        <DepthChart />
                    </div>

                    {/* Order Flow Imbalance / Stats Placeholder */}
                    <div className="h-48 p-4 rounded-xl border border-slate-800 bg-slate-900/60 glass flex flex-col justify-center">
                        <h4 className="text-xs font-bold text-slate-400 mb-2 uppercase tracking-wider">Emir Dengesizliği</h4>
                        <div className="w-full h-4 bg-slate-800 rounded-full overflow-hidden flex mb-2">
                            <div className="bg-green-500 w-[65%] h-full"></div>
                            <div className="bg-red-500 w-[35%] h-full"></div>
                        </div>
                        <div className="flex justify-between text-xs font-bold">
                            <span className="text-green-400">%65 ALIŞ BASKISI</span>
                            <span className="text-red-400">%35 SATIŞ BASKISI</span>
                        </div>
                    </div>
                </div>

                {/* Recent Trades (Right - 3 cols) */}
                <div className="lg:col-span-3 h-full min-h-0 flex flex-col">
                    <RecentTrades ticker={selectedTicker} />
                </div>

            </div>
        </div>
    );
}

