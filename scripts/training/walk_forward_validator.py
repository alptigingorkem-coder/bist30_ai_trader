"""
WalkForwardValidator: Class for walk-forward validation with model retraining.

This module implements walk-forward validation by extracting data loading,
model training, prediction, and result calculation into separate methods.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

import config
from utils.data_loader import DataLoader
from utils.feature_engineering import FeatureEngineer
from core.backtesting import Backtester


class WalkForwardValidator:
    """
    Manages walk-forward validation with model retraining.
    
    This class orchestrates the complete walk-forward validation workflow:
    1. Data loading and feature engineering
    2. Window-based train/test splitting
    3. Model training on each window
    4. Prediction and portfolio construction
    5. Performance calculation and reporting
    """
    
    def __init__(self, start_date: str = "2018-01-01", end_date: str = "2026-02-14"):
        """Initialize validator with date range."""
        self.start_date = start_date
        self.end_date = end_date
        self.full_data = None
        self.results = []
        
    def run(self, window_index: Optional[int] = None) -> Tuple[Optional[pd.DataFrame], float, float]:
        """
        Execute complete walk-forward validation.
        
        Args:
            window_index: Optional specific window to run (1-based)
            
        Returns:
            Tuple of (results DataFrame, average Sharpe, Sharpe std)
        """
        print("="*70)
        print("WALK-FORWARD VALIDATION (Gerçek Model)")
        print("="*70)
        print("\nHer pencerede LightGBM modeli yeniden eğitilir ve test edilir.")
        print("Bu, gerçek Out-of-Sample (OOS) performansı ölçer.")
        print("="*70)
        
        # Load and prepare data
        if not self._load_and_prepare_data():
            return None, 0, 0
        
        # Define windows
        windows = self._define_windows()
        
        # Filter to specific window if requested
        if window_index is not None:
            windows = [windows[window_index - 1]]
            print(f"🎯 Running only Window {window_index}: {windows[0]['name']}")
        
        # Run validation for each window
        for i, window in enumerate(windows, 1):
            result = self._validate_window(i, window)
            self.results.append(result)
        
        # Generate summary
        return self._generate_summary()
    
    def _load_and_prepare_data(self) -> bool:
        """Load data and perform feature engineering."""
        print("\n📥 Tam veri yükleniyor...")
        
        # Load raw data
        data_map = self._load_raw_data()
        if not data_map:
            print("❌ Veri yüklenemedi!")
            return False
        
        # Feature engineering
        processed_dfs = self._process_features(data_map)
        if not processed_dfs:
            print("❌ Feature engineering başarısız!")
            return False
        
        # Combine and prepare
        self.full_data = self._combine_data(processed_dfs)
        
        print(f"📊 Toplam veri: {len(self.full_data)} satır, "
              f"{self.full_data.index.get_level_values('Ticker').nunique()} hisse")
        
        return True
    
    def _load_raw_data(self) -> Dict[str, pd.DataFrame]:
        """Load raw stock data for all tickers."""
        loader = DataLoader()
        tickers = getattr(config, 'BIST30_TICKERS', config.TICKERS)
        
        data_map = {}
        print(f"   Fetching for {len(tickers)} tickers...")
        
        for ticker in tickers:
            try:
                df = loader.fetch_stock_data(ticker)
                if df is not None and not df.empty:
                    df = df[(df.index >= self.start_date) & (df.index <= self.end_date)]
                    if len(df) > 0:
                        data_map[ticker] = df
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
        
        return data_map
    
    def _process_features(self, data_map: Dict[str, pd.DataFrame]) -> List[pd.DataFrame]:
        """Process features for all tickers."""
        print("🔧 Feature'lar hesaplanıyor...")
        
        processed_dfs = []
        for ticker, df in data_map.items():
            try:
                fe = FeatureEngineer(df)
                processed = fe.process_all(ticker=ticker)
                processed['Ticker'] = ticker
                processed_dfs.append(processed)
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
        
        return processed_dfs
    
    def _combine_data(self, processed_dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """Combine processed dataframes into single indexed dataframe."""
        full_data = pd.concat(processed_dfs)
        full_data = full_data.reset_index()
        
        if 'Date' not in full_data.columns:
            full_data.rename(columns={'index': 'Date'}, inplace=True)
        
        full_data['Date'] = pd.to_datetime(full_data['Date'])
        full_data = full_data.set_index(['Date', 'Ticker']).sort_index()
        
        return full_data
    
    def _define_windows(self) -> List[Dict]:
        """Define walk-forward validation windows."""
        return [
            {
                'name': '2020 (COVID)',
                'train': ('2018-01-01', '2019-12-31'),
                'test': ('2020-01-01', '2020-12-31')
            },
            {
                'name': '2021 (Toparlanma)',
                'train': ('2019-01-01', '2020-12-31'),
                'test': ('2021-01-01', '2021-12-31')
            },
            {
                'name': '2022 (Faiz Artışları)',
                'train': ('2020-01-01', '2021-12-31'),
                'test': ('2022-01-01', '2022-12-31')
            },
            {
                'name': '2023 (Geçiş)',
                'train': ('2021-01-01', '2022-12-31'),
                'test': ('2023-01-01', '2023-12-31')
            },
            {
                'name': '2024 (Enflasyon Rallisi)',
                'train': ('2022-01-01', '2023-12-31'),
                'test': ('2024-01-01', '2024-12-31')
            },
            {
                'name': '2025 (Güncel)',
                'train': ('2023-01-01', '2024-12-31'),
                'test': ('2025-01-01', '2026-02-14')
            }
        ]
    
    def _validate_window(self, window_num: int, window: Dict) -> Dict:
        """Validate a single window."""
        print(f"\n{'='*70}")
        print(f"PENCERE {window_num}: {window['name']}")
        print(f"{'='*70}")
        print(f"Train: {window['train'][0]} → {window['train'][1]}")
        print(f"Test:  {window['test'][0]} → {window['test'][1]}")
        
        # Split data
        train_slice, test_slice = self._split_window_data(window)
        
        if train_slice is None or test_slice is None:
            return self._create_empty_result(window_num, window)
        
        # Check data sufficiency
        if len(train_slice) < 100 or len(test_slice) < 20:
            print(f"⚠️  Yetersiz veri (Train: {len(train_slice)}, Test: {len(test_slice)})")
            return self._create_empty_result(window_num, window)
        
        print(f"📊 Train: {len(train_slice)} satır, Test: {len(test_slice)} satır")
        
        # Train model
        model = self._train_model(train_slice)
        
        if model is None:
            # Fallback strategy
            return self._run_fallback_strategy(window_num, window, test_slice)
        
        # Generate predictions and calculate metrics
        return self._calculate_window_metrics(window_num, window, model, test_slice)
    
    def _split_window_data(self, window: Dict) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Split data into train and test for a window."""
        try:
            idx = pd.IndexSlice
            train_slice = self.full_data.loc[idx[window['train'][0]:window['train'][1], :], :]
            test_slice = self.full_data.loc[idx[window['test'][0]:window['test'][1], :], :]
            return train_slice, test_slice
        except KeyError:
            print("⚠️  Veri yok.")
            return None, None
    
    def _train_model(self, train_data: pd.DataFrame):
        """Train model on training data."""
        print("🧠 LightGBM modeli eğitiliyor...")
        
        try:
            from models.ranking_model import RankingModel
            from configs import banking as sector_config
            
            ranker = RankingModel(train_data, sector_config)
            ranker.train()
            
            print("✅ Model eğitildi")
            return ranker
            
        except Exception as e:
            print(f"❌ Model eğitim hatası: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _calculate_window_metrics(
        self, window_num: int, window: Dict, model, test_data: pd.DataFrame
    ) -> Dict:
        """Calculate performance metrics for a window."""
        print("📈 Test periyodunda tahminler alınıyor...")
        
        try:
            # Get daily predictions
            daily_returns = self._generate_daily_predictions(model, test_data)
            
            if not daily_returns:
                print("⚠️  Hiç trade yapılamadı.")
                return self._create_empty_result(window_num, window)
            
            # Calculate metrics
            metrics = self._calculate_metrics(daily_returns)
            
            result = {
                'window': window_num,
                'name': window['name'],
                'test_period': f"{window['test'][0]} → {window['test'][1]}",
                **metrics
            }
            
            self._print_window_results(result)
            return result
            
        except Exception as e:
            print(f"❌ Tahmin hatası: {e}")
            import traceback
            traceback.print_exc()
            return self._create_empty_result(window_num, window)
    
    def _generate_daily_predictions(self, model, test_data: pd.DataFrame) -> List[float]:
        """Generate daily predictions and returns."""
        unique_dates = test_data.index.get_level_values('Date').unique().sort_values()
        port_size = getattr(config, 'PORTFOLIO_SIZE', 5)
        
        all_daily_returns = []
        
        for date in unique_dates:
            try:
                day_data = test_data.xs(date, level='Date')
                if len(day_data) < port_size:
                    continue
                
                # Model prediction
                scores = model.predict(day_data)
                if scores is None or len(scores) == 0:
                    continue
                
                # Select top-N
                score_series = pd.Series(scores, index=day_data.index)
                top_tickers = score_series.nlargest(port_size).index
                
                # Calculate daily return
                daily_ret = self._calculate_daily_return(day_data, top_tickers)
                if daily_ret is not None:
                    all_daily_returns.append(daily_ret)
                    
            except Exception:
                continue
        
        return all_daily_returns
    
    def _calculate_daily_return(self, day_data: pd.DataFrame, top_tickers) -> Optional[float]:
        """Calculate daily return for selected tickers."""
        # Try different return columns
        for col in ['Excess_Return', 'NextDay_Return']:
            if col in day_data.columns:
                selected_returns = day_data.loc[top_tickers, col]
                valid_returns = selected_returns.dropna()
                if len(valid_returns) > 0:
                    return valid_returns.mean()
        
        # Fallback to price change
        selected_returns = day_data.loc[top_tickers, 'Close'].pct_change().fillna(0)
        valid_returns = selected_returns.dropna()
        return valid_returns.mean() if len(valid_returns) > 0 else None
    
    def _calculate_metrics(self, daily_returns: List[float]) -> Dict:
        """Calculate performance metrics from daily returns."""
        daily_rets = np.array(daily_returns)
        cum_ret = np.cumprod(1 + daily_rets)
        
        # Total return
        total_return = cum_ret[-1] - 1
        
        # Sharpe ratio
        sharpe = 0
        if daily_rets.std() > 1e-6:
            sharpe = np.sqrt(252) * daily_rets.mean() / daily_rets.std()
        
        # Max drawdown
        peak = np.maximum.accumulate(cum_ret)
        dd = (cum_ret - peak) / peak
        max_dd = dd.min()
        
        # Win rate
        wins = np.sum(daily_rets > 0)
        total_trades = len(daily_rets)
        win_rate = wins / total_trades if total_trades > 0 else 0
        
        return {
            'sharpe': sharpe,
            'total_return': total_return,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'total_trades': total_trades
        }
    
    def _run_fallback_strategy(
        self, window_num: int, window: Dict, test_data: pd.DataFrame
    ) -> Dict:
        """Run RSI-based fallback strategy."""
        print("⚡ Fallback: RSI stratejisi kullanılıyor...")
        
        unique_tickers = test_data.index.get_level_values('Ticker').unique()
        all_daily_returns = []
        
        for ticker in unique_tickers:
            try:
                ticker_df = test_data.xs(ticker, level='Ticker')
                if ticker_df.empty:
                    continue
            except KeyError:
                continue
            
            signals = pd.Series(1, index=ticker_df.index)
            bt = Backtester(ticker_df, initial_capital=10000)
            res = bt.run_backtest(signals_or_weights=signals)
            
            d_rets = res['Equity'].pct_change().fillna(0)
            d_rets.name = ticker
            all_daily_returns.append(d_rets)
        
        if not all_daily_returns:
            return self._create_empty_result(window_num, window)
        
        # Calculate portfolio metrics
        concat_rets = pd.concat(all_daily_returns, axis=1).fillna(0)
        port_daily_ret = concat_rets.mean(axis=1)
        port_cum_ret = (1 + port_daily_ret).cumprod()
        
        total_return = port_cum_ret.iloc[-1] - 1
        sharpe = 0
        if port_daily_ret.std() > 1e-6:
            sharpe = np.sqrt(252) * port_daily_ret.mean() / port_daily_ret.std()
        
        peak = port_cum_ret.cummax()
        dd = (port_cum_ret - peak) / peak
        max_dd = dd.min()
        
        return {
            'window': window_num,
            'name': window['name'] + ' (FALLBACK)',
            'test_period': f"{window['test'][0]} → {window['test'][1]}",
            'sharpe': sharpe,
            'total_return': total_return,
            'max_drawdown': max_dd,
            'win_rate': 0.0,
            'total_trades': 0
        }
    
    def _create_empty_result(self, window_num: int, window: Dict) -> Dict:
        """Create empty result for failed window."""
        return {
            'window': window_num,
            'name': window['name'],
            'test_period': f"{window['test'][0]} → {window['test'][1]}",
            'sharpe': 0,
            'total_return': 0,
            'max_drawdown': 0,
            'win_rate': 0,
            'total_trades': 0
        }
    
    def _print_window_results(self, result: Dict) -> None:
        """Print results for a window."""
        print(f"\n📊 Sonuçlar ({result['name']}):")
        print(f"   Sharpe:        {result['sharpe']:.2f}")
        print(f"   Total Return:  {result['total_return']*100:.2f}%")
        print(f"   Max Drawdown:  {result['max_drawdown']*100:.2f}%")
        print(f"   Win Rate:      {result['win_rate']*100:.1f}%")
        print(f"   Total Trades:  {result['total_trades']}")
    
    def _generate_summary(self) -> Tuple[Optional[pd.DataFrame], float, float]:
        """Generate and print summary of all windows."""
        if not self.results:
            return None, 0, 0
        
        df_results = pd.DataFrame(self.results)
        
        print("\n" + "="*70)
        print("WALK-FORWARD ÖZET")
        print("="*70)
        print(df_results[['name', 'sharpe', 'total_return', 'max_drawdown', 
                          'win_rate', 'total_trades']].to_string(index=False))
        
        avg_sharpe = df_results['sharpe'].mean()
        std_sharpe = df_results['sharpe'].std()
        avg_return = df_results['total_return'].mean()
        
        print(f"\n{'─'*50}")
        print(f"Ortalama Sharpe:  {avg_sharpe:.2f} ± {std_sharpe:.2f}")
        print(f"Ortalama Return:  {avg_return*100:.2f}%")
        print(f"Tutarlılık (CV):  {std_sharpe/max(abs(avg_sharpe), 0.01)*100:.0f}%")
        print(f"{'─'*50}")
        
        # Save results
        df_results.to_csv("reports/walk_forward_results.csv", index=False)
        print("\n💾 Sonuçlar reports/walk_forward_results.csv'ye kaydedildi")
        
        return df_results, avg_sharpe, std_sharpe
