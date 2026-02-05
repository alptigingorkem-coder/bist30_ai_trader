"use client";

import { useEffect } from "react";
import { useAlertStore } from "@/store/alertStore";
import { useMarketStore } from "@/store/marketStore";
import { Bell, X } from "lucide-react";
import clsx from "clsx";

export default function AlertToast() {
    const { triggeredAlerts, clearTriggered, checkAlerts } = useAlertStore();
    const { tickers } = useMarketStore();

    // Check alerts whenever prices update
    useEffect(() => {
        if (tickers.length === 0) return;

        const priceMap: Record<string, number> = {};
        tickers.forEach(t => {
            priceMap[t.symbol] = t.price;
        });

        checkAlerts(priceMap);
    }, [tickers]);

    if (triggeredAlerts.length === 0) return null;

    return (
        <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
            {triggeredAlerts.map((alert, idx) => (
                <div
                    key={alert.id}
                    className={clsx(
                        "flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl border animate-pulse",
                        alert.condition === 'above'
                            ? "bg-green-900/90 border-green-500/50"
                            : "bg-red-900/90 border-red-500/50"
                    )}
                >
                    <Bell size={18} className={alert.condition === 'above' ? "text-green-400" : "text-red-400"} />
                    <div>
                        <div className="text-white font-bold text-sm">
                            {alert.symbol} {alert.condition === 'above' ? '↑' : '↓'} ₺{alert.targetPrice}
                        </div>
                        <div className="text-xs text-white/70">
                            Alert triggered at {new Date(alert.triggeredAt || '').toLocaleTimeString()}
                        </div>
                    </div>
                    <button
                        onClick={clearTriggered}
                        className="ml-auto text-white/50 hover:text-white"
                    >
                        <X size={16} />
                    </button>
                </div>
            ))}
        </div>
    );
}
