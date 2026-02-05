import { create } from 'zustand';

interface Position {
    side: "LONG" | "SHORT";
    entry_price: number;
    quantity: number;
    entry_time: string;
    current_price?: number;
    entry_confidence?: number;
    entry_regime?: string;
}

interface PortfolioState {
    cash: number;
    positions: Record<string, Position>;
    realized_pnl: number;
    trade_history: any[];
    closed_trades: any[];
    isLoading: boolean;
    error: string | null;

    // Actions
    fetchPortfolio: () => Promise<void>;
    updateFromSocket: (data: any) => void;

    // Computed Helpers
    getTotalValue: (marketPrices: Record<string, number>) => number;
    getOpenPositionsList: (marketPrices: Record<string, number>) => any[];
}

export const usePortfolioStore = create<PortfolioState>((set, get) => ({
    cash: 100000,
    positions: {},
    realized_pnl: 0,
    trade_history: [],
    closed_trades: [],
    isLoading: false,
    error: null,

    fetchPortfolio: async () => {
        set({ isLoading: true });
        try {
            const res = await fetch('http://localhost:8000/api/portfolio');
            if (!res.ok) throw new Error("Failed to fetch portfolio");
            const data = await res.json();
            set({
                cash: data.cash,
                positions: data.positions || {},
                realized_pnl: data.realized_pnl,
                trade_history: data.trade_history || [],
                closed_trades: data.closed_trades || [],
                isLoading: false
            });
        } catch (err: any) {
            console.error(err);
            set({ error: err.message, isLoading: false });
        }
    },

    updateFromSocket: (data: any) => {
        // Data format matches PortfolioState struct from backend
        set({
            cash: data.cash,
            positions: data.positions || {},
            realized_pnl: data.realized_pnl,
            trade_history: data.trade_history || [],
            closed_trades: data.closed_trades || []
        });
    },

    getTotalValue: (marketPrices) => {
        const { cash, positions } = get();
        let equity = cash;

        Object.entries(positions).forEach(([symbol, pos]) => {
            const currentPrice = marketPrices[symbol] || pos.entry_price; // Fallback to entry
            equity += pos.quantity * currentPrice;
        });

        return equity;
    },

    getOpenPositionsList: (marketPrices) => {
        const { positions } = get();
        return Object.entries(positions).map(([symbol, pos]) => {
            const currentPrice = marketPrices[symbol] || pos.entry_price;
            const marketValue = pos.quantity * currentPrice;
            const costBasis = pos.quantity * pos.entry_price;
            const pnl = marketValue - costBasis;
            const pnlPct = (pnl / costBasis) * 100;

            return {
                symbol,
                side: pos.side,
                quantity: pos.quantity,
                entry: pos.entry_price,
                current: currentPrice,
                pnl,
                pnlPct
            };
        });
    }
}));
