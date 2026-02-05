import { ArrowUp, ArrowDown, DollarSign, Wallet, PieChart, Activity } from "lucide-react";
import clsx from "clsx";
import { usePortfolioStore } from "@/store/portfolioStore";

export default function PortfolioSummary() {
    const { cash, realized_pnl, positions } = usePortfolioStore();

    // Calculate Total Equity (Cash + Position Value) - simplified
    // Ideally we need market prices here, using entry price as fallback for now
    let positionValue = 0;
    Object.values(positions).forEach(p => {
        positionValue += p.quantity * (p.current_price || p.entry_price);
    });
    const totalBalance = cash + positionValue;
    const positionCount = Object.keys(positions).length;

    const metrics = [
        {
            label: "TOPLAM BAKİYE",
            value: `₺${totalBalance.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
            change: "Canlı",
            isPositive: true,
            icon: Wallet,
            color: "cyan"
        },
        {
            label: "GERÇEKLEŞEN K/Z",
            value: `₺${realized_pnl.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
            change: realized_pnl >= 0 ? "Kâr" : "Zarar",
            isPositive: realized_pnl >= 0,
            icon: Activity,
            color: realized_pnl >= 0 ? "green" : "red"
        },
        {
            label: "AÇIK POZİSYONLAR",
            value: positionCount.toString(),
            change: "Aktif",
            isPositive: true,
            icon: PieChart,
            color: "purple"
        },
        {
            label: "NAKİT",
            value: `₺${cash.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
            change: "Kullanılabilir",
            isPositive: true,
            icon: DollarSign,
            color: "yellow"
        }
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {metrics.map((metric, idx) => (
                <div key={idx} className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 glass group hover:bg-slate-800/60 transition-colors">
                    <div className="flex justify-between items-start mb-2">
                        <div className={`p-2 rounded-lg bg-${metric.color}-500/10 text-${metric.color}-400`}>
                            <metric.icon size={20} />
                        </div>
                        <div className={clsx("flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-full",
                            metric.isPositive ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"
                        )}>
                            {metric.isPositive ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
                            {metric.change}
                        </div>
                    </div>

                    <div className="mt-2">
                        <div className="text-slate-500 text-xs font-bold tracking-wider mb-1">{metric.label}</div>
                        <div className="text-2xl font-mono font-bold text-white tracking-tight">{metric.value}</div>
                    </div>

                    {/* Progress Bar for Margin or other metrics could go here */}
                    {metric.label === "KULLANILAN MARJ" && (
                        <div className="w-full h-1 bg-slate-800 rounded-full mt-3 overflow-hidden">
                            <div className="h-full bg-yellow-500/70 w-[65%]"></div>
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}
