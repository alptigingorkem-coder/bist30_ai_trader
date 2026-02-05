"use client";

import PortfolioSummary from "@/components/portfolio/PortfolioSummary";
import PositionsTable from "@/components/portfolio/PositionsTable";
import AllocationChart from "@/components/portfolio/AllocationChart";
import RiskMetrics from "@/components/portfolio/RiskMetrics";
import { useEffect } from "react";
import { usePortfolioStore } from "@/store/portfolioStore";

export default function PortfolioPage() {
    const { fetchPortfolio } = usePortfolioStore();

    useEffect(() => {
        fetchPortfolio();
    }, []);

    return (
        <div className="flex flex-col gap-6 w-full h-full text-white overflow-y-auto pr-2">
            <div className="flex justify-between items-center mb-2">
                <h1 className="text-3xl font-display font-bold tracking-tight text-white/90">
                    PORTFÖYÜM
                </h1>
                <div className="text-xs font-mono text-gray-500">
                    HESAP: <span className="text-cyan-400 font-bold">CANLI-8842</span>
                </div>
            </div>

            {/* 1. Top Summary Cards */}
            <PortfolioSummary />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 2. Main Positions Table (2/3 width) */}
                <div className="lg:col-span-2">
                    <PositionsTable />
                </div>

                {/* 3. Right Sidebar: Allocation (1/3 width) */}
                <div className="flex flex-col gap-6">
                    <AllocationChart />
                </div>
            </div>

            {/* 4. Risk Metrics Section (Full Width) */}
            <RiskMetrics />
        </div>
    );
}
