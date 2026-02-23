import os
import sys

# Add project root to path
# scripts/training/ -> scripts/ -> root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def comprehensive_walk_forward():
    """
    Walk-Forward Validation — Gerçek LightGBM Model Tahminleriyle.
    
    Delegates to WalkForwardValidator class for execution.
    
    Returns:
        Tuple of (results DataFrame, average Sharpe, Sharpe std)
    """
    import argparse
    from scripts.training.walk_forward_validator import WalkForwardValidator
    
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', type=int, default=None, 
                       help='Specific window index (1-based) to run')
    args = parser.parse_args()
    
    # Create and run validator
    validator = WalkForwardValidator()
    results, avg_sharpe, std_sharpe = validator.run(window_index=args.window)
    
    return results, avg_sharpe, std_sharpe

if __name__ == "__main__":
    comprehensive_walk_forward()
