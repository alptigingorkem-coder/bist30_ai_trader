
import json
import os
from datetime import datetime
import pandas as pd

class PaperLogger:
    def __init__(self, log_dir="logs/paper_trading"):
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
    def _get_log_file(self):
        """Returns the daily log file path."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"paper_trades_{date_str}.json")

    def log_decision(self, snapshot):
        """
        Logs a single trading decision snapshot.
        snapshot: Dict containing fully resolved trade info.
        """
        file_path = self._get_log_file()
        
        # Add timestamp if missing
        if 'timestamp' not in snapshot:
            snapshot['timestamp'] = datetime.now().isoformat()
            
        # Append to JSON Lines file
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
            
    def load_logs(self, start_date=None, end_date=None):
        """Loads logs into a DataFrame for analysis."""
        all_records = []
        
        # List all JSON files
        files = sorted([f for f in os.listdir(self.log_dir) if f.startswith("paper_trades_") and f.endswith(".json")])
        
        for f in files:
            # Parse date from filename
            try:
                date_part = f.replace("paper_trades_", "").replace(".json", "")
                # Filter by date if requested
                # (Skipping robust date parsing for now, string comparison usually works for ISO dates)
            except:
                continue
                
            path = os.path.join(self.log_dir, f)
            with open(path, 'r', encoding='utf-8') as file_obj:
                for line in file_obj:
                    try:
                        all_records.append(json.loads(line))
                    except:
                        pass
                        
        if not all_records:
            return pd.DataFrame()
            
        return pd.DataFrame(all_records)
