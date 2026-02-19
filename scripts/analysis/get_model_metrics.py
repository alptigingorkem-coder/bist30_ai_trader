import mlflow
import pandas as pd
import os
import sys

# Try to find mlruns
possible_paths = [
    "mlruns",
    "../mlruns",
    "./mlruns",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mlruns")
]

tracking_uri = None
for p in possible_paths:
    if os.path.exists(p):
        tracking_uri = f"file://{os.path.abspath(p)}"
        print(f"Found mlruns at: {p}")
        break

if tracking_uri:
    mlflow.set_tracking_uri(tracking_uri)
else:
    print("Could not find mlruns directory. Using default.")

def get_latest_metrics():
    print("Fetching metrics from MLflow...")
    experiments = mlflow.search_experiments()
    
    if not experiments:
        print("No experiments found.")
        return

    for exp in experiments:
        print(f"\nExperiment: {exp.name} (ID: {exp.experiment_id})")
        
        # Get latest run
        runs = mlflow.search_runs(experiment_ids=[exp.experiment_id], max_results=1, order_by=["start_time DESC"])
        
        if runs.empty:
            print("  No runs found.")
            continue
            
        latest_run = runs.iloc[0]
        print(f"  Latest Run ID: {latest_run.run_id}")
        print(f"  Date: {latest_run.start_time}")
        print(f"  Status: {latest_run.status}")
        
        # Print Metrics
        print("  Metrics:")
        # Filter columns starting with 'metrics.'
        metric_cols = [c for c in runs.columns if c.startswith("metrics.")]
        if metric_cols:
            for col in metric_cols:
                metric_name = col.replace("metrics.", "")
                val = latest_run[col]
                if pd.notna(val):
                    print(f"    - {metric_name}: {val:.6f}")
        else:
            print("    No metrics logged.")

if __name__ == "__main__":
    get_latest_metrics()
