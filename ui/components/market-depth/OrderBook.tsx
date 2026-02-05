"use client";

import { useMarketStore } from "@/store/marketStore";
import clsx from "clsx";
import { useEffect, useState } from "react";

// Mock Order Data Structure
interface OrderLevel {
    price: number;
    amount: number;
    total: number;
    percent: number; // For depth bar visualization
}

export default function OrderBook() {
    const { selectedTicker, tickers } = useMarketStore();
    const [bids, setBids] = useState<OrderLevel[]>([]);
    const [asks, setAsks] = useState<OrderLevel[]>([]);

    useEffect(() => {
        // Generate Mock Depth Data
        const currentPrice = tickers.find((t) => t.symbol === selectedTicker)?.price || 100;

        const generateLevels = (startPrice: number, type: 'bid' | 'ask') => {
            const levels = [];
            let price = startPrice;
            let cumulative = 0;

            for (let i = 0; i < 15; i++) {
                const step = currentPrice * 0.0005; // 0.05% spread steps
                price = type === 'ask' ? price + step : price - step;

                // Deterministic random volume
                const volume = Math.floor(Math.random() * 50000) + 1000;
                cumulative += volume;

                levels.push({
                    price: price,
                    amount: volume,
                    total: cumulative,
                    percent: 0 // calculated later
                });
            }
            return levels;
        };

        const newAsks = generateLevels(currentPrice, 'ask'); // Selling above
        const newBids = generateLevels(currentPrice, 'bid'); // Buying below

        // Calculate percentages for depth bars (relative to max total volume visible)
        const maxVol = Math.max(newAsks[newAsks.length - 1].total, newBids[newBids.length - 1].total);
        newAsks.forEach(l => l.percent = (l.total / maxVol) * 100);
        newBids.forEach(l => l.percent = (l.total / maxVol) * 100);

        setAsks(newAsks.reverse()); // Show lowest ask at bottom (closest to spread)
        setBids(newBids);
    }, [selectedTicker, tickers]);

    const Row = ({ level, type }: { level: OrderLevel, type: 'bid' | 'ask' }) => (
        <div className="relative flex justify-between text-xs py-0.5 px-2 hover:bg-slate-800 cursor-pointer group">
            {/* Depth Visual Bar */}
            <div
                className={clsx(
                    "absolute top-0 bottom-0 opacity-10 transition-all",
                    type === 'bid' ? "right-0 bg-green-500" : "left-0 bg-red-500"
                )}
                style={{ width: `${level.percent}%` }}
            ></div>

            <span className={clsx("font-mono z-10 w-16", type === 'bid' ? "text-green-400" : "text-red-400 font-bold")}>
                {level.price.toFixed(2)}
            </span>
            <span className="font-mono text-slate-300 z-10 w-16 text-right">
                {level.amount.toLocaleString()}
            </span>
            <span className="font-mono text-slate-500 z-10 text-right flex-1">
                {level.total.toLocaleString()}
            </span>
        </div>
    );

    return (
        <div className="flex flex-col h-full rounded-xl border border-slate-800 bg-slate-900/60 glass overflow-hidden">
            <div className="bg-slate-950/50 p-3 border-b border-slate-800 flex justify-between items-center text-xs font-bold text-slate-400">
                <span>FİYAT</span>
                <span className="text-right">MİKTAR</span>
                <span className="text-right">TOPLAM</span>
            </div>

            <div className="flex-1 overflow-y-auto scrollbar-thin flex flex-col">
                {/* Asks (Sellers) - Red */}
                <div className="flex flex-col-reverse"> {/* Reverse to keep lowest ask at bottom */}
                    {asks.map((level, i) => <Row key={i} level={level} type="ask" />)}
                </div>

                {/* Spread Info */}
                <div className="sticky py-2 my-1 bg-slate-800/50 border-y border-slate-800 text-center font-mono text-sm font-bold text-white z-20">
                    SPREAD: <span className="text-slate-400">0.05%</span>
                </div>

                {/* Bids (Buyers) - Green */}
                <div>
                    {bids.map((level, i) => <Row key={i} level={level} type="bid" />)}
                </div>
            </div>
        </div>
    );
}
