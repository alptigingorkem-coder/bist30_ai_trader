"""
Unit tests for PortfolioFormatter.

Tests the formatting and presentation logic for portfolio data.
"""

import pytest
import os
import csv
from datetime import datetime
from paper_trading.portfolio.portfolio_formatter import PortfolioFormatter


class TestGetTradeLedger:
    """Test cases for trade ledger formatting."""
    
    def test_empty_trades(self):
        """Test formatting empty trade list."""
        formatter = PortfolioFormatter()
        ledger = formatter.get_trade_ledger([])
        
        assert ledger == []
    
    def test_single_trade(self):
        """Test formatting a single trade."""
        formatter = PortfolioFormatter()
        
        trades = [{
            "symbol": "ASELS",
            "side": "LONG",
            "entry_price": 40.0,
            "exit_price": 45.0,
            "quantity": 100,
            "pnl": 500.0,
            "return_pct": 0.125,
            "entry_time": "2026-02-22T10:00:00",
            "exit_time": "2026-02-22T15:00:00",
            "holding_minutes": 300
        }]
        
        ledger = formatter.get_trade_ledger(trades)
        
        assert len(ledger) == 1
        assert ledger[0]["symbol"] == "ASELS"
        assert ledger[0]["side"] == "LONG"
        assert ledger[0]["entry_price"] == 40.0
        assert ledger[0]["exit_price"] == 45.0
        assert ledger[0]["quantity"] == 100
        assert ledger[0]["gross_pnl"] == 500.0
        assert ledger[0]["return_pct"] == 12.5  # Converted to %
        assert ledger[0]["holding_days"] == pytest.approx(0.21, abs=0.01)
        assert "trade_id" in ledger[0]
    
    def test_commission_calculation(self):
        """Test commission calculation in ledger."""
        formatter = PortfolioFormatter(commission_rate=0.0025)
        
        trades = [{
            "symbol": "ASELS",
            "entry_price": 40.0,
            "exit_price": 45.0,
            "quantity": 100,
            "pnl": 500.0,
            "return_pct": 0.125,
            "entry_time": "2026-02-22T10:00:00",
            "exit_time": "2026-02-22T15:00:00",
            "holding_minutes": 300
        }]
        
        ledger = formatter.get_trade_ledger(trades)
        
        # Commission = (40 + 45) * 100 * 0.0025 = 21.25
        assert ledger[0]["commission"] == pytest.approx(21.25)
        assert ledger[0]["net_pnl"] == pytest.approx(478.75)
    
    def test_multiple_trades(self):
        """Test formatting multiple trades."""
        formatter = PortfolioFormatter()
        
        trades = [
            {
                "symbol": "ASELS",
                "entry_price": 40.0,
                "exit_price": 45.0,
                "quantity": 100,
                "pnl": 500.0,
                "return_pct": 0.125,
                "entry_time": "2026-02-22T10:00:00",
                "exit_time": "2026-02-22T15:00:00",
                "holding_minutes": 300
            },
            {
                "symbol": "THYAO",
                "entry_price": 100.0,
                "exit_price": 95.0,
                "quantity": 50,
                "pnl": -250.0,
                "return_pct": -0.05,
                "entry_time": "2026-02-22T11:00:00",
                "exit_time": "2026-02-22T14:00:00",
                "holding_minutes": 180
            }
        ]
        
        ledger = formatter.get_trade_ledger(trades)
        
        assert len(ledger) == 2
        assert ledger[0]["symbol"] == "ASELS"
        assert ledger[1]["symbol"] == "THYAO"
        assert ledger[1]["gross_pnl"] == -250.0


class TestExportTradeLedgerCSV:
    """Test cases for CSV export."""
    
    def test_export_empty_trades(self, tmp_path):
        """Test exporting empty trade list."""
        formatter = PortfolioFormatter()
        filepath = str(tmp_path / "test_ledger.csv")
        
        result = formatter.export_trade_ledger_csv([], filepath)
        
        assert result == filepath
        assert os.path.exists(filepath)
    
    def test_export_with_trades(self, tmp_path):
        """Test exporting trades to CSV."""
        formatter = PortfolioFormatter()
        filepath = str(tmp_path / "test_ledger.csv")
        
        trades = [{
            "symbol": "ASELS",
            "side": "LONG",
            "entry_price": 40.0,
            "exit_price": 45.0,
            "quantity": 100,
            "pnl": 500.0,
            "return_pct": 0.125,
            "entry_time": "2026-02-22T10:00:00",
            "exit_time": "2026-02-22T15:00:00",
            "holding_minutes": 300
        }]
        
        result = formatter.export_trade_ledger_csv(trades, filepath)
        
        assert result == filepath
        assert os.path.exists(filepath)
        
        # Verify CSV content
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]["symbol"] == "ASELS"
            assert rows[0]["entry_price"] == "40.0"
            assert rows[0]["exit_price"] == "45.0"
    
    def test_export_default_filepath(self):
        """Test exporting with default filepath."""
        formatter = PortfolioFormatter()
        
        trades = [{
            "symbol": "ASELS",
            "entry_price": 40.0,
            "exit_price": 45.0,
            "quantity": 100,
            "pnl": 500.0,
            "return_pct": 0.125,
            "entry_time": "2026-02-22T10:00:00",
            "exit_time": "2026-02-22T15:00:00",
            "holding_minutes": 300
        }]
        
        result = formatter.export_trade_ledger_csv(trades)
        
        assert result == "logs/paper_trading/trade_ledger.csv"
        assert os.path.exists(result)
        
        # Cleanup
        os.remove(result)


class TestFormatStressStatus:
    """Test cases for stress status formatting."""
    
    def test_format_active_status(self):
        """Test formatting active trading status."""
        formatter = PortfolioFormatter()
        
        status = {
            "trading_halted": False,
            "daily_pnl": 1500.0,
            "daily_pnl_pct": 1.5,
            "daily_max_loss_remaining": 3500.0,
            "consecutive_losses": 1,
            "consecutive_loss_limit": 3,
            "exposure_multiplier": 1.0,
            "effective_max_exposure": 80.0
        }
        
        result = formatter.format_stress_status(status)
        
        assert "ACTIVE" in result
        assert "1500.00 TL" in result
        assert "+1.50%" in result
        assert "1 / 3" in result
    
    def test_format_halted_status(self):
        """Test formatting halted trading status."""
        formatter = PortfolioFormatter()
        
        status = {
            "trading_halted": True,
            "halt_reason": "MAX_DAILY_LOSS",
            "daily_pnl": -5000.0,
            "daily_pnl_pct": -5.0,
            "daily_max_loss_remaining": 0.0,
            "consecutive_losses": 3,
            "consecutive_loss_limit": 3,
            "exposure_multiplier": 0.5,
            "effective_max_exposure": 40.0
        }
        
        result = formatter.format_stress_status(status)
        
        assert "HALTED" in result
        assert "MAX_DAILY_LOSS" in result
        assert "-5000.00 TL" in result


class TestFormatConfidenceAnalysis:
    """Test cases for confidence analysis formatting."""
    
    def test_format_confidence_analysis(self):
        """Test formatting confidence bucket analysis."""
        formatter = PortfolioFormatter()
        
        bucket_analysis = {
            "HIGH (>0.7)": {
                "count": 10,
                "win_rate": 70.0,
                "avg_return_pct": 2.5,
                "total_pnl": 1500.0
            },
            "MEDIUM (0.5-0.7)": {
                "count": 15,
                "win_rate": 60.0,
                "avg_return_pct": 1.8,
                "total_pnl": 1200.0
            }
        }
        
        signal_report = {
            "total_analyzed": 25,
            "correct_signal_correct_execution": {
                "count": 15,
                "pct": "60.0",
                "description": "Perfect trades"
            },
            "correct_signal_wrong_execution": {
                "count": 5,
                "pct": "20.0",
                "description": "Missed opportunities"
            }
        }
        
        result = formatter.format_confidence_analysis(bucket_analysis, signal_report)
        
        assert "CONFIDENCE BUCKET ANALYSIS" in result
        assert "HIGH (>0.7)" in result
        assert "70.0%" in result
        assert "Total Analyzed: 25" in result
        assert "Perfect trades" in result


class TestFormatPositionSummary:
    """Test cases for position summary formatting."""
    
    def test_format_empty_positions(self):
        """Test formatting empty positions."""
        formatter = PortfolioFormatter()
        
        result = formatter.format_position_summary({})
        
        assert result == "No open positions"
    
    def test_format_single_position(self):
        """Test formatting a single position."""
        formatter = PortfolioFormatter()
        
        positions = {
            "ASELS": {
                "side": "LONG",
                "entry_price": 40.0,
                "current_price": 45.0,
                "quantity": 100
            }
        }
        
        result = formatter.format_position_summary(positions)
        
        assert "ASELS" in result
        assert "LONG" in result
        assert "40.00" in result
        assert "45.00" in result
        assert "500.00" in result  # PnL
    
    def test_format_multiple_positions(self):
        """Test formatting multiple positions."""
        formatter = PortfolioFormatter()
        
        positions = {
            "ASELS": {
                "side": "LONG",
                "entry_price": 40.0,
                "current_price": 45.0,
                "quantity": 100
            },
            "THYAO": {
                "side": "SHORT",
                "entry_price": 100.0,
                "current_price": 95.0,
                "quantity": 50
            }
        }
        
        result = formatter.format_position_summary(positions)
        
        assert "ASELS" in result
        assert "THYAO" in result
        assert "LONG" in result
        assert "SHORT" in result
    
    def test_format_with_current_prices(self):
        """Test formatting with external current prices."""
        formatter = PortfolioFormatter()
        
        positions = {
            "ASELS": {
                "side": "LONG",
                "entry_price": 40.0,
                "current_price": 45.0,  # Will be overridden
                "quantity": 100
            }
        }
        
        current_prices = {"ASELS": 50.0}
        
        result = formatter.format_position_summary(positions, current_prices)
        
        assert "50.00" in result  # Uses external price
        assert "1000.00" in result  # PnL with new price


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_missing_trade_fields(self):
        """Test handling trades with missing fields."""
        formatter = PortfolioFormatter()
        
        trades = [{"symbol": "ASELS"}]  # Missing most fields
        
        ledger = formatter.get_trade_ledger(trades)
        
        assert len(ledger) == 1
        assert ledger[0]["symbol"] == "ASELS"
        assert ledger[0]["entry_price"] == 0
        assert ledger[0]["gross_pnl"] == 0
    
    def test_zero_commission_rate(self):
        """Test with zero commission rate."""
        formatter = PortfolioFormatter(commission_rate=0.0)
        
        trades = [{
            "symbol": "ASELS",
            "entry_price": 40.0,
            "exit_price": 45.0,
            "quantity": 100,
            "pnl": 500.0,
            "return_pct": 0.125,
            "entry_time": "2026-02-22T10:00:00",
            "exit_time": "2026-02-22T15:00:00",
            "holding_minutes": 300
        }]
        
        ledger = formatter.get_trade_ledger(trades)
        
        assert ledger[0]["commission"] == 0.0
        assert ledger[0]["net_pnl"] == 500.0
