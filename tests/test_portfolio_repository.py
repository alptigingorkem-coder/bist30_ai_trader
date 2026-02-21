"""
Unit tests for PortfolioRepository.

Tests the data persistence layer for portfolio state management.
"""

import pytest
import json
import os
from pathlib import Path
from paper_trading.portfolio.portfolio_repository import PortfolioRepository


class TestPortfolioRepositoryLoad:
    """Test cases for loading portfolio state."""
    
    def test_load_with_existing_file(self, tmp_path):
        """Test loading state from an existing file."""
        # Setup
        state_file = tmp_path / "test_state.json"
        test_state = {
            "cash": 100000,
            "positions": {},
            "realized_pnl": 0,
            "trade_history": [],
            "closed_trades": []
        }
        
        # Write test state to file
        with open(state_file, 'w') as f:
            json.dump(test_state, f)
        
        # Test
        repo = PortfolioRepository(str(state_file))
        loaded = repo.load()
        
        # Assert
        assert loaded == test_state
        assert loaded["cash"] == 100000
        assert loaded["positions"] == {}
    
    def test_load_with_missing_file(self, tmp_path):
        """Test loading state when file doesn't exist."""
        # Setup
        state_file = tmp_path / "nonexistent.json"
        
        # Test
        repo = PortfolioRepository(str(state_file))
        loaded = repo.load()
        
        # Assert
        assert loaded is None
    
    def test_load_with_corrupt_file(self, tmp_path):
        """Test loading state from a corrupt JSON file."""
        # Setup
        state_file = tmp_path / "corrupt.json"
        
        # Write invalid JSON
        with open(state_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Test & Assert
        repo = PortfolioRepository(str(state_file))
        with pytest.raises(ValueError, match="Failed to parse state file"):
            repo.load()
    
    def test_load_with_complex_state(self, tmp_path):
        """Test loading state with complex nested data."""
        # Setup
        state_file = tmp_path / "complex_state.json"
        test_state = {
            "cash": 95000.50,
            "positions": {
                "ASELS": {
                    "quantity": 100,
                    "entry_price": 45.50,
                    "current_price": 47.20
                }
            },
            "realized_pnl": 1250.75,
            "trade_history": [
                {"symbol": "THYAO", "pnl": 500},
                {"symbol": "GARAN", "pnl": 750.75}
            ],
            "closed_trades": []
        }
        
        with open(state_file, 'w') as f:
            json.dump(test_state, f)
        
        # Test
        repo = PortfolioRepository(str(state_file))
        loaded = repo.load()
        
        # Assert
        assert loaded == test_state
        assert loaded["positions"]["ASELS"]["quantity"] == 100
        assert loaded["realized_pnl"] == 1250.75


class TestPortfolioRepositorySave:
    """Test cases for saving portfolio state."""
    
    def test_save_creates_file(self, tmp_path):
        """Test that save creates a new file."""
        # Setup
        state_file = tmp_path / "new_state.json"
        test_state = {
            "cash": 100000,
            "positions": {},
            "realized_pnl": 0
        }
        
        # Test
        repo = PortfolioRepository(str(state_file))
        result = repo.save(test_state)
        
        # Assert
        assert result is True
        assert state_file.exists()
    
    def test_save_preserves_all_fields(self, tmp_path):
        """Test that save preserves all state fields."""
        # Setup
        state_file = tmp_path / "test_state.json"
        test_state = {
            "cash": 95000,
            "positions": {"ASELS": {"quantity": 100}},
            "realized_pnl": 1500,
            "trade_history": [{"symbol": "THYAO"}],
            "closed_trades": [],
            "peak_equity": 101500
        }
        
        # Test
        repo = PortfolioRepository(str(state_file))
        repo.save(test_state)
        
        # Load and verify
        with open(state_file, 'r') as f:
            loaded = json.load(f)
        
        # Assert
        assert loaded == test_state
        assert loaded["cash"] == 95000
        assert loaded["positions"]["ASELS"]["quantity"] == 100
        assert loaded["peak_equity"] == 101500
    
    def test_save_creates_directory(self, tmp_path):
        """Test that save creates parent directories if needed."""
        # Setup
        state_file = tmp_path / "nested" / "dir" / "state.json"
        test_state = {"cash": 100000}
        
        # Test
        repo = PortfolioRepository(str(state_file))
        result = repo.save(test_state)
        
        # Assert
        assert result is True
        assert state_file.exists()
        assert state_file.parent.exists()
    
    def test_save_overwrites_existing_file(self, tmp_path):
        """Test that save overwrites existing file."""
        # Setup
        state_file = tmp_path / "state.json"
        old_state = {"cash": 100000}
        new_state = {"cash": 95000}
        
        # Create initial file
        with open(state_file, 'w') as f:
            json.dump(old_state, f)
        
        # Test
        repo = PortfolioRepository(str(state_file))
        repo.save(new_state)
        
        # Load and verify
        with open(state_file, 'r') as f:
            loaded = json.load(f)
        
        # Assert
        assert loaded == new_state
        assert loaded["cash"] == 95000


class TestPortfolioRepositoryCSVExport:
    """Test cases for CSV export functionality."""
    
    def test_export_csv_creates_file(self, tmp_path):
        """Test that CSV export creates a file."""
        # Setup
        csv_file = tmp_path / "trades.csv"
        trades = [
            {"symbol": "ASELS", "pnl": 100, "date": "2024-01-01"},
            {"symbol": "THYAO", "pnl": 200, "date": "2024-01-02"}
        ]
        
        # Test
        repo = PortfolioRepository()
        result = repo.export_to_csv(trades, str(csv_file))
        
        # Assert
        assert result is True
        assert csv_file.exists()
    
    def test_export_csv_with_empty_trades(self, tmp_path):
        """Test CSV export with empty trade list."""
        # Setup
        csv_file = tmp_path / "empty.csv"
        trades = []
        
        # Test
        repo = PortfolioRepository()
        result = repo.export_to_csv(trades, str(csv_file))
        
        # Assert
        assert result is False
        assert not csv_file.exists()
    
    def test_export_csv_content(self, tmp_path):
        """Test that CSV export contains correct data."""
        # Setup
        csv_file = tmp_path / "trades.csv"
        trades = [
            {"symbol": "ASELS", "pnl": 100.50, "quantity": 10},
            {"symbol": "THYAO", "pnl": -50.25, "quantity": 5}
        ]
        
        # Test
        repo = PortfolioRepository()
        repo.export_to_csv(trades, str(csv_file))
        
        # Read and verify
        with open(csv_file, 'r') as f:
            lines = f.readlines()
        
        # Assert
        assert len(lines) == 3  # Header + 2 trades
        assert "symbol" in lines[0]
        assert "ASELS" in lines[1]
        assert "THYAO" in lines[2]
    
    def test_export_csv_creates_directory(self, tmp_path):
        """Test that CSV export creates parent directories."""
        # Setup
        csv_file = tmp_path / "nested" / "dir" / "trades.csv"
        trades = [{"symbol": "ASELS", "pnl": 100}]
        
        # Test
        repo = PortfolioRepository()
        result = repo.export_to_csv(trades, str(csv_file))
        
        # Assert
        assert result is True
        assert csv_file.exists()
        assert csv_file.parent.exists()


class TestPortfolioRepositoryEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_load_with_unicode_characters(self, tmp_path):
        """Test loading state with Turkish characters."""
        # Setup
        state_file = tmp_path / "unicode_state.json"
        test_state = {
            "cash": 100000,
            "positions": {
                "ŞEKER": {"quantity": 100},
                "İŞBANK": {"quantity": 50}
            },
            "note": "Türkçe karakterler: ğüşıöç"
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(test_state, f, ensure_ascii=False)
        
        # Test
        repo = PortfolioRepository(str(state_file))
        loaded = repo.load()
        
        # Assert
        assert loaded == test_state
        assert "ŞEKER" in loaded["positions"]
        assert "İŞBANK" in loaded["positions"]
    
    def test_save_with_unicode_characters(self, tmp_path):
        """Test saving state with Turkish characters."""
        # Setup
        state_file = tmp_path / "unicode_save.json"
        test_state = {
            "positions": {"ŞEKER": {"quantity": 100}},
            "note": "Türkçe: ğüşıöç"
        }
        
        # Test
        repo = PortfolioRepository(str(state_file))
        result = repo.save(test_state)
        
        # Assert
        assert result is True
        
        # Verify by reading file
        with open(state_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "ŞEKER" in content
            assert "Türkçe" in content
    
    def test_load_with_empty_file(self, tmp_path):
        """Test loading from an empty file."""
        # Setup
        state_file = tmp_path / "empty.json"
        
        # Create empty file
        state_file.touch()
        
        # Test & Assert
        repo = PortfolioRepository(str(state_file))
        with pytest.raises(ValueError):
            repo.load()
    
    def test_save_with_very_large_state(self, tmp_path):
        """Test saving a large state with many positions."""
        # Setup
        state_file = tmp_path / "large_state.json"
        
        # Create state with 100 positions
        positions = {f"STOCK{i}": {"quantity": i * 10} for i in range(100)}
        test_state = {
            "cash": 100000,
            "positions": positions,
            "trade_history": [{"symbol": f"STOCK{i}", "pnl": i} for i in range(1000)]
        }
        
        # Test
        repo = PortfolioRepository(str(state_file))
        result = repo.save(test_state)
        
        # Assert
        assert result is True
        
        # Verify by loading
        loaded = repo.load()
        assert len(loaded["positions"]) == 100
        assert len(loaded["trade_history"]) == 1000
    
    def test_save_with_special_float_values(self, tmp_path):
        """Test saving state with special float values."""
        # Setup
        state_file = tmp_path / "float_state.json"
        test_state = {
            "cash": 100000.123456789,
            "realized_pnl": -1500.50,
            "peak_equity": 0.0
        }
        
        # Test
        repo = PortfolioRepository(str(state_file))
        repo.save(test_state)
        loaded = repo.load()
        
        # Assert
        assert loaded["cash"] == test_state["cash"]
        assert loaded["realized_pnl"] == test_state["realized_pnl"]
        assert loaded["peak_equity"] == test_state["peak_equity"]
    
    def test_export_csv_with_special_characters(self, tmp_path):
        """Test CSV export with special characters."""
        # Setup
        csv_file = tmp_path / "special_trades.csv"
        trades = [
            {"symbol": "ŞEKER", "pnl": 100.50, "note": "Güzel işlem"},
            {"symbol": "İŞBANK", "pnl": -50.25, "note": "Kötü işlem"}
        ]
        
        # Test
        repo = PortfolioRepository()
        result = repo.export_to_csv(trades, str(csv_file))
        
        # Assert
        assert result is True
        
        # Verify content
        with open(csv_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "ŞEKER" in content
            assert "İŞBANK" in content
            assert "Güzel işlem" in content


class TestPortfolioRepositoryIntegration:
    """Integration tests for PortfolioRepository."""
    
    def test_save_and_load_roundtrip(self, tmp_path):
        """Test that save and load preserve data correctly."""
        # Setup
        state_file = tmp_path / "roundtrip.json"
        original_state = {
            "cash": 98500.75,
            "positions": {
                "ASELS": {"quantity": 100, "entry_price": 45.50},
                "THYAO": {"quantity": 50, "entry_price": 120.00}
            },
            "realized_pnl": 2500.50,
            "trade_history": [
                {"symbol": "GARAN", "pnl": 1000},
                {"symbol": "ISCTR", "pnl": 1500.50}
            ],
            "closed_trades": [],
            "peak_equity": 102500.75
        }
        
        # Test
        repo = PortfolioRepository(str(state_file))
        
        # Save
        save_result = repo.save(original_state)
        assert save_result is True
        
        # Load
        loaded_state = repo.load()
        
        # Assert
        assert loaded_state == original_state
        assert loaded_state["cash"] == original_state["cash"]
        assert loaded_state["positions"] == original_state["positions"]
        assert loaded_state["realized_pnl"] == original_state["realized_pnl"]
    
    def test_multiple_save_load_cycles(self, tmp_path):
        """Test multiple save/load cycles preserve data."""
        # Setup
        state_file = tmp_path / "cycles.json"
        repo = PortfolioRepository(str(state_file))
        
        # Cycle 1
        state1 = {"cash": 100000, "positions": {}}
        repo.save(state1)
        loaded1 = repo.load()
        assert loaded1 == state1
        
        # Cycle 2 - modify state
        state2 = {"cash": 95000, "positions": {"ASELS": {"quantity": 100}}}
        repo.save(state2)
        loaded2 = repo.load()
        assert loaded2 == state2
        assert loaded2 != state1
        
        # Cycle 3 - modify again
        state3 = {"cash": 90000, "positions": {"ASELS": {"quantity": 50}}}
        repo.save(state3)
        loaded3 = repo.load()
        assert loaded3 == state3
        assert loaded3 != state2
    
    def test_concurrent_repository_instances(self, tmp_path):
        """Test that multiple repository instances work correctly."""
        # Setup
        state_file = tmp_path / "shared.json"
        test_state = {"cash": 100000, "positions": {}}
        
        # Create two repository instances
        repo1 = PortfolioRepository(str(state_file))
        repo2 = PortfolioRepository(str(state_file))
        
        # Save with repo1
        repo1.save(test_state)
        
        # Load with repo2
        loaded = repo2.load()
        
        # Assert
        assert loaded == test_state
