import clsx from "clsx";
import { ArrowUp, ArrowDown, MoreHorizontal } from "lucide-react";


import { usePortfolioStore } from "@/store/portfolioStore";
import { useMarketStore } from "@/store/marketStore";

export default function PositionsTable() {
    const { positions } = usePortfolioStore();
    const { tickers } = useMarketStore(); // To get real-time prices

    // Convert positions dict to array with current prices
    const positionsList = Object.entries(positions).map(([symbol, pos]) => {
        // Find current market price
        const tickerData = tickers.find(t => t.symbol === symbol || t.symbol === symbol + ".IS");
        const currentPrice = tickerData ? tickerData.price : (pos.current_price || pos.entry_price);

        const marketValue = pos.quantity * currentPrice;
        const costBasis = pos.quantity * pos.entry_price;
        const pnl = marketValue - costBasis;
        const pnlPct = costBasis > 0 ? (pnl / costBasis) * 100 : 0;

        return {
            symbol,
            entry: pos.entry_price,
            current: currentPrice,
            quantity: pos.quantity,
            pnl,
            pnlPct,
            type: pos.side
        };
    });

    return (
        <div className="p-0 rounded-2xl border border-slate-800 bg-slate-900/60 glass overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center">
                <h3 className="font-display font-bold text-white tracking-wide">AÇIK POZİSYONLAR</h3>
                <button className="text-xs font-bold text-cyan-400 hover:text-cyan-300">GEÇMİŞİ GÖR</button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-slate-500 uppercase bg-slate-950/50">
                        <tr>
                            <th className="px-6 py-3">Hisse</th>
                            <th className="px-6 py-3">Yön</th>
                            <th className="px-6 py-3 text-right">Miktar</th>
                            <th className="px-6 py-3 text-right">Giriş Fiyatı</th>
                            <th className="px-6 py-3 text-right">Güncel Fiyat</th>
                            <th className="px-6 py-3 text-right">K/Z (₺)</th>
                            <th className="px-6 py-3 text-right">K/Z (%)</th>
                            <th className="px-6 py-3 text-center">İşlem</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/50">
                        {positionsList.map((pos) => (
                            <tr key={pos.symbol} className="hover:bg-slate-800/30 transition-colors group">
                                <td className="px-6 py-3 font-bold text-white">
                                    {pos.symbol}
                                    <span className="block text-[10px] text-slate-500 font-normal">BIST 30</span>
                                </td>
                                <td className="px-6 py-3">
                                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-green-500/10 text-green-400 border border-green-500/20">
                                        {pos.type}
                                    </span>
                                </td>
                                <td className="px-6 py-3 text-right font-mono text-slate-300">
                                    {pos.quantity.toLocaleString()}
                                </td>
                                <td className="px-6 py-3 text-right font-mono text-slate-400">
                                    {pos.entry.toFixed(2)}
                                </td>
                                <td className="px-6 py-3 text-right font-mono font-bold text-white">
                                    {pos.current.toFixed(2)}
                                </td>
                                <td className={clsx("px-6 py-3 text-right font-mono font-bold", pos.pnl >= 0 ? "text-green-400" : "text-red-400")}>
                                    {pos.pnl > 0 ? "+" : ""}{pos.pnl.toLocaleString()}
                                </td>
                                <td className="px-6 py-3 text-right">
                                    <div className={clsx("flex items-center justify-end gap-1 font-bold", pos.pnlPct >= 0 ? "text-green-400" : "text-red-400")}>
                                        {pos.pnlPct >= 0 ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
                                        {Math.abs(pos.pnlPct).toFixed(2)}%
                                    </div>
                                </td>
                                <td className="px-6 py-3 text-center">
                                    <button className="p-1 hover:bg-slate-700/50 rounded-lg text-slate-400 hover:text-white transition-colors">
                                        <MoreHorizontal size={16} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
