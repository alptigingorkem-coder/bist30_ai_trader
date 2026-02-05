"use client";

import { useEffect, useState } from "react";
import { Activity, Wifi, AlertTriangle, Server, Database } from "lucide-react";
import clsx from "clsx";

interface HeaderState {
    status: "CONNECTING" | "OK" | "WARNING" | "CRITICAL";
    source: string;
    message: string;
    ping: number;
}

export default function HealthMonitor() {
    const [state, setState] = useState<HeaderState>({
        status: "CONNECTING",
        source: "-",
        message: "Sunucuya bağlanılıyor...",
        ping: 0
    });

    // Durum metnini Türkçeleştir
    const getStatusLabel = (status: HeaderState["status"]) => {
        switch (status) {
            case "OK": return "CANLI";
            case "WARNING": return "ÖNBELLEK";
            case "CRITICAL": return "HATA";
            default: return "BAĞLANIYOR";
        }
    };

    useEffect(() => {
        let ws: WebSocket;
        let keepAliveInterval: NodeJS.Timeout;

        const connect = () => {
            ws = new WebSocket("ws://localhost:8000/ws");
            const startTime = Date.now();

            ws.onopen = () => {
                setState(prev => ({ ...prev, status: "OK", message: "Bağlantı başarılı", ping: Date.now() - startTime }));

                // Keep-alive
                keepAliveInterval = setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) ws.send("ping");
                }, 30000);
            };

            ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);

                    if (msg.type === "MARKET_UPDATE") {
                        // Backend'den gelen: { type, status, source, data }
                        const isCache = msg.source && msg.source.includes("Cache");
                        const isError = msg.status === "ERROR" || msg.status === "CRITICAL";

                        let status: HeaderState["status"] = "OK";
                        if (isError) status = "CRITICAL";
                        else if (isCache) status = "WARNING";

                        setState({
                            status: status,
                            source: msg.source || "Bilinmiyor",
                            message: isCache ? "Önbellek Verisi Kullanılıyor" : "Canlı Piyasa Verisi",
                            ping: 0 // Anlık update sıklığına göre belki hesaplanır ama şimdilik 0
                        });
                    } else if (msg.type === "MARKET_CRITICAL_ERROR") {
                        setState({
                            status: "CRITICAL",
                            source: "YOK",
                            message: msg.error || "KRİTİK VERİ HATASI",
                            ping: 0
                        });
                    }
                } catch (e) {
                    console.error("WS Parse Error", e);
                }
            };

            ws.onclose = () => {
                setState({ status: "CRITICAL", source: "-", message: "Sunucu bağlantısı koptu", ping: 0 });
                clearInterval(keepAliveInterval);
                setTimeout(connect, 3000); // Reconnect
            };

            ws.onerror = () => {
                // Close handle eder
            };
        };

        connect();

        return () => {
            if (ws) ws.close();
            if (keepAliveInterval) clearInterval(keepAliveInterval);
        };
    }, []);

    // Renk ve İkon Belirleme
    const getStatusConfig = () => {
        switch (state.status) {
            case "OK":
                return { color: "text-green-400", bg: "bg-green-500/10", border: "border-green-500/20", icon: Wifi };
            case "WARNING":
                return { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20", icon: Database };
            case "CRITICAL":
                return { color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20", icon: AlertTriangle };
            default:
                return { color: "text-slate-400", bg: "bg-slate-800/50", border: "border-slate-700", icon: Activity };
        }
    };

    const config = getStatusConfig();
    const Icon = config.icon;

    return (
        <div className={clsx(
            "flex items-center gap-3 px-4 py-2 rounded-full border backdrop-blur-md transition-all duration-500",
            config.bg, config.border
        )}>
            <div className={clsx("relative flex items-center justify-center", config.color)}>
                <Icon size={16} />
                {/* Pulse Effect for OK/WARNING */}
                {(state.status === "OK" || state.status === "WARNING") && (
                    <span className={clsx("absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping",
                        state.status === "OK" ? "bg-green-400" : "bg-amber-400"
                    )}></span>
                )}
            </div>

            <div className="flex flex-col">
                <span className={clsx("text-xs font-bold leading-none tracking-wider", config.color)}>
                    SİSTEM DURUMU: {getStatusLabel(state.status)}
                </span>
                <span className="text-[10px] text-slate-400 font-mono leading-tight mt-0.5">
                    KAYNAK: {state.source}
                </span>
            </div>

            {state.status === "CRITICAL" && (
                <div className="ml-2 px-2 py-0.5 rounded bg-red-500 text-white text-[10px] font-bold animate-pulse">
                    İŞLEM YOK
                </div>
            )}
        </div>
    );
}
