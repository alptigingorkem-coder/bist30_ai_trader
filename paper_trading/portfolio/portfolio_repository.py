"""
Portfolio data persistence layer.

This module handles loading and saving portfolio state to/from JSON files.
Follows the Repository pattern for data access operations.
"""

import json
import os
import csv
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PortfolioRepository:
    """
    Handles portfolio state persistence operations.
    
    Responsibilities:
    - Load portfolio state from JSON file
    - Save portfolio state to JSON file
    - Export trade ledger to CSV
    - Handle file I/O errors gracefully
    
    This class follows the Repository pattern, separating data access
    concerns from business logic.
    """
    
    def __init__(self, state_file: str = "logs/paper_trading/portfolio_state.json"):
        """
        Initialize the repository with a state file path.
        
        Args:
            state_file: Path to the JSON file for storing portfolio state
        """
        self.state_file = state_file
    
    def load(self) -> Optional[Dict]:
        """
        Load portfolio state from JSON file.
        
        Returns:
            Dictionary containing portfolio state, or None if file doesn't exist
            
        Raises:
            ValueError: If the JSON file is corrupt or invalid
            IOError: If there's an unexpected error reading the file
        """
        if not os.path.exists(self.state_file):
            logger.info(f"State file not found: {self.state_file}")
            return None
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                logger.info(f"Successfully loaded state from {self.state_file}")
                return state
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt state file: {e}")
            raise ValueError(f"Failed to parse state file: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading state: {e}")
            raise IOError(f"Failed to load state: {e}")
    
    def save(self, state: Dict) -> bool:
        """
        Save portfolio state to JSON file.
        
        Args:
            state: Dictionary containing portfolio state to save
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            # Write state to file
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved state to {self.state_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            return False
    
    def export_to_csv(self, trades: List[Dict], filepath: str) -> bool:
        """
        Export trade ledger to CSV file.
        
        Args:
            trades: List of trade dictionaries to export
            filepath: Path to the CSV file to create
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if not trades:
                logger.warning("No trades to export")
                return False
            
            # Get fieldnames from first trade
            fieldnames = list(trades[0].keys())
            
            # Write to CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(trades)
            
            logger.info(f"Successfully exported {len(trades)} trades to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return False
