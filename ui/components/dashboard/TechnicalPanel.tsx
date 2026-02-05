"use client";

import React from "react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    AreaChart,
    Area
} from "recharts";
import { Activity, TrendingUp, ArrowUp, ArrowDown } from "lucide-react";

// Mock Data for Indicators
const generateIndicatorData = () => {
    const data = [];
    for (let i = 0; i < 30; i++) {
        data.push({
            day: i,
            rsi: 30 + Math.random() * 40 + (i * 0.5), // Trending up
            macd: Math.random() * 2 - 1,
            signal: Math.random() * 2 - 1,
            price: 100 + Math.random() * 10 + i,
            ma20: 100 + i * 0.8,
            ma50: 95 + i * 0.5
        });
    }
    return data;
};

const data = generateIndicatorData();

export default function TechnicalPanel({ ticker }: { ticker: string }) {
    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* 1. RSI Chart */}
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 glass">
                <h3 className="text-slate-300 font-bold mb-4 flex items-center gap-2">
                    <Activity size={16} className="text-cyan-400" /> RSI (14) Momentum
                </h3>
                <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis dataKey="day" hide />
                            <YAxis domain={[0, 100]} stroke="#64748b" fontSize={10} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }}
                                itemStyle={{ color: '#e2e8f0' }}
                            />
                            {/* Overbought/Oversold Lines */}
                            <Line type="monotone" dataKey="rsi" stroke="#00bcd4" strokeWidth={2} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
                <div className="flex justify-between mt-2 text-xs text-slate-500">
                    <span>Aşırı Satım (30)</span>
                    <span className="text-cyan-400 font-bold">Mevcut: 64.2</span>
                    <span>Aşırı Alım (70)</span>
                </div>
            </div>

            {/* 2. MACD Chart */}
            <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 glass">
                <h3 className="text-slate-300 font-bold mb-4 flex items-center gap-2">
                    <TrendingUp size={16} className="text-purple-400" /> MACD Trendi
                </h3>
                <div className="h-[200px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis dataKey="day" hide />
                            <YAxis stroke="#64748b" fontSize={10} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }}
                            />
                            <Area type="monotone" dataKey="macd" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.2} />
                            <Area type="monotone" dataKey="signal" stackId="1" stroke="#ef4444" fill="transparent" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
                <div className="flex justify-between mt-2 text-xs text-slate-500 font-mono">
                    <span>Histogram: <span className="text-green-400">+0.45</span></span>
                    <span>Boğa Kesişimi</span>
                </div>
            </div>

            {/* 3. Moving Averages Summary */}
            <div className="col-span-1 lg:col-span-2 p-6 rounded-xl border border-slate-800 bg-slate-900/40 glass">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-white font-display font-bold text-lg">Detaylı Teknik Özet</h3>
                    <span className="px-3 py-1 bg-green-500/10 text-green-400 text-xs font-bold rounded-full border border-green-500/20">
                        GÜÇLÜ AL
                    </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                        { label: "SMA (20)", value: "76.40", signal: "AL", color: "green" },
                        { label: "SMA (50)", value: "72.15", signal: "AL", color: "green" },
                        { label: "SMA (200)", value: "68.90", signal: "AL", color: "green" },
                        { label: "RSI (14)", value: "64.20", signal: "NÖTR", color: "yellow" },
                        { label: "Stoch %K", value: "82.00", signal: "SAT", color: "red" },
                        { label: "CCI (20)", value: "110.4", signal: "AL", color: "green" },
                        { label: "ADX (14)", value: "35.5", signal: "GÜÇLÜ TREND", color: "cyan" },
                        { label: "Williams %R", value: "-15.0", signal: "AŞIRI ALIM", color: "red" },
                    ].map((item, idx) => (
                        <div key={idx} className="flex flex-col p-3 rounded-lg bg-slate-800/30 border border-slate-800/50">
                            <span className="text-slate-500 text-xs mb-1">{item.label}</span>
                            <div className="flex justify-between items-end">
                                <span className="text-white font-mono font-bold">{item.value}</span>
                                <span className={`text-[10px] font-bold text-${item.color}-400`}>
                                    {item.signal}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

        </div>
    );
}
