"use client";

import { useEffect } from "react";
import StockScreener from "@/components/market/StockScreener";
import { useMarketStore } from "@/store/marketStore";
import dynamic from "next/dynamic";

const TradingChart = dynamic(() => import("@/components/charts/TradingChart"), {
    ssr: false,
});

export default function MarketPage() {
    const { connectWebSocket, setTicker, selectedTicker } = useMarketStore();

    useEffect(() => {
        connectWebSocket();
        setTicker(selectedTicker); // Load chart data
    }, []);

    return (
        <div className="flex flex-col lg:flex-row gap-6 w-full h-full text-white overflow-hidden">
            {/* Left: Screener */}
            <div className="w-full lg:w-80 h-full min-h-[500px] lg:min-h-0 flex-shrink-0">
                <StockScreener />
            </div>

            {/* Right: Chart & Details */}
            <div className="flex-1 flex flex-col gap-6 min-h-0 overflow-y-auto">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <h1 className="text-3xl font-display font-bold tracking-tight text-white/90">
                        PİYASA
                    </h1>
                    <div className="text-xs font-mono text-slate-500">
                        {new Date().toLocaleDateString()} • CANLI VERİ
                    </div>
                </div>

                {/* Chart */}
                <div className="flex-1 min-h-[400px]">
                    <TradingChart />
                </div>
            </div>
        </div>
    );
}
