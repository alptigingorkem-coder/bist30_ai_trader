"use client";

import React, { useEffect, useRef, useState } from "react";
import {
    createChart,
    IChartApi,
    ISeriesApi,
    ColorType,
    CandlestickSeries,
    LineSeries,
    AreaSeries,
    SeriesMarker,
    Time,
} from "lightweight-charts";
import { useMarketStore, CandleData } from "@/store/marketStore";

interface PredictionData {
    forecast: { time: string, value: number, upper: number, lower: number }[];
    signals: { time: string, position: string, color: string, shape: string, text: string }[];
}

export default function TradingChart() {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
    const predictionLineRef = useRef<ISeriesApi<"Line"> | null>(null);
    const predictionBandRef = useRef<ISeriesApi<"Area"> | null>(null);

    const { candles, selectedTicker } = useMarketStore();
    const [predictions, setPredictions] = useState<PredictionData | null>(null);

    // Fetch predictions when ticker changes
    useEffect(() => {
        const fetchPredictions = async () => {
            try {
                const res = await fetch(`http://localhost:8000/api/predictions/${selectedTicker}`);
                if (res.ok) {
                    const data = await res.json();
                    setPredictions(data);
                }
            } catch (e) {
                console.error("Failed to fetch predictions:", e);
            }
        };
        fetchPredictions();
    }, [selectedTicker]);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        // Create Chart
        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
            layout: {
                background: { type: ColorType.Solid, color: "#111827" }, // surface color
                textColor: "#94a3b8", // slate-400
            },
            grid: {
                vertLines: { color: "#1e293b" }, // border color
                horzLines: { color: "#1e293b" },
            },
            timeScale: {
                borderColor: "#334155",
            },
        });

        // Add Candlestick Series
        const candleSeries = chart.addSeries(CandlestickSeries, {
            upColor: "#00c853", // bull green
            downColor: "#ef5350", // bear red
            borderVisible: false,
            wickUpColor: "#00c853",
            wickDownColor: "#ef5350",
        });

        // Add Prediction Line (Future Forecast)
        const predictionLine = chart.addSeries(LineSeries, {
            color: "#06b6d4", // cyan
            lineWidth: 2,
            lineStyle: 2, // Dashed
            priceLineVisible: false,
            lastValueVisible: true,
        });

        // Add Prediction Band (Confidence Interval) - Just upper for now, lower is harder with Area
        // We'll use a second line for lower, or fill between if supported
        const predictionBand = chart.addSeries(AreaSeries, {
            topColor: "rgba(6, 182, 212, 0.2)",
            bottomColor: "rgba(6, 182, 212, 0.02)",
            lineColor: "rgba(6, 182, 212, 0.6)",
            lineWidth: 1,
            priceLineVisible: false,
        });

        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;
        predictionLineRef.current = predictionLine;
        predictionBandRef.current = predictionBand;

        // Load Data
        if (candles.length > 0) {
            // @ts-ignore - lightweight-charts typing quirks
            candleSeries.setData(candles);
            chart.timeScale().fitContent();
        }

        // Resize Observer
        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                });
            }
        };
        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            chart.remove();
        };
    }, []);

    // Update Data on State Change
    useEffect(() => {
        if (candleSeriesRef.current && candles.length > 0) {
            // @ts-ignore
            candleSeriesRef.current.setData(candles);
            chartRef.current?.timeScale().fitContent();
        }
    }, [candles]);

    // Update Predictions Overlay
    useEffect(() => {
        if (!predictions || !predictionLineRef.current || !predictionBandRef.current || !candleSeriesRef.current) return;

        // 1. Set Prediction Line
        const forecastData = predictions.forecast.map(f => ({
            time: f.time as Time,
            value: f.value
        }));
        predictionLineRef.current.setData(forecastData);

        // 2. Set Prediction Band (Upper Bound)
        const bandData = predictions.forecast.map(f => ({
            time: f.time as Time,
            value: f.upper
        }));
        predictionBandRef.current.setData(bandData);

        // Note: Markers API changed in lightweight-charts v4+
        // Signals are displayed via the prediction line instead

    }, [predictions]);

    return (
        <div className="w-full h-full p-4 bg-[var(--color-dash-surface)] rounded-2xl border border-[var(--color-dash-border)] shadow-xl relative group">
            <div className="absolute top-6 left-6 z-10 text-white font-display text-sm flex items-center gap-3">
                <span>{selectedTicker} / TRY</span>
                <span className="text-gray-500 text-xs">1D</span>
                <span className="text-cyan-400 text-xs font-bold flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                    AI OVERLAY ACTIVE
                </span>
            </div>
            <div ref={chartContainerRef} className="w-full h-[400px] md:h-[600px]" />
        </div>
    );
}
