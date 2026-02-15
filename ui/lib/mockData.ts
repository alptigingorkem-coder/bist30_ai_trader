// Mock data generator for development/demo purposes
import { CandleData } from "@/store/marketStore";

export function generateMockData(): CandleData[] {
    const candles: CandleData[] = [];
    let basePrice = 50 + Math.random() * 100;
    const now = new Date();

    for (let i = 365; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);

        const open = basePrice + (Math.random() - 0.5) * 3;
        const close = open + (Math.random() - 0.5) * 4;
        const high = Math.max(open, close) + Math.random() * 2;
        const low = Math.min(open, close) - Math.random() * 2;
        const volume = Math.floor(Math.random() * 10000000);

        candles.push({
            time: date.toISOString().split("T")[0],
            open: parseFloat(open.toFixed(2)),
            high: parseFloat(high.toFixed(2)),
            low: parseFloat(low.toFixed(2)),
            close: parseFloat(close.toFixed(2)),
            volume,
        });

        basePrice = close;
    }

    return candles;
}
