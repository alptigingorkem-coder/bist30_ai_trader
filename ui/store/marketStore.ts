import { create } from 'zustand';
import { usePortfolioStore } from './portfolioStore';

export interface CandleData {
    time: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
}

interface TickerData {
    symbol: string;
    price: number;
    change: number;
    volume: string;
    timestamp?: string;
}

interface MarketState {
    isConnected: boolean;
    selectedTicker: string;
    tickerData: TickerData[];
    candles: CandleData[];
    tickers: TickerData[];
    socket: WebSocket | null;

    setTicker: (ticker: string) => Promise<void>;
    connectWebSocket: () => void;
    disconnectWebSocket: () => void;
}

const DEFAULT_TICKERS = [
    "AKBNK", "ALARK", "ASELS", "ASTOR", "BIMAS",
    "EKGYO", "ENKAI", "EREGL", "FROTO", "GARAN",
    "GUBRF", "HEKTS", "ISCTR", "KCHOL", "KONTR",
    "KRDMD", "ODAS", "OYAKC", "PETKM",
    "PGSUS", "SAHOL", "SASA", "SISE", "TAVHL",
    "TCELL", "THYAO", "TOASO", "TSKB", "TTKOM",
    "TUPRS", "YKBNK", "XU100"
];

export const useMarketStore = create<MarketState>((set, get) => ({
    isConnected: false,
    selectedTicker: 'XU100',
    tickerData: [],
    candles: [],
    tickers: DEFAULT_TICKERS.map(t => ({ symbol: t, price: 0, change: 0, volume: "0M" })),
    socket: null,

    setTicker: async (ticker: string) => {
        set({ selectedTicker: ticker });

        // Fetch historical data from API
        try {
            const res = await fetch(`http://localhost:8000/api/market-data/${ticker}`);
            if (res.ok) {
                const data = await res.json();
                if (Array.isArray(data)) {
                    set({ candles: data });
                }
            }
        } catch (e) {
            console.error("Failed to fetch history:", e);
        }
    },

    connectWebSocket: () => {
        if (get().isConnected) return;

        let wsV: WebSocket;
        try {
            wsV = new WebSocket('ws://localhost:8000/ws');
        } catch (err) {
            console.error("WS Create Error", err);
            return;
        }

        wsV.onopen = () => {
            console.log('✅ WebSocket Connected');
            set({ isConnected: true, socket: wsV });

            // Ping to keep alive
            setInterval(() => {
                if (wsV.readyState === WebSocket.OPEN) {
                    wsV.send('ping');
                }
            }, 5000);
        };

        wsV.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);

                // 1. Market Data Update (Array of tickers)
                if (message.type === 'MARKET_UPDATE') {
                    set({ tickers: message.data });
                }

                // 2. Portfolio Update -> Forward to Portfolio Store
                if (message.type === 'PORTFOLIO_UPDATE') {
                    usePortfolioStore.getState().updateFromSocket(message.data);
                }

            } catch (e) {
                console.error('WebSocket Parse Error:', e);
            }
        };

        wsV.onclose = () => {
            console.log('❌ WebSocket Disconnected');
            set({ isConnected: false, socket: null });
            // Reconnect logic
            setTimeout(() => get().connectWebSocket(), 3000);
        };
    },

    disconnectWebSocket: () => {
        const { socket } = get();
        if (socket) {
            socket.close();
            set({ isConnected: false, socket: null });
        }
    }
}));

