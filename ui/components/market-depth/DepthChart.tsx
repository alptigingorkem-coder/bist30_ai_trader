"use client";

import { useMarketStore } from "@/store/marketStore";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function DepthChart() {
    const { selectedTicker, tickers } = useMarketStore();
    const currentPrice = tickers.find((t) => t.symbol === selectedTicker)?.price || 100;

    // Simulate Cumulative Depth Data
    const data = [];
    const steps = 40;

    // Bids (Green, Left side)
    for (let i = steps; i > 0; i--) {
        const p = currentPrice * (1 - (i * 0.002));
        data.push({
            price: p,
            bidVolume: Math.pow(steps - i, 2) * 100 + 5000,
            askVolume: null,
        });
    }

    // Midpoint
    data.push({ price: currentPrice, bidVolume: 0, askVolume: 0 });

    // Asks (Red, Right side)
    for (let i = 1; i <= steps; i++) {
        const p = currentPrice * (1 + (i * 0.002));
        data.push({
            price: p,
            bidVolume: null,
            askVolume: Math.pow(i, 2) * 100 + 5000,
        });
    }

    return (
        <div className="h-full w-full p-4 rounded-xl border border-slate-800 bg-slate-900/60 glass flex flex-col">
            <h3 className="font-display font-bold text-white mb-4">DERİNLİK GRAFİĞİ ({selectedTicker})</h3>
            <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id="colorBid" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorAsk" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <XAxis
                            dataKey="price"
                            type="number"
                            domain={['auto', 'auto']}
                            tickFormatter={(val) => val.toFixed(2)}
                            stroke="#475569"
                            fontSize={10}
                        />
                        <YAxis hide />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }}
                            itemStyle={{ color: '#fff' }}
                            formatter={(value: any) => value ? value.toLocaleString() : ''}
                            labelFormatter={(label) => `Price: ${Number(label).toFixed(2)}`}
                        />
                        <Area
                            type="step"
                            dataKey="bidVolume"
                            stroke="#22c55e"
                            fillOpacity={1}
                            fill="url(#colorBid)"
                        />
                        <Area
                            type="step"
                            dataKey="askVolume"
                            stroke="#ef4444"
                            fillOpacity={1}
                            fill="url(#colorAsk)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
