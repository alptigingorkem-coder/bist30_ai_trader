"use client";


import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { usePortfolioStore } from "@/store/portfolioStore";
import { useMarketStore } from "@/store/marketStore";

export default function AllocationChart() {
    const { cash, positions } = usePortfolioStore();
    const { tickers } = useMarketStore();

    // Calculate Values
    let stockValue = 0;
    Object.entries(positions).forEach(([symbol, pos]) => {
        const tickerData = tickers.find(t => t.symbol === symbol || t.symbol === symbol + ".IS");
        const price = tickerData ? tickerData.price : (pos.current_price || pos.entry_price);
        stockValue += pos.quantity * price;
    });

    const totalValue = cash + stockValue;
    const stockPct = totalValue > 0 ? Math.round((stockValue / totalValue) * 100) : 0;
    const cashPct = totalValue > 0 ? Math.round((cash / totalValue) * 100) : 100;

    const data = [
        { name: "Hisseler", value: stockPct, color: "#22c55e" },  // Green
        { name: "Nakit", value: cashPct, color: "#06b6d4" },    // Cyan
    ];

    return (
        <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/60 glass h-[350px] flex flex-col">
            <h3 className="font-display font-bold text-white mb-4">VARLIK DAĞILIMI</h3>

            <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={100}
                            paddingAngle={5}
                            dataKey="value"
                            stroke="none"
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Pie>
                        <Tooltip
                            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '12px' }}
                            itemStyle={{ color: '#ffffff', fontWeight: 'bold' }}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2">
                {data.map((entry) => (
                    <div key={entry.name} className="flex items-center gap-2 text-sm">
                        <span
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: entry.color }}
                        ></span>
                        <span className="text-slate-300">{entry.name}</span>
                        <span className="ml-auto font-bold text-white">{entry.value}%</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
