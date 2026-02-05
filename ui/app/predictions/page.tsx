"use client";

import PredictionTable from "@/components/predictions/PredictionTable";
import { CheckCircle, AlertTriangle, Cpu, TrendingUp } from "lucide-react";

export default function PredictionsPage() {
    return (
        <div className="flex flex-col gap-6 w-full h-full text-white overflow-hidden">
            <div className="flex justify-between items-center flex-shrink-0">
                <h1 className="text-3xl font-display font-bold tracking-tight text-white/90">
                    AI TAHMİNLER
                </h1>
                <div className="flex gap-2">
                    <button className="px-4 py-2 rounded-lg bg-cyan-500/10 text-cyan-400 font-bold text-sm border border-cyan-500/20 hover:bg-cyan-500/20 transition-colors">
                        Modeli Yenile
                    </button>
                    <button className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 font-bold text-sm border border-slate-700 hover:bg-slate-700 transition-colors">
                        Ayarlar
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-0 flex-1 pb-2">

                {/* 1. Main Predictions Table (3/4 width) */}
                <div className="lg:col-span-3 flex flex-col min-h-0">
                    <PredictionTable />
                </div>

                {/* 2. Right Sidebar: Model Metrics (1/4 width) */}
                <div className="flex flex-col gap-6 overflow-y-auto pr-2 scrollbar-thin">

                    {/* Overall Accuracy Card */}
                    <div className="p-6 rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-900/50 glass relative overflow-hidden flex-shrink-0">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/10 rounded-full blur-2xl -mr-8 -mt-8 pointer-events-none"></div>

                        <div className="flex items-center gap-2 mb-2 text-green-400 font-bold text-sm">
                            <CheckCircle size={16} /> MODEL DOĞRULUĞU
                        </div>
                        <div className="text-4xl font-mono font-bold text-white mb-1">
                            76.4%
                        </div>
                        <div className="text-xs text-slate-500">
                            Son 500 İşlem • Backtest ile Doğrulandı
                        </div>
                    </div>

                    {/* Active Regimes */}
                    <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 glass flex-shrink-0">
                        <h3 className="font-display font-bold text-white mb-3 flex items-center gap-2">
                            <Cpu size={18} className="text-purple-400" /> AKTİF PİYASA REJİMİ
                        </h3>
                        <div className="space-y-3">
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-slate-400">Bull Trend</span>
                                <span className="px-2 py-0.5 rounded bg-green-500/20 text-green-400 font-bold text-xs">Yüksek Olasılık</span>
                            </div>
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-slate-400">Volatility</span>
                                <span className="px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-400 font-bold text-xs">Orta</span>
                            </div>
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-slate-400">Mean Reversion</span>
                                <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-500 font-bold text-xs">Pasif</span>
                            </div>
                        </div>
                    </div>

                    {/* Top Gainers (AI Picks) */}
                    <div className="flex-1 p-4 rounded-xl border border-slate-800 bg-slate-900/40 glass flex-shrink-0">
                        <h3 className="font-display font-bold text-white mb-3 flex items-center gap-2">
                            <TrendingUp size={18} className="text-cyan-400" /> EN İYİ PERFORMANS
                        </h3>
                        <div className="space-y-3">
                            {[{ s: 'GARAN', p: '+12.4%' }, { s: 'THYAO', p: '+8.1%' }, { s: 'AKBNK', p: '+5.6%' }].map((item, idx) => (
                                <div key={idx} className="flex justify-between items-center p-2 rounded bg-slate-800/30 border border-slate-800/50">
                                    <span className="font-bold text-white text-sm">{item.s}</span>
                                    <span className="font-mono text-green-400 font-bold text-sm">{item.p}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}

