from core.execution import ExecutionManager
import logging

# Configure simple logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ExecutionTest")

def test_execution_manager():
    log.info("Testing ExecutionManager...")
    
    # Initialize with default commission
    em = ExecutionManager(commission_rate=0.002)
    
    # Scenario 1: Basic Buy
    cash = 10000.0
    price = 50.0 # 50 TL per share
    
    # Calculate optimal lots
    lots = em.calculate_optimal_lots(price, cash)
    log.info(f"Price: {price}, Cash: {cash} -> Optimal Lots: {lots}")
    
    # Expected: 10000 / (50 * 1.002) = 10000 / 50.1 = 199.6 -> 199 lots
    expected_lots = int(10000 / (50 * 1.002))
    if lots == expected_lots:
        log.info("✅ Lot calculation correct.")
    else:
        log.error(f"❌ Lot calculation failed! Expected {expected_lots}, got {lots}")

    # Scenario 2: Validate Order - Success
    valid = em.validate_order("TEST", lots, price, cash)
    if valid:
        log.info("✅ Order validation passed for feasible trade.")
    else:
        log.error("❌ Order validation failed for feasible trade!")

    # Scenario 3: Validate Order - Insufficient Funds
    too_many_lots = lots + 1
    valid = em.validate_order("TEST", too_many_lots, price, cash)
    if not valid:
        log.info("✅ Order validation correctly rejected insufficient funds.")
    else:
        log.error("❌ Order validation passed for INSUFFICIENT funds!")

    # Scenario 4: Slippage Simulation
    slippage_price = em.simulate_slippage(price) # Removed lots argument if not needed
    log.info(f"Original Price: {price}, Slippage Price: {slippage_price}")
    if slippage_price > price:
         log.info("✅ Slippage applied correctly (price increased).")
    else:
         log.warning("⚠️ Slippage did not increase price (might be random?).")

    log.info("ExecutionManager Test Complete.")

if __name__ == "__main__":
    test_execution_manager()
