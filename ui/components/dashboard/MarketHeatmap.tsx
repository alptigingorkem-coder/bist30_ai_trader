"use client";

import { useMarketStore } from "@/store/marketStore";
import { ResponsiveContainer, Treemap, Tooltip } from "recharts";
import clsx from "clsx";

// Custom Content for Treemap Node
const CustomizedContent = (props: any) => {
    const { root, depth, x, y, width, height, index, name, change, price, symbol } = props;

    // Determine color based on change
    let bgColor = "#1e293b"; // global-gray
    let textColor = "#fff";

    if (change > 0) {
        // Green Scale
        if (change > 3) bgColor = "#14532d"; // dark green
        else if (change > 1) bgColor = "#15803d"; // green
        else bgColor = "#166534"; // light green
    } else if (change < 0) {
        // Red Scale
        if (change < -3) bgColor = "#7f1d1d"; // dark red
        else if (change < -1) bgColor = "#b91c1c"; // red
        else bgColor = "#991b1b"; // light red
    }

    return (
        <g>
            <rect
                x={x}
                y={y}
                width={width}
                height={height}
                style={{
                    fill: bgColor,
                    stroke: "#0f172a", // border color
                    strokeWidth: 2,
                    strokeOpacity: 1,
                }}
            />
            {width > 40 && height > 40 && (
                <foreignObject x={x} y={y} width={width} height={height}>
                    <div className="flex flex-col items-center justify-center w-full h-full p-1 overflow-hidden" title={`${name}: ${change}%`}>
                        <span className="font-bold text-white text-xs leading-none">{name}</span>
                        <span className="font-mono text-[10px] text-white/80 leading-none mt-1">{change}%</span>
                        {height > 60 && <span className="font-mono text-[9px] text-white/60 mt-1">₺{price}</span>}
                    </div>
                </foreignObject>
            )}
        </g>
    );
};

const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload;
        return (
            <div className="bg-slate-900 border border-slate-700 p-2 rounded shadow-xl text-xs">
                <div className="font-bold text-white mb-1">{data.name}</div>
                <div className="text-slate-400">Fiyat: <span className="text-white font-mono">₺{data.price}</span></div>
                <div className="text-slate-400">Değişim: <span className={data.change >= 0 ? "text-green-400" : "text-red-400"}>{data.change}%</span></div>
                <div className="text-slate-400">Hacim: <span className="text-white">{data.volume}</span></div>
            </div>
        );
    }
    return null;
};

export default function MarketHeatmap() {
    const { tickers } = useMarketStore();

    // Transform data for Treemap
    // Treemap needs 'name', 'size' (volume_raw), and custom props (change, price)
    const treeMapData = tickers.map(t => ({
        name: t.symbol,
        size: (t as any).volume_raw || 1000, // Fallback if raw not available yet
        change: t.change,
        price: t.price,
        volume: t.volume,
        symbol: t.symbol
    })).sort((a, b) => b.size - a.size); // Sort by size for better layout

    // Recharts Treemap requires a root object with children for correct rendering sometimes, 
    // or just an array. We'll try array first.

    return (
        <div className="w-full h-full min-h-[250px] bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
            <div className="px-4 py-3 border-b border-slate-800 flex justify-between items-center">
                <h3 className="font-display font-bold text-white text-sm">PİYASA HARİTASI (HACİM AĞIRLIKLI)</h3>
            </div>
            <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                    <Treemap
                        data={treeMapData}
                        dataKey="size"
                        stroke="#fff"
                        fill="#8884d8"
                        content={<CustomizedContent />}
                        aspectRatio={4 / 3}
                    >
                        <Tooltip content={<CustomTooltip />} />
                    </Treemap>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
