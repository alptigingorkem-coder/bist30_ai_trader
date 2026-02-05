import { create } from 'zustand';

export interface Alert {
    id: string;
    symbol: string;
    condition: 'above' | 'below';
    targetPrice: number;
    isActive: boolean;
    createdAt: string;
    triggeredAt?: string;
}

interface AlertState {
    alerts: Alert[];
    triggeredAlerts: Alert[];

    // Actions
    addAlert: (alert: Omit<Alert, 'id' | 'createdAt' | 'isActive'>) => void;
    removeAlert: (id: string) => void;
    triggerAlert: (id: string) => void;
    clearTriggered: () => void;
    checkAlerts: (prices: Record<string, number>) => void;
}

export const useAlertStore = create<AlertState>((set, get) => ({
    alerts: [],
    triggeredAlerts: [],

    addAlert: (alert) => {
        const newAlert: Alert = {
            ...alert,
            id: `alert_${Date.now()}`,
            createdAt: new Date().toISOString(),
            isActive: true,
        };
        set((state) => ({ alerts: [...state.alerts, newAlert] }));
    },

    removeAlert: (id) => {
        set((state) => ({ alerts: state.alerts.filter(a => a.id !== id) }));
    },

    triggerAlert: (id) => {
        set((state) => {
            const alert = state.alerts.find(a => a.id === id);
            if (!alert) return state;

            const updatedAlert = { ...alert, isActive: false, triggeredAt: new Date().toISOString() };
            return {
                alerts: state.alerts.map(a => a.id === id ? updatedAlert : a),
                triggeredAlerts: [...state.triggeredAlerts, updatedAlert]
            };
        });
    },

    clearTriggered: () => {
        set({ triggeredAlerts: [] });
    },

    checkAlerts: (prices) => {
        const { alerts, triggerAlert } = get();

        alerts.forEach(alert => {
            if (!alert.isActive) return;

            const currentPrice = prices[alert.symbol];
            if (currentPrice === undefined) return;

            let shouldTrigger = false;
            if (alert.condition === 'above' && currentPrice >= alert.targetPrice) {
                shouldTrigger = true;
            } else if (alert.condition === 'below' && currentPrice <= alert.targetPrice) {
                shouldTrigger = true;
            }

            if (shouldTrigger) {
                triggerAlert(alert.id);
            }
        });
    }
}));
