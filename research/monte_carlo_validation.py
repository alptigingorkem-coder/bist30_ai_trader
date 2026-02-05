"""
Monte Carlo Simulation for BIST30 AI Trader
Runs 1000 randomized scenarios to estimate performance distribution
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
import os
warnings.filterwarnings('ignore')

def load_daily_returns():
    """Load the concatenated daily returns"""
    results_file = 'reports/daily_returns_concatenated.csv'
    if not os.path.exists(results_file):
        raise FileNotFoundError("Daily returns file not found. Run optimization first.")
        
    df = pd.read_csv(results_file, index_col=0, parse_dates=True)
    
    # Calculate Portfolio Return (Equal Weighted Average of all active tickers)
    # This represents the "System Performance"
    portfolio_return = df.mean(axis=1)
    
    return portfolio_return

def monte_carlo_simulation(daily_returns_series, n_scenarios=2000, years_ahead=5, block_size=20):
    """
    Run Monte Carlo simulation using Block Bootstrap with BLACK SWAN events.
    
    Args:
        daily_returns_series: Series of historical daily returns
        n_scenarios: Number of scenarios to simulate (Increased to 2000 for better tail resolution)
        years_ahead: Number of years to project
        block_size: Size of blocks to sample (in days)
    """
    print(f"\n🎲 Monte Carlo Simülasyonu Başlatılıyor (Block Bootstrap + Black Swan)...")
    print(f"   Senaryo: {n_scenarios}")
    print(f"   Projeksiyon: {years_ahead} yıl")
    print(f"   Blok Boyutu: {block_size} gün")
    
    # --- BLACK SWAN CONFIG ---
    CRISIS_YEAR_PROB = 0.10   # Her yıl %10 ihtimalle "Kriz Yılı" olur
    BLACK_SWAN_DAILY_PROB = 0.001 # Her gün binde 1 ihtimalle "Ani Çöküş" (Flash Crash)
    
    print(f"   ⚠️  Kriz Yılı Olasılığı: %{CRISIS_YEAR_PROB*100}")
    print(f"   ⚠️  Black Swan (Flash Crash) Olasılığı: %{BLACK_SWAN_DAILY_PROB*100} (Günlük)")
    
    if len(daily_returns_series) < block_size:
        raise ValueError(f"Yetersiz veri. Minimum {block_size} birim veri gerekli.")
    
    # Config TIMEFRAME='W' ise annual_days=52, değilse 252.
    # Ancak daily_returns_series haftalıksa prob'ları ona göre scale etmeliyiz.
    # Varsayım: daily_returns_series aslında 'Portfolio_Return' (haftalık veya günlük).
    # Optuna scripti 'W' modunda haftalık getiri üretiyor.
    # O zaman annual_trading_days = 52.
    annual_trading_days = 52 
    total_days = years_ahead * annual_trading_days
    
    scenario_final_values = []
    
    np.random.seed(42)  # For reproducibility
    returns_array = daily_returns_series.values
    n_samples = len(returns_array)
    
    for scenario in range(n_scenarios):
        # 1. Base Market Path (Bootstrap)
        simulated_path = []
        days_generated = 0
        
        while days_generated < total_days:
            start_idx = np.random.randint(0, n_samples - block_size + 1)
            block = returns_array[start_idx : start_idx + block_size]
            simulated_path.extend(block)
            days_generated += len(block)
            
        simulated_path = np.array(simulated_path[:total_days])
        
        # 2. Inject Crisis Years
        # Her yıl için (total_days / annual_trading_days) kriz kontrolü
        for year in range(years_ahead):
            if np.random.random() < CRISIS_YEAR_PROB:
                # Kriz Yılı! O yıla denk gelen günlere ekstra negatif drift ekle
                # Yılın başlangıç ve bitiş indeksleri
                start_day = year * annual_trading_days
                end_day = (year + 1) * annual_trading_days
                
                # Kriz şiddeti: Yıllık -%30 ile -%50 arası ek kayıp
                # Bu kaybı günlere yayalım
                crisis_severity = np.random.uniform(0.30, 0.50)
                # Haftalık periyotta (1-severity)^(1/52) - 1
                weekly_drag = (1 - crisis_severity)**(1/annual_trading_days) - 1
                
                simulated_path[start_day:end_day] += weekly_drag
        
        # 3. Inject Black Swans (Flash Crashes)
        # Bütün simülasyon boyunca rastgele günlerde şok
        for day in range(total_days):
            if np.random.random() < BLACK_SWAN_DAILY_PROB:
                # Flash Crash: -%10 ile -%20 arası ani düşüş
                shock = np.random.uniform(-0.10, -0.20)
                simulated_path[day] += shock
                
        # Calculate Cumulative
        cumulative = np.prod(1 + simulated_path)
        scenario_final_values.append(cumulative)
    
    scenario_final_values = np.array(scenario_final_values)
    
    # Calculate statistics
    results = {
        'final_values': scenario_final_values,
        'percentiles': {
            '1st': np.percentile(scenario_final_values, 1), # Extreme Tail
            '5th': np.percentile(scenario_final_values, 5),
            '25th': np.percentile(scenario_final_values, 25),
            '50th': np.percentile(scenario_final_values, 50),
            '75th': np.percentile(scenario_final_values, 75),
            '95th': np.percentile(scenario_final_values, 95),
        },
        'mean': np.mean(scenario_final_values),
        'std': np.std(scenario_final_values),
        'prob_ruin': np.mean(scenario_final_values < 0.2), # Anaparanın %80'ini kaybetme
        'prob_loss': np.mean(scenario_final_values < 1.0),
        'prob_double': np.mean(scenario_final_values > 2.0),
    }
    
    print(f"\n✅ Simülasyon Tamamlandı!")
    print(f"   Ortalama: {results['mean']:.2f}x")
    print(f"   Medyan (50%): {results['percentiles']['50th']:.2f}x")
    print(f"   VaR (95% - Kötü): {results['percentiles']['5th']:.2f}x")
    print(f"   VaR (99% - Çok Kötü): {results['percentiles']['1st']:.2f}x")
    print(f"   İflas Riski (<0.2x): %{results['prob_ruin']*100:.2f}")
    print(f"   Zarar Riski (<1.0x): %{results['prob_loss']*100:.2f}")
    
    return results

def stress_test(results_df):
    """
    Stress test scenarios based on historical crisis patterns
    """
    print(f"\n⚠️ Stress Test Başlatılıyor...")
    
    # Define crisis scenarios based on historical patterns
    scenarios = {
        '2001 Argentina Crisis': {
            'description': 'Ekonomik çöküş, para birimi krizi',
            'returns': [-0.30, -0.20, 0.10, 0.40, 0.20],  # Severe drop then recovery
            'sharpe_multiplier': 0.5,
            'dd_multiplier': 2.0
        },
        '2008 Global Crisis': {
            'description': 'Küresel finansal kriz, likidite krizi',
            'returns': [-0.35, -0.15, 0.20, 0.50, 0.30],
            'sharpe_multiplier': 0.4,
            'dd_multiplier': 2.5
        },
        '2018 Turkey Crisis': {
            'description': 'TL krizi, faiz şoku, döviz dalgalanması',
            'returns': [-0.25, -0.10, 0.15, 0.35, 0.25],
            'sharpe_multiplier': 0.6,
            'dd_multiplier': 1.8
        },
        '2023-like Event': {
            'description': 'Deprem + Seçim + Enflasyon kombinasyonu',
            'returns': [0.20, -0.10, 0.95, 0.30, 0.10],  # Based on actual 2020-2024
            'sharpe_multiplier': 0.8,
            'dd_multiplier': 1.2
        }
    }
    
    stress_results = {}
    
    for scenario_name, scenario_data in scenarios.items():
        returns = scenario_data['returns']
        cumulative = np.prod([1 + r for r in returns])
        avg_return = np.mean(returns)
        worst_year = min(returns)
        
        # Estimate Sharpe and DD based on historical average
        avg_sharpe = results_df['cv_sharpe'].mean() * scenario_data['sharpe_multiplier']
        avg_dd = results_df['test_drawdown'].mean() * scenario_data['dd_multiplier']
        
        stress_results[scenario_name] = {
            'description': scenario_data['description'],
            'cumulative_return': cumulative,
            'avg_annual_return': avg_return,
            'worst_year': worst_year,
            'estimated_sharpe': avg_sharpe,
            'estimated_max_dd': avg_dd,
            'survivability': 'Hayatta kalır' if cumulative > 0.5 else 'Kritik risk'
        }
        
        print(f"\n   📉 {scenario_name}:")
        print(f"      {scenario_data['description']}")
        print(f"      5 yıllık kümülatif: {cumulative:.2f}x ({(cumulative-1)*100:+.1f}%)")
        print(f"      En kötü yıl: {worst_year*100:.1f}%")
        print(f"      Tahmini Sharpe: {avg_sharpe:.2f}")
        print(f"      Tahmini Max DD: {avg_dd*100:.1f}%")
    
    return stress_results

def calculate_risk_metrics(monte_carlo_results):
    """Calculate advanced risk metrics"""
    
    final_values = monte_carlo_results['final_values']
    
    # Value at Risk (VaR)
    var_95 = monte_carlo_results['percentiles']['5th']
    var_99 = monte_carlo_results['percentiles']['1st']
    
    # Conditional Value at Risk (CVaR)
    cvar_95 = np.mean(final_values[final_values <= var_95])
    
    # Upside potential
    prob_5x = np.mean(final_values > 5.0)
    
    metrics = {
        'VaR_95': var_95,
        'VaR_99': var_99,
        'CVaR_95': cvar_95,
        'Prob_loss': monte_carlo_results['prob_loss'],
        'Prob_ruin': monte_carlo_results['prob_ruin'],
        'Prob_5x': prob_5x,
    }
    
    return metrics

def create_monte_carlo_visualization(monte_carlo_results, stress_results, risk_metrics):
    """Create comprehensive visualization"""
    
    fig = plt.figure(figsize=(18, 10))
    fig.suptitle('BIST30 AI Trader - Monte Carlo Simülasyonu & Stress Test', 
                 fontsize=18, fontweight='bold', y=0.995)
    
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    # 1. Distribution of Final Values (Top Left)
    ax1 = fig.add_subplot(gs[0, 0])
    
    values = monte_carlo_results['final_values']
    ax1.hist(values, bins=50, color='#2E86AB', alpha=0.7, edgecolor='black')
    ax1.axvline(monte_carlo_results['percentiles']['50th'], color='green', 
                linestyle='--', linewidth=2, label=f"Medyan: {monte_carlo_results['percentiles']['50th']:.2f}x")
    ax1.axvline(monte_carlo_results['percentiles']['5th'], color='red', 
                linestyle='--', linewidth=2, label=f"5. Persentil: {monte_carlo_results['percentiles']['5th']:.2f}x")
    ax1.axvline(monte_carlo_results['percentiles']['95th'], color='orange', 
                linestyle='--', linewidth=2, label=f"95. Persentil: {monte_carlo_results['percentiles']['95th']:.2f}x")
    
    ax1.set_title('5 Yıllık Kümülatif Getiri Dağılımı', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Kümülatif Getiri (x)', fontsize=10)
    ax1.set_ylabel('Senaryo Sayısı', fontsize=10)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # 2. Probability Distribution (Top Middle)
    ax2 = fig.add_subplot(gs[0, 1])
    
    percentiles = np.arange(0, 101, 1)
    percentile_values = np.percentile(values, percentiles)
    
    ax2.plot(percentiles, percentile_values, linewidth=2.5, color='#A23B72')
    ax2.fill_between(percentiles, 0, percentile_values, alpha=0.3, color='#A23B72')
    ax2.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax2.axhline(y=2.0, color='green', linestyle='--', alpha=0.5, label='2x')
    ax2.axhline(y=3.0, color='blue', linestyle='--', alpha=0.5, label='3x')
    
    ax2.set_title('Kümülatif Dağılım Fonksiyonu (CDF)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Persentil (%)', fontsize=10)
    ax2.set_ylabel('Kümülatif Getiri (x)', fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # 3. Risk Metrics Table (Top Right)
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis('off')
    
    risk_data = [
        ['Risk Metriği', 'Değer'],
        ['VaR (95%)', f"{risk_metrics['VaR_95']:.2f}x"],
        ['VaR (99%)', f"{risk_metrics['VaR_99']:.2f}x"],
        ['Zarar Olasılığı (<1.0x)', f"{risk_metrics['Prob_loss']*100:.2f}%"],
        ['İFLAS RİSKİ (<0.2x)', f"{risk_metrics['Prob_ruin']*100:.2f}%"],
        ['', ''],
        ['Medyan Getiri', f"{monte_carlo_results['percentiles']['50th']:.2f}x"],
        ['2x Kazanç', f"{monte_carlo_results['prob_double']*100:.1f}%"],
        ['5x Kazanç', f"{risk_metrics['Prob_5x']*100:.1f}%"],
    ]
    
    table = ax3.table(cellText=risk_data, cellLoc='center', loc='center',
                      colWidths=[0.6, 0.4])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)
    
    # Style
    for i in range(len(risk_data)):
        if i == 0:
            table[(i, 0)].set_facecolor('#2E86AB')
            table[(i, 1)].set_facecolor('#2E86AB')
            table[(i, 0)].set_text_props(weight='bold', color='white')
            table[(i, 1)].set_text_props(weight='bold', color='white')
        elif i == 5:
            table[(i, 0)].set_facecolor('#E8E8E8')
            table[(i, 1)].set_facecolor('#E8E8E8')
        else:
            if i < 5:
                # Risk Metrics Background
                if i == 4: # İflas Riski
                    if risk_metrics['Prob_ruin'] > 0.01:
                         table[(i, 1)].set_facecolor('#FF5252') # Kırmızı Alarm
                         table[(i, 0)].set_text_props(weight='bold', color='red')
                    else:
                         table[(i, 1)].set_facecolor('#FFCDD2')
                else:
                    table[(i, 1)].set_facecolor('#FFCDD2')  
            else:
                table[(i, 1)].set_facecolor('#C8F7DC')  # Upside in green
    
    ax3.set_title('Risk Metrikleri & Olasılıklar', fontsize=12, fontweight='bold', pad=20)
    
    # 4. Stress Test Results (Bottom Span)
    ax4 = fig.add_subplot(gs[1, :])
    
    stress_names = list(stress_results.keys())
    cumulative_returns = [stress_results[name]['cumulative_return'] for name in stress_names]
    worst_years = [stress_results[name]['worst_year'] * 100 for name in stress_names]
    
    x = np.arange(len(stress_names))
    width = 0.35
    
    bars1 = ax4.bar(x - width/2, cumulative_returns, width, label='5 Yıllık Kümülatif (x)',
                    color='#2E86AB', alpha=0.7, edgecolor='black')
    bars2 = ax4.bar(x + width/2, [wy/100 + 1 for wy in worst_years], width, 
                    label='En Kötü Yıl (1+return)',
                    color='#A23B72', alpha=0.7, edgecolor='black')
    
    ax4.axhline(y=1.0, color='gray', linestyle='--', linewidth=1)
    ax4.set_title('Stress Test Sonuçları (Kriz Senaryoları)', fontsize=14, fontweight='bold')
    ax4.set_ylabel('Getiri Multiplikörü (x)', fontsize=11)
    ax4.set_xticks(x)
    ax4.set_xticklabels(stress_names, rotation=15, ha='right', fontsize=10)
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}x',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Save
    output_path = 'reports/monte_carlo_results.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n✅ Monte Carlo görselleştirmesi kaydedildi: {output_path}")
    plt.close()
    
    return output_path

def main():
    print("="*70)
    print("BIST30 AI Trader - Monte Carlo Simülasyonu & Stress Testing (Block Bootstrap)")
    print("="*70)
    
    # Load backtest results for Stress Test (still needs yearly stats)
    try:
        results_df = pd.read_csv('reports/optuna_walk_forward_results.csv')
    except Exception:
        print("Uyarı: 'reports/optuna_walk_forward_results.csv' bulunamadı.")
        print("Stress testleri için bu dosyaya ihtiyaç var. Lütfen önce optimizasyonu çalıştırın.")
        results_df = None
    
    # Load daily returns for Monte Carlo
    try:
        print("\n📊 Günlük getiri verisi yükleniyor...")
        daily_returns = load_daily_returns()
        print(f"✅ {len(daily_returns)} günlük veri yüklendi")
    except Exception as e:
        print(f"HATA: {e}")
        print("Lütfen 'research/optuna_nested_walk_forward.py' betiğini (en azından --dry-run modunda) çalıştırın.")
        return

    # Run Monte Carlo
    mc_results = monte_carlo_simulation(daily_returns, n_scenarios=1000, years_ahead=5, block_size=20)
    
    # Run Stress Tests (if possible)
    stress_results = {}
    if results_df is not None:
        stress_results = stress_test(results_df)
    else:
        print("Stress testleri atlandı (Yıllık veri eksik).")
    
    # Calculate Risk Metrics
    risk_metrics = calculate_risk_metrics(mc_results)
    
    # Create visualization
    print(f"\n🎨 Görselleştirme oluşturuluyor...")
    viz_path = create_monte_carlo_visualization(mc_results, stress_results, risk_metrics)
    
    print("\n" + "="*70)
    print("✅ Monte Carlo Analizi Tamamlandı!")
    print("="*70)
    print(f"\n📁 Sonuçlar: {viz_path}")
    
    return mc_results, stress_results, risk_metrics

if __name__ == "__main__":
    main()
