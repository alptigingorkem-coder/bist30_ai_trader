"use client";

import clsx from "clsx";
import { Newspaper, TrendingUp, TrendingDown, Minus, ExternalLink } from "lucide-react";

interface NewsItem {
    id: number;
    title: string;
    source: string;
    time: string;
    tickers: string[];
    sentiment: "POSITIVE" | "NEGATIVE" | "NEUTRAL";
    impact_score: number; // 0-100 impact
}

export default function NewsCard({ news }: { news: NewsItem }) {

    return (
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 glass hover:bg-slate-800/60 transition-all group group-hover:border-slate-700">
            <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-500">
                    <Newspaper size={14} />
                    <span>{news.source}</span>
                    <span>•</span>
                    <span>{news.time}</span>
                </div>

                {/* Sentiment Badge */}
                <div className={clsx("flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-lg border",
                    news.sentiment === "POSITIVE" ? "bg-green-500/10 text-green-400 border-green-500/20" :
                        news.sentiment === "NEGATIVE" ? "bg-red-500/10 text-red-400 border-red-500/20" :
                            "bg-slate-800 text-slate-400 border-slate-700"
                )}>
                    {news.sentiment === "POSITIVE" ? <TrendingUp size={12} /> :
                        news.sentiment === "NEGATIVE" ? <TrendingDown size={12} /> :
                            <Minus size={12} />}
                    {news.sentiment}
                </div>
            </div>

            <h3 className="text-white font-display font-medium leading-snug mb-3 group-hover:text-cyan-400 transition-colors">
                {news.title}
            </h3>

            <div className="flex justify-between items-center">
                <div className="flex gap-2">
                    {news.tickers.map(t => (
                        <span key={t} className="text-xs font-mono font-bold text-cyan-500 bg-cyan-950/30 px-1.5 py-0.5 rounded border border-cyan-900/50">
                            ${t}
                        </span>
                    ))}
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">AI Impact</span>
                    <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div
                            className={clsx("h-full rounded-full",
                                news.sentiment === "POSITIVE" ? "bg-green-500" :
                                    news.sentiment === "NEGATIVE" ? "bg-red-500" : "bg-slate-500"
                            )}
                            style={{ width: `${news.impact_score}%` }}
                        ></div>
                    </div>
                </div>
            </div>
        </div>
    );
}
