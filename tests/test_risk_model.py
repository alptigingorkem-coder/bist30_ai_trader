
from risk_model import RiskModel

def test_risk_model():
    print("--- Risk Model Test ---")
    
    rm = RiskModel()
    
    # Scenarios: [Regime, Pred_Return, Volatility, Price]
    # Regime: 0=Sideways, 1=Crash, 2=Trend
    scenarios = [
        ("Good Trade (Trend)", 2, 0.03, 0.04, 100),
        ("Crash Mode", 1, 0.05, 0.04, 100),
        ("Low Return", 2, 0.005, 0.04, 100), # < Threshold
        ("High Volatility", 2, 0.03, 0.15, 100), # > Max Vol
    ]
    
    capital = 100000
    
    for name, reg, ret, vol, price in scenarios:
        print(f"\nScanning: {name}")
        approved, reason = rm.check_filters(reg, ret, vol, price)
        print(f"  Approved: {approved} | Reason: {reason}")
        
        if approved:
            amount, ratio = rm.calculate_position_size(ret, vol, capital)
            print(f"  Position Size: {amount:.2f} ({ratio*100:.2f}%)")

if __name__ == "__main__":
    test_risk_model()
