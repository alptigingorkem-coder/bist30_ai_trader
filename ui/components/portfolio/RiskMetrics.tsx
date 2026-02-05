"use client";

import { Shield, TrendingDown, Percent, Activity } from "lucide-react";
import clsx from "clsx";

// These would ideally come from a backend risk calculation service
// For now, we show mock values as placeholders
const MOCK_RISK_METRICS = {
    var95: 2450, // 95% VaR in TL
    varPercent: 2.1, // As % of portfolio
    kellyCriterion: 0.23, // Optimal position fraction
    beta: 1.15, // vs XU100
    volatility: 18.4, // Annualized %
    sortino: 0.92,
    correlationBIST: 0.78
};

interface MetricCardProps {
    icon: React.ReactNode;
    label: string;
    value: string;
    subValue?: string;
    color?: string;
}

const MetricCard = ({ icon, label, value, subValue, color = "cyan" }: MetricCardProps) => (
    <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2 mb-2">
            <div className={clsx("text-sm", `text-${color}-400`)}>{icon}</div>
            <span className="text-xs text-slate-400 uppercase tracking-wider">{label}</span>
        </div>
        <div className="text-xl font-mono font-bold text-white">{value}</div>
        {subValue && <div className="text-xs text-slate-500 mt-1">{subValue}</div>}
    </div>
);

export default function RiskMetrics() {
    const metrics = MOCK_RISK_METRICS; // In production: fetch from API

    return (
        <div className="p-6 rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-900/50 glass">
            <h3 className="font-display font-bold text-white mb-4 flex items-center gap-2">
                <Shield size={18} className="text-purple-400" />
                RİSK METRİKLERİ
            </h3>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {/* VaR */}
                <MetricCard
                    icon={<TrendingDown size={16} />}
                    label="VaR (%95)"
                    value={`₺${metrics.var95.toLocaleString()}`}
                    subValue={`Portföyün %${metrics.varPercent}'i`}
                    color="red"
                />

                {/* Kelly Criterion */}
                <MetricCard
                    icon={<Percent size={16} />}
                    label="Kelly Criterion"
                    value={`${(metrics.kellyCriterion * 100).toFixed(0)}%`}
                    subValue="Optimal pozisyon boyutu"
                    color="green"
                />

                {/* Beta */}
                <MetricCard
                    icon={<Activity size={16} />}
                    label="Beta (XU100'e göre)"
                    value={metrics.beta.toFixed(2)}
                    subValue={metrics.beta > 1 ? "Piyasadan daha oynak" : "Piyasadan az oynak"}
                    color="yellow"
                />

                {/* Volatility */}
                <MetricCard
                    icon={<Activity size={16} />}
                    label="Volatilite (Yıllık)"
                    value={`${metrics.volatility}%`}
                    subValue="Son 30 günlük"
                    color="cyan"
                />
            </div>

            {/* Additional Metrics Row */}
            <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="p-3 rounded-lg bg-slate-800/50 flex justify-between items-center">
                    <span className="text-xs text-slate-400">Sortino Ratio</span>
                    <span className="font-mono font-bold text-white">{metrics.sortino}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-800/50 flex justify-between items-center">
                    <span className="text-xs text-slate-400">BIST30 Korelasyonu</span>
                    <span className="font-mono font-bold text-white">{metrics.correlationBIST}</span>
                </div>
            </div>

            {/* Disclaimer */}
            <div className="mt-4 p-3 rounded-lg bg-yellow-900/20 border border-yellow-700/30 text-xs text-yellow-200/80">
                ⚠️ Risk metrikleri geçmiş verilere dayalıdır ve gelecek performansı tahmin etmez.
            </div>
        </div>
    );
}
