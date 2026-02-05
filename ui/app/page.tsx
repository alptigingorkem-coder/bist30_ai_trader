"use client";

import { useEffect } from "react";
import dynamic from "next/dynamic";
import { useMarketStore } from "@/store/marketStore";
import { generateMockData } from "@/lib/mockData";
import { ArrowUp, ArrowDown } from "lucide-react";
import clsx from "clsx";
import AiConfidenceWidget from "@/components/dashboard/AiConfidenceWidget";
import SignalFeed from "@/components/dashboard/SignalFeed";
import MarketHeatmap from "@/components/dashboard/MarketHeatmap";

// Lazy Load Chart (CSR Only)
const TradingChart = dynamic(() => import("@/components/charts/TradingChart"), {
  ssr: false,
});

import Watchlist from "@/components/dashboard/Watchlist";

// ... existing imports

export default function Home() {
  const { tickers, selectedTicker, setTicker, connectWebSocket, isConnected } = useMarketStore();

  useEffect(() => {
    // Initial Load
    setTicker(selectedTicker);
    // Connect WS
    connectWebSocket();
  }, []);

  return (
    <div className="flex flex-col gap-4 w-full h-full text-white overflow-y-auto pb-6 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
      {/* 1. Header Bar */}
      <div className="flex justify-between items-center py-2 px-1 border-b border-slate-800/50 flex-shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-display font-bold tracking-tight text-white/90">
            PİYASA GÖRÜNÜMÜ
          </h1>
          <div className="h-4 w-px bg-slate-700"></div>
          <span className="text-sm font-display text-cyan-400 font-bold">{selectedTicker}</span>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-gray-500">
          <span className={clsx("flex items-center gap-1 transition-colors", isConnected ? "text-green-400" : "text-red-400")}>
            <span className={clsx("w-1.5 h-1.5 rounded-full animate-pulse", isConnected ? "bg-green-500" : "bg-red-500")}></span>
            {isConnected ? "CANLI" : "BAĞLANTI YOK"}
          </span>
          <span>{new Date().toLocaleDateString()}</span>
        </div>
      </div>

      {/* 2. Main Layout (Grid) */}
      <div className="grid grid-cols-12 gap-6 min-h-[600px]">

        {/* LEFT: Main Chart Area (8 cols) */}
        <div className="col-span-12 lg:col-span-9 flex flex-col gap-4 h-full">
          <div className="flex-1 rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden shadow-2xl min-h-[500px]">
            <TradingChart />
          </div>
          {/* Heatmap moved here for better layout balance */}
          <div className="h-[300px] w-full rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden">
            <MarketHeatmap />
          </div>

          {/* Bottom Info Bar */}
          <div className="h-10 rounded-lg border border-slate-800 bg-slate-900/40 flex items-center px-4 justify-between flex-shrink-0">
            <span className="text-xs text-slate-500">BIST 30 AI TRADER v3.0 // ACTIVE MODEL: ENSEMBLE // TIER-1</span>
            <span className="text-xs text-slate-500">H1 TIMEFRAME</span>
          </div>
        </div>

        {/* RIGHT: Sidebar (4 cols -> on large screens) */}
        <div className="col-span-12 lg:col-span-3 flex flex-col gap-4 h-full">
          {/* A. Watchlist */}
          <Watchlist />

          {/* B. AI Widget */}
          <AiConfidenceWidget />

          {/* C. Signals */}
          <SignalFeed />
        </div>
      </div>

    </div>
  );
}
