import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import config
from core.risk_manager import RiskManager

class Backtester:
    def __init__(self, data, initial_capital=10000, commission=0.002):
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.commission = commission
        
    def calculate_slippage(self, volume, avg_volume, position_size_qty):
        """
        FIX 19: Gerçekçi slippage hesabı
        Eğer hacim bilgisi yoksa varsayılan sabit değer döner.
        """
        if pd.isna(volume) or pd.isna(avg_volume) or avg_volume == 0:
            return 0.001 # Varsayılan %0.1
            
        # Ortalama hacmin ne kadarlık kısmını alıyoruz?
        volume_impact = position_size_qty / avg_volume
        
        if volume_impact < 0.01:
            return 0.0002  # %0.02 (Limit emir varsayımı ile çok düşük)
        elif volume_impact < 0.05:
            return 0.0005   # %0.05
        else:
            return 0.001   # %0.1 normal slippage

    def apply_market_impact(self, price, size_qty, avg_volume, is_buy=True):
        """
        FIX 20: Büyük pozisyonlar fiyatı hareket ettirir.
        size: İşlem adedi
        avg_volume: Ortalama hacim
        """
        if pd.isna(avg_volume) or avg_volume == 0:
            return price
            
        volume_impact = size_qty / avg_volume
        
        # %10'dan büyük pozisyonlar fiyatı etkiler
        if volume_impact > 0.10:
            impact = (volume_impact - 0.10) * 0.001  # Her %10 için +%0.1 etki (Azaltıldı)
            
            if is_buy:
                return price * (1 + impact)  # Alırken fiyat yükselir
            else:
                return price * (1 - impact)  # Satarken fiyat düşer
                
        return price

    def run_backtest(self, signals_or_weights):
        """
        Event-driven Backtest with Risk Management.
        signals_or_weights: 
            - Series of 1/0 for Signals (All-in/All-out)
            - Series of floats (0.0-1.0) for Weights (Dynamic Sizing)
        """
        # Risk Yöneticisi
        risk_manager = RiskManager()
        
        # Veri boyutu kontrolü
        common_index = self.data.index.intersection(signals_or_weights.index)
        df = self.data.loc[common_index].copy()
        inputs = signals_or_weights.loc[common_index]
        
        # Input tipini belirle
        is_weighted = False
        if inputs.dtype == float:
            # Eğer float ve 0-1 arasındaysa weighted varsay
            if inputs.max() <= 1.0 and inputs.min() >= 0.0:
                 is_weighted = True
        
        # ATR verisi
        if 'ATR' not in df.columns:
            # print("UYARI: ATR sütunu bulunamadı, varsayılan volatilite kullanılacak.")
            df['ATR'] = np.nan
            
        # Rejim Verisi
        if 'Regime' not in df.columns:
            df['Regime'] = 'Trend_Up' # Varsayılan
        
        # Sonuç saklama
        positions = np.zeros(len(df)) # 1 (Long) or 0 (Flat) - or actual weight?
        # Ağırlıklı sistemde position = current_weight
        current_weights = np.zeros(len(df))
        
        trades = np.zeros(len(df))
        exit_reasons = [None] * len(df)
        
        # YENİ: Equity Tracking Array
        equities = np.zeros(len(df))
        equities[0] = self.initial_capital
        
        # Durum Değişkenleri
        in_position = False
        entry_price = 0.0
        entry_date = None
        peak_price = 0.0
        days_held = 0
        
        prices = df['Close'].values
        opens = df['Open'].values
        highs = df['High'].values
        lows = df['Low'].values
        atrs = df['ATR'].values
        regimes = df['Regime'].values
        dates = df.index
        input_values = inputs.values
        
        # Volume ve Avg Volume hazırlığı (Slippage için)
        volumes = df['Volume'].values if 'Volume' in df.columns else np.zeros(len(df))
        # Basit 20 günlük ortalama hacim (pandas 3.0 uyumlu)
        avg_volumes = df['Volume'].rolling(20).mean().bfill().values if 'Volume' in df.columns else np.zeros(len(df))
        
        # Equity Tracking
        equity = self.initial_capital
        cash = self.initial_capital
        holdings_value = 0.0
        holdings_qty = 0.0 # Lot sayısı
        
        peak_equity = equity
        circuit_breaker_triggered = False
        
        for i in range(1, len(df)):
            current_close = prices[i]
            current_open = opens[i]
            current_high = highs[i]
            current_low = lows[i]
            current_date = dates[i]
            current_atr = atrs[i]
            current_regime = regimes[i]
            input_val = input_values[i] # Signal (0/1) or Weight (0.0-1.0)
            
            # --- Valuation Update ---
            if holdings_qty > 0:
                holdings_value = holdings_qty * current_close
                in_position = True
            else:
                holdings_value = 0.0
                in_position = False
                
            equity = cash + holdings_value
            
            if equity > peak_equity: peak_equity = equity
            
            # Drawdown check
            dd = (equity - peak_equity) / peak_equity if peak_equity > 0 else 0
            
            if dd < -0.30 and not circuit_breaker_triggered:
                print(f"!!! CIRCUIT BREAKER TETİKLENDİ ({current_date.date()}) !!! Drawdown: {dd:.2%}. İşlemler durduruluyor.")
                # Force Sell
                if holdings_qty > 0:
                    trades[i] = 1
                    exit_reasons[i] = 'CIRCUIT_BREAKER'
                    # Sell at Open or Close? Panic -> Open
                    sell_price = current_open 
                    cash += holdings_qty * sell_price * (1 - self.commission)
                    holdings_qty = 0
                    holdings_value = 0
                
                circuit_breaker_triggered = True
                positions[i] = 0
                current_weights[i] = 0
                
                equity = cash # Update equity after sell
                equities[i] = equity 
                continue
                
            if circuit_breaker_triggered:
                 positions[i] = 0
                 current_weights[i] = 0
                 equities[i] = cash # Cash only
                 continue

            # Risk Parameters Update
            risk_manager.adjust_for_regime(current_regime)
            
            if np.isnan(current_atr):
                 current_atr = current_close * 0.03
            
            # --- DECISION LOGIC ---
            action = 'HOLD'
            target_qty = holdings_qty # Default: No change
            exit_reason = None
            
            # 1. RISK MANAGER CHECKS (Stop Loss / Take Profit)
            # Sadece pozisyondaysak kontrol et
            if in_position:
                days_held = (current_date - entry_date).days
                if current_high > peak_price: peak_price = current_high
                
                check_res, reason = risk_manager.check_exit_conditions(current_close, entry_price, peak_price, current_atr, days_held)
                
                # Check Intrabar Stops (Basic simulation)
                # ... (Existing logic simplified for weighted check)
                
                # Eğer Risk Manager SAT diyorsa, ağırlık sıfırlanır
                if check_res == 'SELL':
                    action = 'SELL'
                    exit_reason = reason
            
            # 2. SIGNAL / WEIGHT CHECK
            # Eğer Risk Manager HOLD dediyse, modelin sinyaline bak
            if action == 'HOLD':
                if is_weighted:
                    # Target Allocation
                    base_weight = input_val # 0.0 to 1.0 (Capital adjusted)
                    
                    # YENİ: Risk-Based Sizing Adjustment
                    if getattr(config, 'ENABLE_RISK_SIZING', False):
                        stop_dist = risk_manager.get_stop_distance(current_close, current_atr)
                        # Risk Weight = Risk_Per_Trade / Stop_Distance
                        # E.g. 0.02 / 0.10 = 0.20 weight
                        risk_weight = config.RISK_PER_TRADE / (stop_dist + 1e-6)
                        
                        # Ağırlığı risk limitine ve genel limite göre küçült
                        target_weight = min(base_weight, risk_weight, config.MAX_SINGLE_POS_WEIGHT)
                    else:
                        target_weight = base_weight

                    if target_weight < 0: target_weight = 0
                    if target_weight > 1: target_weight = 1 # No leverage
                    
                    target_value = equity * target_weight
                    target_qty_calc = target_value / current_close
                    
                    # Rebalancing Threshold (işlem maliyetini azaltmak için küçük değişimleri yapma)
                    qty_diff_pct = 0
                    if holdings_qty > 0:
                        qty_diff_pct = abs(target_qty_calc - holdings_qty) / holdings_qty
                    else:
                        qty_diff_pct = 1.0 if target_qty_calc > 0 else 0
                        
                    if qty_diff_pct > 0.10: # %10'dan fazla değişim varsa işlem yap
                        if target_qty_calc > holdings_qty:
                            action = 'BUY'
                            target_qty = target_qty_calc
                        elif target_qty_calc < holdings_qty:
                            # YENİ: Minimum Holding Days Check (Only for model-driven rebalance/sell)
                            min_holding = getattr(config, 'MIN_HOLDING_DAYS', 0)
                            if days_held >= min_holding:
                                # Kısmi satış veya tam satış
                                action = 'SELL' if target_qty_calc < (holdings_qty * 0.1) else 'REBALANCE_SELL'
                                target_qty = target_qty_calc
                                if action == 'SELL': exit_reason = 'WEIGHT_ZERO'
                            else:
                                # Henüz gün dolmadı, ağırlık değişimini reddet
                                action = 'HOLD'
                            
                else:
                    # Binary Signal
                    if input_val == 1 and not in_position:
                        action = 'BUY'
                        # All in
                        target_qty = (cash * 0.99) / current_close # %1 buffer for comms
                    elif input_val == 0 and in_position:
                        # Time based exit check (only if not stop loss)
                        if days_held >= risk_manager.min_holding_periods:
                             action = 'SELL'
                             exit_reason = 'SIGNAL_LOST'
                             target_qty = 0
            
            # --- EXECUTION ---
            # slippage = 0.001 # ESKİ SABİT
            
            # Dinamik Slippage için geçici (işlem anında hesaplanacak)
            current_volume = volumes[i]
            current_avg_vol = avg_volumes[i]
            
            if action == 'BUY' or action == 'REBALANCE_SELL': # FIX BUG-5: Rebalance logic enabled
                 # Calculate diff
                 diff_qty = target_qty - holdings_qty
                 
                 if diff_qty > 0: # BUY
                     # Slippage Hesabı (Alınacak miktar üzerinden)
                     slippage = self.calculate_slippage(current_volume, current_avg_vol, diff_qty)
                     
                     # FIX 20: Market Impact
                     executed_price = self.apply_market_impact(current_close, diff_qty, current_avg_vol, is_buy=True)
                     
                     cost = diff_qty * executed_price * (1 + slippage)
                     total_cost = cost * (1 + self.commission)
                     
                     if cash >= total_cost:
                         cash -= total_cost
                         holdings_qty += diff_qty
                         trades[i] = 1
                         
                         # FIX BUG-6: VWAP Entry Price for Scale-in
                         if in_position and holdings_qty > 0:
                             # Old total cost + New total cost / Total qty
                             # (Using executed_price for new part)
                             entry_price = (entry_price * (holdings_qty - diff_qty) + executed_price * diff_qty) / holdings_qty
                         else:
                             # Fresh entry
                             entry_price = executed_price # Use executed_price (slippage included)
                             entry_date = current_date
                             peak_price = current_close
                             
                 elif diff_qty < 0: # SELL
                     sell_qty = abs(diff_qty)
                     
                     # Slippage Hesabı (Satılacak miktar üzerinden)
                     slippage = self.calculate_slippage(current_volume, current_avg_vol, sell_qty)
                     
                     # FIX 20: Market Impact
                     executed_price = self.apply_market_impact(current_close, sell_qty, current_avg_vol, is_buy=False)
                     
                     proceeds = sell_qty * executed_price * (1 - slippage)
                     net_proceeds = proceeds * (1 - self.commission)
                     
                     cash += net_proceeds
                     holdings_qty -= sell_qty
                     trades[i] = 1
                     if holdings_qty < 1e-6: # Closed
                         holdings_qty = 0
                         in_position = False
                         exit_reasons[i] = exit_reason or 'REBALANCE'

            elif action == 'SELL': # Full Sell
                if holdings_qty > 0:
                     # Slippage Hesabı
                     slippage = self.calculate_slippage(current_volume, current_avg_vol, holdings_qty)
                     
                     # FIX 20: Market Impact
                     executed_price = self.apply_market_impact(current_close, holdings_qty, current_avg_vol, is_buy=False)
                     
                     proceeds = holdings_qty * executed_price * (1 - slippage)
                     net_proceeds = proceeds * (1 - self.commission)
                     
                     cash += net_proceeds
                     holdings_qty = 0
                     trades[i] = 1
                     in_position = False
                     exit_reasons[i] = exit_reason
            
            # Kayıt
            positions[i] = 1 if holdings_qty > 0 else 0
            # Update Equity after trades
            if holdings_qty > 0:
                holdings_value = holdings_qty * current_close
            else:
                holdings_value = 0.0
            
            equity = cash + holdings_value
            equities[i] = equity
            
            current_weights[i] = (holdings_qty * current_close) / equity if equity > 0 else 0
        
        # Sonuçları DataFrame'e yaz
        df['Position'] = positions
        df['Actual_Weight'] = current_weights # FIX BUG-2 part 1: Track actual weight
        df['Trades'] = trades 
        df['ExitReason'] = exit_reasons
        df['Equity'] = equities
        
        # Getiri Hesabı
        # FIX BUG-2 part 2: Strategy return should be based on prior day's WEIGHT, not binary position
        df['Strategy_Return_Gross'] = df['Actual_Weight'].shift(1).fillna(0) * df['Log_Return']
        
        # Maliyetler: Komisyon + Slippage
        # Komisyon her işlemde (Al/Sat)
        commission_cost = df['Trades'] * self.commission
        
        # Slippage her işlemde (Varsayılan %0.1)
        slippage_rate = 0.001
        slippage_cost = df['Trades'] * slippage_rate
        
        df['Transaction_Costs'] = commission_cost + slippage_cost
        
        # FIX BUG-3: Use Equity.pct_change() as the Source of Truth for returns.
        # This is the most robust way to calculate net daily returns for a ticker
        # because it captures all realized trades, costs, and mark-to-market.
        df['Net_Strategy_Return'] = df['Equity'].pct_change().fillna(0)
        
        df['Cumulative_Market_Return'] = (1 + df['Log_Return']).cumprod()
        df['Cumulative_Strategy_Return'] = (1 + df['Net_Strategy_Return']).cumprod()
        
        # Benchmark (XU100) Getirisi (Eğer veride varsa)
        if 'XU100' in df.columns:
            # XU100 getirisi hesapla
            df['XU100_Return'] = df['XU100'].pct_change().fillna(0)
            df['Cumulative_Benchmark_Return'] = (1 + df['XU100_Return']).cumprod()
            
            # İlk günleri normalize et (Backtest başlangıcında 1 olsun)
            # df['Cumulative_Benchmark_Return'] = df['Cumulative_Benchmark_Return'] / df['Cumulative_Benchmark_Return'].iloc[0]
        
        self.results = df
        return df
        
    def calculate_metrics(self):
        """Gelişmiş performans metriklerini hesaplar."""
        if not hasattr(self, 'results'):
            print("Önce run_backtest() çalıştırılmalı.")
            return None
            
        df = self.results
        returns = df['Net_Strategy_Return']
        
        # Temel Metrikler
        total_return = df['Cumulative_Strategy_Return'].iloc[-1] - 1

        # FIX-A1 / A3: daily_mean*252 yerine CAGR kullana.
        # Per-ticker çoğu gün pozisyonda olmadığında daily_mean sıfırla dilüte oluyordu
        # → yıllık getiri < risk_free → Sharpe zorunlu negatif çıkıyordu.
        # CAGR = (1 + total_return)^(252 / trading_days) - 1
        n_trading_days = max(len(returns), 1)
        annual_return = (1 + total_return) ** (252.0 / n_trading_days) - 1 if total_return > -1 else 0.0

        annual_volatility = returns.std() * np.sqrt(252)

        # FIX-A1: risk_free = 0  (per-ticker exposure-adjusted kontekst;
        # Türkiye risk-free %19-45 → anlamlı bir karşılaştırma yapılmaz)
        sharpe_ratio = annual_return / annual_volatility if annual_volatility > 0 else 0
        
        # Max Drawdown
        cum_ret = df['Cumulative_Strategy_Return']
        running_max = cum_ret.cummax()
        drawdown = (cum_ret - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Yeni Metrikler
        # Win Rate
        winning_trades = returns[returns > 0].count()
        losing_trades = returns[returns < 0].count()
        total_trades = df['Trades'].sum() # Toplam işlem sayısı (Al+Sat) yaklaşık 2 katı
        # Daha doğru trade sayısı: 0'dan 1'e veya 1'den 0'a geçişler
        num_round_trip_trades = df['Trades'].sum() / 2
        
        win_rate = winning_trades / (winning_trades + losing_trades) if (winning_trades + losing_trades) > 0 else 0
        
        # Profit Factor
        gross_profit = returns[returns > 0].sum()
        gross_loss = abs(returns[returns < 0].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calmar Ratio
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Sortino Ratio (Downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino_ratio = annual_return / downside_std if downside_std > 0 else 0
        
        metrics = {
            'Total Return': total_return,
            'CAGR': annual_return,              # FIX-A3: Standart yıllık getiri (CAGR)
            'Annual Return': annual_return,     # backward-compat alias
            'Volatility': annual_volatility,
            'Sharpe Ratio': sharpe_ratio,
            'Max Drawdown': max_drawdown,
            'Win Rate': win_rate,
            'Profit Factor': profit_factor,
            'Calmar Ratio': calmar_ratio,
            'Sortino Ratio': sortino_ratio,
            'Num Trades': num_round_trip_trades
        }
        
        return metrics

    def plot_results(self, filename='reports/backtest_results.png'):
        """Sonuçları görselleştirir."""
        import os
        if not hasattr(self, 'results'):
            return
            
        if not os.path.exists('reports'):
            os.makedirs('reports')
            
        plt.figure(figsize=(12, 6))
        plt.plot(self.results['Cumulative_Market_Return'], label='Hisse (Buy & Hold)', alpha=0.5, linestyle='--')
        plt.plot(self.results['Cumulative_Strategy_Return'], label='AI Stratejisi', linewidth=2, color='blue')
        
        if 'Cumulative_Benchmark_Return' in self.results.columns:
             plt.plot(self.results['Cumulative_Benchmark_Return'], label='XU100 Endeksi', alpha=0.7, color='orange')
             
        plt.title("Backtest Sonuçları: Strateji vs Market vs Benchmark")
        plt.legend()
        plt.grid(True)
        plt.savefig(filename)
        plt.close()

    def plot_drawdown(self, filename='reports/drawdown.png'):
        """Drawdown grafiğini çizer ve kaydeder."""
        import os
        if not hasattr(self, 'results') or self.results.empty:
            return
            
        if not os.path.exists('reports'):
            os.makedirs('reports')

        # Calculate drawdown if not already in results
        if 'Drawdown' not in self.results.columns:
            cum_ret = self.results['Cumulative_Strategy_Return']
            running_max = cum_ret.cummax()
            self.results['Drawdown'] = (cum_ret - running_max) / running_max
        
        plt.figure(figsize=(12, 6))
        plt.plot(self.results.index, self.results['Drawdown'], color='red')
        plt.fill_between(self.results.index, self.results['Drawdown'], 0, color='red', alpha=0.3)
        plt.title('Portfolio Drawdown')
        plt.xlabel('Date')
        plt.ylabel('Drawdown')
        plt.grid(True)
        plt.savefig(filename)
        plt.close()

    def plot_monthly_heatmap(self, filename='reports/monthly_heatmap.png'):
        """Aylık getiri ısı haritasını çizer."""
        import os
        import seaborn as sns
        if not hasattr(self, 'results') or self.results.empty:
            return
            
        if not os.path.exists('reports'):
            os.makedirs('reports')
        
        df = self.results.copy()
        df['Year'] = df.index.year
        df['Month'] = df.index.month
        
        # Aylık getirileri hesapla
        monthly_returns = df.groupby(['Year', 'Month'])['Net_Strategy_Return'].apply(lambda x: (1 + x).prod() - 1).unstack()
        
        plt.figure(figsize=(10, len(monthly_returns)/2 + 2))
        sns.heatmap(monthly_returns * 100, annot=True, fmt=".1f", cmap="RdYlGn", center=0, cbar_kws={'label': 'Return (%)'})
        plt.title("Monthly Returns (%)")
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()

    def save_trade_log(self, filename='trade_log.csv'):
        """İşlem geçmişini CSV olarak kaydeder."""
        if not hasattr(self, 'results'): return
        
        df = self.results
        # Trade giriş ve çıkışlarını filtrele
        # Position değişimi: 0->1 (Alış), 1->0 (Satış)
        df['Pos_Diff'] = df['Position'].diff()
        
        trades = []
        entry_date = None
        entry_price = 0
        
        for date, row in df.iterrows():
            if row['Pos_Diff'] == 1: # Alış
                entry_date = date
                entry_price = row['Close']
            elif row['Pos_Diff'] == -1: # Satış
                exit_date = date
                exit_price = row['Close']
                # Gross Return
                gross_pct = (exit_price - entry_price) / entry_price
                
                # Net Return (Approx: Gross - 2 * Commission - 2 * Slippage)
                # Slippage (0.1%) + Commission (self.commission)
                total_cost_pct = (self.commission + 0.001) * 2
                net_pct = gross_pct - total_cost_pct
                
                reason = row['ExitReason']
                
                trades.append({
                    'Entry Date': entry_date,
                    'Entry Price': entry_price,
                    'Exit Date': exit_date,
                    'Exit Price': exit_price,
                    'Gross Return': gross_pct,
                    'Net Return': net_pct,
                    'Reason': reason
                })
        
        if trades:
            pd.DataFrame(trades).to_csv(filename, index=False)

    def generate_html_report(self, filename='report.html', ticker="UNKNOWN"):
        """Tek sayfalık detaylı HTML rapor oluşturur."""
        if not hasattr(self, 'results'): return

        metrics = self.calculate_metrics()
        
        # Dosya isimlerini ticker'a özel yap (Overwrite'ı engellemek için)
        safe_ticker = ticker.replace('.', '_').replace(':', '')
        
        # Filenames (Full paths for saving)
        # Note: 'reports/' prefix is already assumed if plot methods use it, 
        # but better to be explicit here and pass it to plot methods.
        # But plot methods as I defined them default to 'reports/X.png'.
        # I should pass 'reports/X_ticker.png'.
        
        img_backtest = f"reports/backtest_results_{safe_ticker}.png"
        img_drawdown = f"reports/drawdown_{safe_ticker}.png"
        img_heatmap = f"reports/monthly_heatmap_{safe_ticker}.png"
        
        # Grafikleri oluştur
        self.plot_results(filename=img_backtest) # Need update plot_results to accept filename
        self.plot_drawdown(filename=img_drawdown)
        self.plot_monthly_heatmap(filename=img_heatmap)
        
        # HTML için sadece dosya adı (Relative path, aynı klasörde)
        # os.path.basename kullanabiliriz
        import os
        src_backtest = os.path.basename(img_backtest)
        src_drawdown = os.path.basename(img_drawdown)
        src_heatmap = os.path.basename(img_heatmap)
        
        # HTML Şablonu
        html_content = f"""
        <html>
        <head>
            <title>{ticker} Backtest Report</title>
            <style>
                body {{ font-family: monospace; padding: 20px; background-color: #f4f4f4; }}
                .container {{ background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); max-width: 1200px; margin: auto; }}
                h1, h2 {{ color: #333; }}
                .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
                .metric-box {{ background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 5px solid #007bff; }}
                .metric-title {{ font-size: 0.9em; color: #666; }}
                .metric-value {{ font-size: 1.4em; font-weight: bold; color: #333; }}
                .images {{ display: flex; flex-direction: column; gap: 20px; }}
                img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{ticker} AI Trader Backtest Report</h1>
                <p>Generated on: {pd.Timestamp.now()}</p>
                <hr>
                
                <h2>Performance Metrics</h2>
                <div class="metrics-grid">
        """
        
        for k, v in metrics.items():
            if isinstance(v, float):
                val_str = f"{v:.2f}" if abs(v) > 0.01 else f"{v:.4f}"
                if "Return" in k or "Drawdown" in k or "Rate" in k or "Volatility" in k: # Yüzdesel göster
                     val_str = f"{v*100:.2f}%"
            else:
                val_str = str(v)
                
            html_content += f"""
                    <div class="metric-box">
                        <div class="metric-title">{k}</div>
                        <div class="metric-value">{val_str}</div>
                    </div>
            """
            
        html_content += f"""
                </div>
                
                <h2>Equity Curve</h2>
                <div class="images">
                    <img src="{src_backtest}" alt="Equity Curve">
                    <img src="{src_drawdown}" alt="Drawdown">
                    <img src="{src_heatmap}" alt="Monthly Heatmap">
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

