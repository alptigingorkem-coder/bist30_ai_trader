# Feature Importance Analysis Report

## Analysis Overview

**Analysis Date:** 2024-01-15 14:30:00  
**Analysis Duration:** 4.1 minutes  
**Tickers Analyzed:** 5 (THYAO, GARAN, AKBNK, EREGL, SAHOL)  
**Data Points:** 12,500

---

## Feature Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Features** | 30 | 100.0% |
| **Blacklisted Features** | 10 | 33.3% |
| **Remaining Features** | 20 | 66.7% |

---

## Model Performance Comparison

### Baseline Model (All Features)
- **NDCG@3:** 0.6217
- **Features Used:** 30

### Optimized Model (After Feature Selection)
- **NDCG@3:** 0.6543
- **Features Used:** 20

### Performance Improvement
- **Absolute Change:** +0.0326
- **Relative Improvement:** +5.24%

✅ **Excellent improvement!** The feature selection significantly improved model performance.

---

## Top Features by Importance

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | rsi_14 | 0.085000 |
| 2 | macd_signal | 0.072000 |
| 3 | bb_width | 0.068000 |
| 4 | volume_sma_20 | 0.055000 |
| 5 | price_momentum_5 | 0.048000 |
| 6 | atr_14 | 0.042000 |
| 7 | obv_change | 0.038000 |
| 8 | stoch_k | 0.035000 |
| 9 | cci_20 | 0.031000 |
| 10 | adx_14 | 0.028000 |
| 11 | williams_r | 0.025000 |
| 12 | mfi_14 | 0.022000 |
| 13 | trix | 0.019000 |
| 14 | kama | 0.016000 |
| 15 | ppo | 0.013000 |
| 16 | roc_10 | 0.010000 |
| 17 | tsi | 0.008000 |
| 18 | ultimate_osc | 0.006000 |
| 19 | vwap_diff | 0.004000 |
| 20 | chaikin_osc | 0.003000 |

---

## Configuration

| Parameter | Value |
|-----------|-------|
| **Sample Size** | 1000 |
| **Importance Threshold** | 0.002 |
| **Start Date** | 2023-01-01 |
| **End Date** | 2023-12-31 |
| **Output Directory** | reports/feature_importance |

---

## Blacklisted Features

Total blacklisted features: **10**

<details>
<summary>Click to expand blacklisted features list</summary>

- `aroon_up`, `aroon_down`, `dpo`, `kst`, `mass_index`
- `pvo`, `eom`, `force_index`, `nvi`, `pvi`

</details>

---

## Summary

This analysis identified **10** low-contribution features that were removed from the model. The optimized model using **20** features achieved a NDCG@3 score of **0.6543**, representing a **+5.24%** change compared to the baseline model.

### Recommendations

- ✅ Excellent results! Consider deploying the optimized model to production.
- 🎯 Target NDCG@3 of 0.65 achieved! The optimization goal has been met.

---

*Report generated on 2024-01-15 14:35:00*
