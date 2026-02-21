"""
Property-based tests for PortfolioRepository.

Uses Hypothesis to test universal properties that should hold for all inputs.
These tests validate correctness properties across many generated test cases.
"""

import pytest
from hypothesis import given, strategies as st, settings
from pathlib import Path
import tempfile
import os
from paper_trading.portfolio.portfolio_repository import PortfolioRepository


# ============================================================================
# HYPOTHESIS STRATEGIES
# ============================================================================

# Strategy for generating valid portfolio positions
position_strategy = st.fixed_dictionaries({
    "quantity": st.floats(min_value=1, max_value=10000, allow_nan=False, allow_infinity=False),
    "entry_price": st.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False),
    "current_price": st.floats(min_value=0.01, max_value=1000, allow_nan=False, allow_infinity=False),
})

# Strategy for generating trade history entries
trade_strategy = st.fixed_dictionaries({
    "symbol": st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=3, max_size=6),
    "pnl": st.floats(min_value=-10000, max_value=10000, allow_nan=False, allow_infinity=False),
    "date": st.text(min_size=10, max_size=10),  # Simple date string
})

# Strategy for generating complete portfolio state
portfolio_state_strategy = st.fixed_dictionaries({
    "cash": st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False),
    "positions": st.dictionaries(
        keys=st.text(alphabet=st.characters(whitelist_categories=("Lu",)), min_size=3, max_size=6),
        values=position_strategy,
        max_size=10
    ),
    "realized_pnl": st.floats(min_value=-100000, max_value=100000, allow_nan=False, allow_infinity=False),
    "trade_history": st.lists(trade_strategy, max_size=20),
    "closed_trades": st.lists(trade_strategy, max_size=20),
    "peak_equity": st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False),
})


# ============================================================================
# PROPERTY 4: STATE SERIALIZATION ROUND-TRIP
# ============================================================================

class TestStateSerializationRoundTrip:
    """
    Property 4: State Serialization Round-Trip
    
    Validates: Requirements 1.5
    
    For any portfolio state, serialize then deserialize should preserve all data.
    This property ensures that no data is lost during save/load operations.
    """
    
    @given(state=portfolio_state_strategy)
    @settings(max_examples=100, deadline=None)
    def test_save_load_preserves_all_data(self, state):
        """
        Property: For any state S, load(save(S)) == S
        
        This tests that the serialization round-trip preserves all data exactly.
        """
        # Setup
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            repo = PortfolioRepository(state_file)
            
            # Test: Save then load
            save_result = repo.save(state)
            assert save_result is True, "Save should succeed"
            
            loaded_state = repo.load()
            assert loaded_state is not None, "Load should return state"
            
            # Property: Loaded state equals original state
            assert loaded_state == state, "Round-trip should preserve all data"
            
            # Verify individual fields
            assert loaded_state["cash"] == state["cash"]
            assert loaded_state["positions"] == state["positions"]
            assert loaded_state["realized_pnl"] == state["realized_pnl"]
            assert loaded_state["trade_history"] == state["trade_history"]
            assert loaded_state["closed_trades"] == state["closed_trades"]
            assert loaded_state["peak_equity"] == state["peak_equity"]
    
    @given(state=portfolio_state_strategy)
    @settings(max_examples=100, deadline=None)
    def test_multiple_saves_are_idempotent(self, state):
        """
        Property: save(S); save(S); load() == save(S); load()
        
        Multiple saves of the same state should be idempotent.
        """
        # Setup
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            repo = PortfolioRepository(state_file)
            
            # Test: Save once
            repo.save(state)
            loaded_once = repo.load()
            
            # Save again (should overwrite)
            repo.save(state)
            loaded_twice = repo.load()
            
            # Property: Both loads should return identical data
            assert loaded_once == loaded_twice
            assert loaded_twice == state
    
    @given(
        state1=portfolio_state_strategy,
        state2=portfolio_state_strategy
    )
    @settings(max_examples=50, deadline=None)
    def test_save_overwrites_previous_state(self, state1, state2):
        """
        Property: save(S1); save(S2); load() == S2
        
        Saving a new state should completely overwrite the previous state.
        """
        # Setup
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            repo = PortfolioRepository(state_file)
            
            # Test: Save first state
            repo.save(state1)
            
            # Save second state (should overwrite)
            repo.save(state2)
            
            # Load
            loaded = repo.load()
            
            # Property: Loaded state should be state2, not state1
            assert loaded == state2
            assert loaded != state1 or state1 == state2  # Unless they're equal
    
    @given(state=portfolio_state_strategy)
    @settings(max_examples=100, deadline=None)
    def test_numeric_precision_preserved(self, state):
        """
        Property: Numeric values maintain precision through serialization.
        
        Float values should be preserved with reasonable precision.
        """
        # Setup
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            repo = PortfolioRepository(state_file)
            
            # Test: Save and load
            repo.save(state)
            loaded = repo.load()
            
            # Property: Numeric values should be very close (within floating point precision)
            assert abs(loaded["cash"] - state["cash"]) < 1e-10
            assert abs(loaded["realized_pnl"] - state["realized_pnl"]) < 1e-10
            assert abs(loaded["peak_equity"] - state["peak_equity"]) < 1e-10
            
            # Check positions
            for symbol in state["positions"]:
                if symbol in loaded["positions"]:
                    orig_pos = state["positions"][symbol]
                    load_pos = loaded["positions"][symbol]
                    assert abs(load_pos["quantity"] - orig_pos["quantity"]) < 1e-10
                    assert abs(load_pos["entry_price"] - orig_pos["entry_price"]) < 1e-10


# ============================================================================
# PROPERTY: SERIALIZATION INVARIANTS
# ============================================================================

class TestSerializationInvariants:
    """
    Additional invariants that should hold for serialization.
    """
    
    @given(state=portfolio_state_strategy)
    @settings(max_examples=100, deadline=None)
    def test_state_keys_preserved(self, state):
        """
        Property: All keys in original state exist in loaded state.
        """
        # Setup
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            repo = PortfolioRepository(state_file)
            
            # Test
            repo.save(state)
            loaded = repo.load()
            
            # Property: All original keys should exist in loaded state
            for key in state.keys():
                assert key in loaded, f"Key '{key}' should be preserved"
    
    @given(state=portfolio_state_strategy)
    @settings(max_examples=100, deadline=None)
    def test_position_symbols_preserved(self, state):
        """
        Property: All position symbols are preserved.
        """
        # Setup
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            repo = PortfolioRepository(state_file)
            
            # Test
            repo.save(state)
            loaded = repo.load()
            
            # Property: All position symbols should be preserved
            original_symbols = set(state["positions"].keys())
            loaded_symbols = set(loaded["positions"].keys())
            assert original_symbols == loaded_symbols
    
    @given(state=portfolio_state_strategy)
    @settings(max_examples=100, deadline=None)
    def test_trade_history_length_preserved(self, state):
        """
        Property: Trade history length is preserved.
        """
        # Setup
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            repo = PortfolioRepository(state_file)
            
            # Test
            repo.save(state)
            loaded = repo.load()
            
            # Property: Trade history should have same length
            assert len(loaded["trade_history"]) == len(state["trade_history"])
            assert len(loaded["closed_trades"]) == len(state["closed_trades"])


# ============================================================================
# PROPERTY: FILE SYSTEM INVARIANTS
# ============================================================================

class TestFileSystemInvariants:
    """
    Properties related to file system operations.
    """
    
    @given(state=portfolio_state_strategy)
    @settings(max_examples=50, deadline=None)
    def test_save_creates_file(self, state):
        """
        Property: Save operation always creates a file.
        """
        # Setup
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "test_state.json")
            repo = PortfolioRepository(state_file)
            
            # Verify file doesn't exist initially
            assert not os.path.exists(state_file)
            
            # Test
            result = repo.save(state)
            
            # Property: File should exist after save
            assert result is True
            assert os.path.exists(state_file)
    
    @given(state=portfolio_state_strategy)
    @settings(max_examples=50, deadline=None)
    def test_save_creates_parent_directories(self, state):
        """
        Property: Save creates parent directories if they don't exist.
        """
        # Setup
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = os.path.join(tmpdir, "nested", "dir", "test_state.json")
            repo = PortfolioRepository(state_file)
            
            # Verify parent directories don't exist
            parent_dir = os.path.dirname(state_file)
            assert not os.path.exists(parent_dir)
            
            # Test
            result = repo.save(state)
            
            # Property: Parent directories should be created
            assert result is True
            assert os.path.exists(parent_dir)
            assert os.path.exists(state_file)
