"use client";

import { useState, useEffect, useCallback } from "react";
import { XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area, AreaChart, BarChart, Bar, Cell } from "recharts";
import { Play, Calendar, TrendingUp, TrendingDown, AlertTriangle, Clock, ArrowUpRight, ArrowDownRight, Info, RefreshCw } from "lucide-react";
import clsx from "clsx";

const API_BASE = "http://localhost:8000";

// Metric Card Component
const MetricCard = ({ label, value, subValue, icon, color = "white" }: {
    label: string;
    value: string;
    subValue?: string;
    icon?: React.ReactNode;
    color?: string;
}) => (
    <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2 mb-1">
            {icon && <span className={`text-${color}-400`}>{icon}</span>}
            <span className="text-xs text-slate-400">{label}</span>
        </div>
        <div className={`text-xl font-mono font-bold text-${color}-400`}>{value}</div>
        {subValue && <div className="text-xs text-slate-500 mt-1">{subValue}</div>}
    </div>
);

interface BacktestResult {
    metrics: {
        totalReturn: number;
        cagr: number;
        sharpeRatio: number;
        sortinoRatio: number;
        maxDrawdown: number;
        calmarRatio: number;
        totalTrades: number;
        winRate: number;
        profitFactor: number;
        avgHoldingDays: number;
    };
    equityCurve: Array<{ date: string; equity: number; drawdown: number }>;
    monthlyReturns: Array<{ month: string; value: number }>;
    config: {
        trainStart: string;
        trainEnd: string;
        testEnd: string;
        initialCapital: number;
        portfolioSize: number;
        tickerCount: number;
    };
}

export default function BacktestPage() {
    // Form State
    const [trainStart, setTrainStart] = useState("2015-01-01");
    const [trainEnd, setTrainEnd] = useState("2021-01-01");
    const [testEnd, setTestEnd] = useState("2024-12-31");
    const [initialCapital, setInitialCapital] = useState("100000");

    // Job State
    const [isRunning, setIsRunning] = useState(false);
    const [jobId, setJobId] = useState<string | null>(null);
    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState("");
    const [error, setError] = useState<string | null>(null);

    // Results
    const [results, setResults] = useState<BacktestResult | null>(null);

    // Validation
    const [validationError, setValidationError] = useState<string | null>(null);

    // Auto-sync trainEnd with testStart
    useEffect(() => {
        // trainEnd should be the test start date
        // No action needed if user changes manually
    }, [trainEnd]);

    // Validate dates on change
    useEffect(() => {
        const validateDates = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/backtest/validate`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        train_start: trainStart,
                        train_end: trainEnd,
                        test_end: testEnd,
                        initial_capital: parseFloat(initialCapital)
                    })
                });
                const data = await res.json();
                setValidationError(data.valid ? null : data.error);
            } catch {
                // API not available, skip validation
                setValidationError(null);
            }
        };

        validateDates();
    }, [trainStart, trainEnd, testEnd, initialCapital]);

    // Poll job status
    const pollStatus = useCallback(async (id: string) => {
        try {
            const res = await fetch(`${API_BASE}/api/backtest/status/${id}`);
            const data = await res.json();

            if (!data.success) {
                setError(data.error);
                setIsRunning(false);
                return;
            }

            setProgress(data.progress);
            setStatusMessage(data.message);

            if (data.status === "completed") {
                setResults(data.result);
                setIsRunning(false);
            } else if (data.status === "error") {
                setError(data.message);
                setIsRunning(false);
            } else {
                // Continue polling
                setTimeout(() => pollStatus(id), 1000);
            }
        } catch (err) {
            setError("API bağlantı hatası");
            setIsRunning(false);
        }
    }, []);

    // Start backtest
    const runBacktest = async () => {
        if (validationError) return;

        setIsRunning(true);
        setError(null);
        setResults(null);
        setProgress(0);
        setStatusMessage("Başlatılıyor...");

        try {
            const res = await fetch(`${API_BASE}/api/backtest/run`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    train_start: trainStart,
                    train_end: trainEnd,
                    test_end: testEnd,
                    initial_capital: parseFloat(initialCapital)
                })
            });
            const data = await res.json();

            if (!data.success) {
                setError(data.error);
                setIsRunning(false);
                return;
            }

            setJobId(data.job_id);
            pollStatus(data.job_id);
        } catch (err) {
            setError("API bağlantı hatası. Sunucu çalışıyor mu?");
            setIsRunning(false);
        }
    };

    return (
        <div className="flex flex-col gap-6 w-full h-full text-white overflow-y-auto pr-2 pb-8">
            {/* Header */}
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-display font-bold tracking-tight text-white/90">
                    GERİYE DÖNÜK TEST
                </h1>
                <div className="text-xs font-mono text-slate-500">
                    STRATEJİ: AI RANKER v2.1
                </div>
            </div>

            {/* Configuration Panel */}
            <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 glass">
                <h3 className="font-display font-bold text-white mb-4 flex items-center gap-2">
                    <Calendar size={18} className="text-cyan-400" />
                    AYARLAR
                </h3>

                {/* Training Period */}
                <div className="mb-4">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                        <span className="text-sm font-medium text-slate-300">EĞİTİM DÖNEMİ</span>
                        <Info size={14} className="text-slate-500" title="Model bu dönemdeki verilerle eğitilir" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs text-slate-400 mb-2">EĞİTİM BAŞLANGIÇ</label>
                            <input type="date" value={trainStart} onChange={(e) => setTrainStart(e.target.value)}
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500" />
                        </div>
                        <div>
                            <label className="block text-xs text-slate-400 mb-2">EĞİTİM BİTİŞ</label>
                            <input type="date" value={trainEnd} onChange={(e) => setTrainEnd(e.target.value)}
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500" />
                        </div>
                    </div>
                </div>

                {/* Test Period */}
                <div className="mb-4">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-3 h-3 rounded-full bg-green-500"></div>
                        <span className="text-sm font-medium text-slate-300">TEST DÖNEMİ</span>
                        <Info size={14} className="text-slate-500" title="Backtest bu dönemde çalışır" />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-xs text-slate-400 mb-2">TEST BAŞLANGIÇ</label>
                            <input type="date" value={trainEnd} disabled
                                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-slate-400 cursor-not-allowed" />
                            <span className="text-xs text-slate-500 mt-1">= Eğitim Bitiş</span>
                        </div>
                        <div>
                            <label className="block text-xs text-slate-400 mb-2">TEST BİTİŞ</label>
                            <input type="date" value={testEnd} onChange={(e) => setTestEnd(e.target.value)}
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-green-500" />
                        </div>
                        <div>
                            <label className="block text-xs text-slate-400 mb-2">BAŞLANGIÇ SERMAYESİ (₺)</label>
                            <input type="number" value={initialCapital} onChange={(e) => setInitialCapital(e.target.value)}
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white font-mono focus:outline-none focus:border-cyan-500" />
                        </div>
                    </div>
                </div>

                {/* Validation Error */}
                {validationError && (
                    <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center gap-2">
                        <AlertTriangle size={16} className="text-red-400" />
                        <span className="text-sm text-red-400">{validationError}</span>
                    </div>
                )}

                {/* Info Banner */}
                <div className="mb-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center gap-2">
                    <Clock size={16} className="text-amber-400" />
                    <span className="text-sm text-amber-300">
                        Model eğitim süresi: ~2-5 dakika (veri miktarına bağlı)
                    </span>
                </div>

                {/* Run Button */}
                <button onClick={runBacktest} disabled={isRunning || !!validationError}
                    className={clsx("w-full py-4 rounded-lg font-bold flex items-center justify-center gap-2 transition-colors text-lg",
                        isRunning || validationError
                            ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                            : "bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white")}>
                    {isRunning ? (
                        <>
                            <RefreshCw size={20} className="animate-spin" />
                            {statusMessage} ({progress}%)
                        </>
                    ) : (
                        <>
                            <Play size={20} />
                            TESTİ BAŞLAT
                        </>
                    )}
                </button>

                {/* Progress Bar */}
                {isRunning && (
                    <div className="mt-4">
                        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300"
                                style={{ width: `${progress}%` }}
                            ></div>
                        </div>
                    </div>
                )}

                {/* Error Display */}
                {error && (
                    <div className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/30">
                        <div className="flex items-center gap-2 text-red-400">
                            <AlertTriangle size={18} />
                            <span className="font-bold">Hata</span>
                        </div>
                        <p className="text-red-300 mt-2">{error}</p>
                    </div>
                )}
            </div>

            {/* Results */}
            {results && (
                <>
                    {/* Config Summary */}
                    <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700">
                        <div className="flex flex-wrap gap-4 text-sm">
                            <div>
                                <span className="text-slate-400">Eğitim: </span>
                                <span className="text-blue-400 font-mono">{results.config.trainStart} → {results.config.trainEnd}</span>
                            </div>
                            <div>
                                <span className="text-slate-400">Test: </span>
                                <span className="text-green-400 font-mono">{results.config.trainEnd} → {results.config.testEnd}</span>
                            </div>
                            <div>
                                <span className="text-slate-400">Hisse Sayısı: </span>
                                <span className="text-white font-mono">{results.config.tickerCount}</span>
                            </div>
                            <div>
                                <span className="text-slate-400">Portföy: </span>
                                <span className="text-white font-mono">Top {results.config.portfolioSize}</span>
                            </div>
                        </div>
                    </div>

                    {/* Row 1: Key Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                        <div className="p-4 rounded-xl border border-green-500/30 bg-gradient-to-br from-green-900/30 to-slate-900">
                            <div className="text-xs text-slate-400">TOPLAM GETİRİ</div>
                            <div className={clsx("text-2xl font-mono font-bold", results.metrics.totalReturn >= 0 ? "text-green-400" : "text-red-400")}>
                                {results.metrics.totalReturn >= 0 ? "+" : ""}{results.metrics.totalReturn}%
                            </div>
                        </div>
                        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
                            <div className="text-xs text-slate-400">BİTİŞ SERMAYESİ</div>
                            <div className="text-2xl font-mono font-bold text-white">
                                ₺{(parseFloat(initialCapital) * (1 + results.metrics.totalReturn / 100)).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                            </div>
                        </div>
                        <MetricCard label="CAGR" value={`${results.metrics.cagr}%`} color="green" />
                        <MetricCard label="SHARPE ORANI" value={results.metrics.sharpeRatio.toString()} color="white" />
                        <MetricCard label="SORTINO ORANI" value={results.metrics.sortinoRatio.toString()} color="white" />
                        <div className="p-4 rounded-xl border border-red-500/30 bg-slate-900/60">
                            <div className="flex items-center gap-1 text-xs text-slate-400">
                                <AlertTriangle size={12} className="text-red-400" />MAKS DRAWDOWN
                            </div>
                            <div className="text-xl font-mono font-bold text-red-400">{results.metrics.maxDrawdown}%</div>
                        </div>
                    </div>

                    {/* Row 2: Trade Stats */}
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                        <MetricCard label="KAZANMA ORANI" value={`${results.metrics.winRate}%`} color="green" />
                        <MetricCard label="TOPLAM İŞLEM" value={results.metrics.totalTrades.toString()} />
                        <MetricCard label="KÂR FAKTÖRÜ" value={results.metrics.profitFactor.toString()} color="cyan" />
                        <MetricCard label="CALMAR ORANI" value={results.metrics.calmarRatio.toString()} color="white" />
                        <MetricCard label="ORT. SÜRE" value={`${results.metrics.avgHoldingDays} gün`} icon={<Clock size={14} />} />
                    </div>

                    {/* Row 3: Charts */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Equity Curve */}
                        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60">
                            <h3 className="font-display font-bold text-white mb-4 flex items-center gap-2">
                                <TrendingUp size={18} className="text-green-400" />ÖZKAYNAK EĞRİSİ
                            </h3>
                            <div className="h-[250px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={results.equityCurve}>
                                        <defs>
                                            <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#00c853" stopOpacity={0.4} />
                                                <stop offset="95%" stopColor="#00c853" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                        <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10 }} />
                                        <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={(v) => `₺${(v / 1000).toFixed(0)}K`} />
                                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }} />
                                        <Area type="monotone" dataKey="equity" stroke="#00c853" strokeWidth={2} fill="url(#colorEquity)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Drawdown Chart */}
                        <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60">
                            <h3 className="font-display font-bold text-white mb-4 flex items-center gap-2">
                                <TrendingDown size={18} className="text-red-400" />DÜŞÜŞ (DRAWDOWN)
                            </h3>
                            <div className="h-[250px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={results.equityCurve}>
                                        <defs>
                                            <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.6} />
                                                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                        <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10 }} />
                                        <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}%`} domain={[-50, 0]} />
                                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }} />
                                        <Area type="monotone" dataKey="drawdown" stroke="#ef4444" strokeWidth={2} fill="url(#colorDrawdown)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>

                    {/* Row 4: Monthly Returns */}
                    <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60">
                        <h3 className="font-display font-bold text-white mb-4">AYLIK GETİRİLER</h3>
                        <div className="h-[200px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={results.monthlyReturns}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                    <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 10 }} />
                                    <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
                                    <Tooltip
                                        content={({ active, payload, label }) => {
                                            if (active && payload && payload.length) {
                                                const value = payload[0].value as number;
                                                return (
                                                    <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/95 shadow-xl">
                                                        <p className="text-slate-200 font-bold mb-1 text-xs">{label}</p>
                                                        <div className="flex items-center gap-2">
                                                            <div className={`w-2 h-2 rounded-full ${value >= 0 ? 'bg-green-500' : 'bg-red-500'}`}></div>
                                                            <p className={`text-sm font-mono font-bold ${value >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                                %{value}
                                                            </p>
                                                        </div>
                                                    </div>
                                                );
                                            }
                                            return null;
                                        }}
                                        cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                    />
                                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                                        {results.monthlyReturns.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.value >= 0 ? "#00c853" : "#ef4444"} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </>
            )}

            {/* Empty State */}
            {!results && !isRunning && (
                <div className="flex-1 flex items-center justify-center text-slate-500 text-center">
                    <div>
                        <div className="text-6xl mb-4">📊</div>
                        <div className="font-bold mb-2">Henüz Test Sonucu Yok</div>
                        <div className="text-sm">Yukarıdaki parametreleri ayarlayın ve &quot;Testi Başlat&quot; butonuna tıklayın.</div>
                    </div>
                </div>
            )}
        </div>
    );
}
