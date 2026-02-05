"use client";

import { Save, Server, Shield, Key } from "lucide-react";

export default function SettingsPage() {
    return (
        <div className="flex flex-col gap-6 w-full h-full text-white overflow-y-auto pr-2">
            <div className="flex justify-between items-center px-1">
                <h1 className="text-3xl font-display font-bold tracking-tight text-white/90">
                    SYSTEM SETTINGS
                </h1>
                <button className="flex items-center gap-2 px-6 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition-all shadow-lg shadow-cyan-500/20">
                    <Save size={18} />
                    SAVE CHANGES
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-6">

                {/* 1. Connection Settings */}
                <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 glass">
                    <h3 className="flex items-center gap-2 font-bold text-lg text-slate-200 mb-6 pb-4 border-b border-slate-800">
                        <Server className="text-cyan-400" size={20} />
                        CONNECTION CONFIG
                    </h3>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-bold text-slate-500 mb-2 uppercase">WebSocket Server URL</label>
                            <input
                                type="text"
                                defaultValue="ws://localhost:8000/ws"
                                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-sm font-mono focus:outline-none focus:border-cyan-500 transition-colors text-white"
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-bold text-slate-500 mb-2 uppercase">Reconnect Interval (ms)</label>
                                <input
                                    type="number"
                                    defaultValue="3000"
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-sm font-mono focus:outline-none focus:border-cyan-500 transition-colors text-white"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-slate-500 mb-2 uppercase">Max Retries</label>
                                <input
                                    type="number"
                                    defaultValue="5"
                                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-sm font-mono focus:outline-none focus:border-cyan-500 transition-colors text-white"
                                />
                            </div>
                        </div>

                        <div className="flex items-center gap-3 mt-2 p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                            <span className="text-xs font-bold text-green-400">System Connected</span>
                        </div>
                    </div>
                </div>

                {/* 2. Risk Management */}
                <div className="p-6 rounded-2xl border border-slate-800 bg-slate-900/60 glass">
                    <h3 className="flex items-center gap-2 font-bold text-lg text-slate-200 mb-6 pb-4 border-b border-slate-800">
                        <Shield className="text-red-400" size={20} />
                        RISK PARAMETERS
                    </h3>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-bold text-slate-500 mb-2 uppercase">Max Position Size (%)</label>
                            <div className="flex items-center gap-4">
                                <input type="range" min="1" max="20" defaultValue="5" className="flex-1 accent-cyan-500 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer" />
                                <span className="font-mono font-bold text-white w-12 text-right">5%</span>
                            </div>
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-slate-500 mb-2 uppercase">Daily Loss Limit (₺)</label>
                            <input
                                type="number"
                                defaultValue="50000"
                                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-sm font-mono focus:outline-none focus:border-cyan-500 transition-colors text-white"
                            />
                        </div>
                        <div className="flex items-center gap-3 py-2">
                            <input type="checkbox" defaultChecked className="w-4 h-4 rounded border-slate-700 bg-slate-900 accent-cyan-500" />
                            <span className="text-sm text-slate-300">Enable Kill-Switch (Auto-Liquidate)</span>
                        </div>
                    </div>
                </div>

                {/* 3. API Keys (Mock) */}
                <div className="lg:col-span-2 p-6 rounded-2xl border border-slate-800 bg-slate-900/60 glass">
                    <h3 className="flex items-center gap-2 font-bold text-lg text-slate-200 mb-6 pb-4 border-b border-slate-800">
                        <Key className="text-yellow-400" size={20} />
                        API INTEGRATIONS
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-xs font-bold text-slate-500 mb-2 uppercase">Data Provider Key</label>
                            <input
                                type="password"
                                defaultValue="sk_live_********************"
                                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-sm font-mono focus:outline-none focus:border-cyan-500 transition-colors text-white"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-slate-500 mb-2 uppercase">Broker API Secret</label>
                            <input
                                type="password"
                                defaultValue="********************************"
                                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-sm font-mono focus:outline-none focus:border-cyan-500 transition-colors text-white"
                            />
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
