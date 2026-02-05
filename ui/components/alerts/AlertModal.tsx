"use client";

import { useState } from "react";
import { useAlertStore } from "@/store/alertStore";
import { useMarketStore } from "@/store/marketStore";
import { X, Bell } from "lucide-react";
import clsx from "clsx";

interface AlertModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function AlertModal({ isOpen, onClose }: AlertModalProps) {
    const { tickers } = useMarketStore();
    const { addAlert } = useAlertStore();

    const [symbol, setSymbol] = useState(tickers[0]?.symbol || "");
    const [condition, setCondition] = useState<'above' | 'below'>('above');
    const [targetPrice, setTargetPrice] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!symbol || !targetPrice) return;

        addAlert({
            symbol,
            condition,
            targetPrice: parseFloat(targetPrice),
        });

        // Reset & Close
        setTargetPrice("");
        onClose();
    };

    if (!isOpen) return null;

    const currentTickerPrice = tickers.find(t => t.symbol === symbol)?.price || 0;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
            <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md shadow-2xl">
                {/* Header */}
                <div className="flex justify-between items-center px-6 py-4 border-b border-slate-800">
                    <div className="flex items-center gap-2 text-white font-bold">
                        <Bell size={18} className="text-cyan-400" />
                        YENİ FİYAT ALARMI
                    </div>
                    <button onClick={onClose} className="text-slate-400 hover:text-white">
                        <X size={20} />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    {/* Symbol Select */}
                    <div>
                        <label className="block text-xs text-slate-400 mb-2">HİSSE</label>
                        <select
                            value={symbol}
                            onChange={(e) => setSymbol(e.target.value)}
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-500"
                        >
                            {tickers.map(t => (
                                <option key={t.symbol} value={t.symbol}>{t.symbol}</option>
                            ))}
                        </select>
                        <div className="text-xs text-slate-500 mt-1">
                            Mevcut Fiyat: <span className="text-white font-mono">{currentTickerPrice.toFixed(2)}</span>
                        </div>
                    </div>

                    {/* Condition */}
                    <div>
                        <label className="block text-xs text-slate-400 mb-2">KOŞUL</label>
                        <div className="flex gap-3">
                            <button
                                type="button"
                                onClick={() => setCondition('above')}
                                className={clsx(
                                    "flex-1 py-3 rounded-lg font-bold text-sm border transition-colors",
                                    condition === 'above'
                                        ? "bg-green-500/20 border-green-500/50 text-green-400"
                                        : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500"
                                )}
                            >
                                Fiyat Üstünde
                            </button>
                            <button
                                type="button"
                                onClick={() => setCondition('below')}
                                className={clsx(
                                    "flex-1 py-3 rounded-lg font-bold text-sm border transition-colors",
                                    condition === 'below'
                                        ? "bg-red-500/20 border-red-500/50 text-red-400"
                                        : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500"
                                )}
                            >
                                Fiyat Altında
                            </button>
                        </div>
                    </div>

                    {/* Target Price */}
                    <div>
                        <label className="block text-xs text-slate-400 mb-2">HEDEF FİYAT (₺)</label>
                        <input
                            type="number"
                            step="0.01"
                            value={targetPrice}
                            onChange={(e) => setTargetPrice(e.target.value)}
                            placeholder="Hedef fiyatı girin..."
                            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white font-mono focus:outline-none focus:border-cyan-500"
                        />
                    </div>

                    {/* Submit */}
                    <button
                        type="submit"
                        className="w-full py-3 rounded-lg bg-cyan-500 hover:bg-cyan-600 text-white font-bold transition-colors"
                    >
                        ALARM OLUŞTUR
                    </button>
                </form>
            </div>
        </div>
    );
}
