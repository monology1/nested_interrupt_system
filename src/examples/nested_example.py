"""
Enhanced example of nested interrupt handling with additional priority scenarios.
"""

import time
import logging
import sys
import os
import threading
import matplotlib
matplotlib.use('MacOSX')  # Use MacOSX backend

# Add the parent directory to the path so we can import our package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.interrupt_handler import InterruptSystem
from src.visualization import InterruptVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EnhancedPriorityExample")

# Global system instance
system = InterruptSystem()

# Add a very low priority interrupt
def handle_lowest_priority(interrupt):
    """Handler for the absolute lowest priority interrupt."""
    logger.info(f"🔵 LOWEST PRIORITY INTERRUPT: {interrupt.name} with data: {interrupt.data}")
    logger.info(f"🔵 Lowest priority handler - first phase (1 second)...")
    time.sleep(1)

    # Try triggering different priority interrupts during lowest priority
    logger.info(f"🔵 Lowest priority handler - triggering LOW priority interrupt")
    system.trigger("low_priority", data="From lowest handler")

    logger.info(f"🔵 Lowest priority handler - second phase (1 second)...")
    time.sleep(1)

    logger.info(f"🔵 Lowest priority handler - triggering MEDIUM priority interrupt")
    system.trigger("medium_priority", data="From lowest handler")

    # This will be preempted by higher priority interrupts
    logger.info(f"🔵 Lowest priority handler - final phase (2 seconds)...")
    time.sleep(2)
    logger.info(f"🔵 Lowest priority interrupt completed")


def handle_critical(interrupt):
    """Handler for critical priority interrupt."""
    logger.info(f"⚠️ CRITICAL INTERRUPT: {interrupt.name} with data: {interrupt.data}")
    logger.info(f"⚠️ Critical handler is running for 3 seconds...")

    # Try triggering lower priority during critical
    time.sleep(1.5)
    logger.info(f"⚠️ Critical handler - triggering LOW priority interrupt")
    system.trigger("low_priority", data="From critical handler (should queue)")

    time.sleep(1.5)  # Critical operations
    logger.info(f"⚠️ Critical interrupt completed")


def handle_high_priority(interrupt):
    """Handler for high priority interrupt."""
    logger.info(f"🔴 HIGH PRIORITY INTERRUPT: {interrupt.name} with data: {interrupt.data}")
    logger.info(f"🔴 High priority handler running for 2 seconds...")

    # Try triggering both higher and lower priority during high
    time.sleep(0.5)
    logger.info(f"🔴 High priority handler - triggering LOWEST priority interrupt")
    system.trigger("lowest_priority", data="From high handler (should queue)")

    time.sleep(1.0)
    logger.info(f"🔴 High priority handler - triggering CRITICAL priority interrupt")
    system.trigger("critical", data="From high handler (should preempt)")

    time.sleep(0.5)  # This will be preempted by critical
    logger.info(f"🔴 High priority interrupt completed")


def handle_medium_priority(interrupt):
    """Handler for medium priority interrupt."""
    logger.info(f"🟠 MEDIUM PRIORITY INTERRUPT: {interrupt.name} with data: {interrupt.data}")

    # First phase of medium priority work
    logger.info(f"🟠 Medium priority handler - first phase (2 seconds)...")
    time.sleep(2)

    # Trigger a high priority interrupt in the middle of processing
    logger.info(f"🟠 Medium priority handler - triggering high priority interrupt")
    system.trigger("high_priority", data="From medium handler (should preempt)")

    # This will be preempted if high priority interrupt is triggered
    logger.info(f"🟠 Medium priority handler - second phase (2 seconds)...")
    time.sleep(2)

    # Simultaneously trigger multiple interrupts with different priorities
    logger.info(f"🟠 Medium priority handler - triggering multiple interrupts simultaneously")
    system.trigger("lowest_priority", data="Part of simultaneous trigger")
    system.trigger("low_priority", data="Part of simultaneous trigger")
    system.trigger("critical", data="Part of simultaneous trigger (should be handled first)")

    # Final phase that will be preempted by critical interrupt
    logger.info(f"🟠 Medium priority handler - final phase (1 second)...")
    time.sleep(1)

    logger.info(f"🟠 Medium priority interrupt completed")


def handle_low_priority(interrupt):
    """Handler for low priority interrupt."""
    logger.info(f"🟢 LOW PRIORITY INTERRUPT: {interrupt.name} with data: {interrupt.data}")

    # First phase of low priority work
    logger.info(f"🟢 Low priority handler - first phase (1 second)...")
    time.sleep(1)

    # Try to interrupt self with same priority
    logger.info(f"🟢 Low priority handler - triggering another LOW priority interrupt")
    system.trigger("low_priority", data="Same priority interrupt (should queue)")

    # This part will be preempted if any higher priority interrupts occur
    logger.info(f"🟢 Low priority handler - second phase (1.5 seconds)...")
    time.sleep(1.5)

    # Trigger rapid sequence of different priorities
    logger.info(f"🟢 Low priority handler - triggering rapid sequence of interrupts")
    system.trigger("medium_priority", data="Rapid sequence")
    system.trigger("lowest_priority", data="Rapid sequence")
    system.trigger("high_priority", data="Rapid sequence")

    # This will likely be preempted multiple times
    logger.info(f"🟢 Low priority handler - final phase (1.5 seconds)...")
    time.sleep(1.5)

    logger.info(f"🟢 Low priority interrupt completed")


def run_demo():
    """
    Main demo function to run the visualization and trigger the interrupts.
    """
    # Register interrupts with priorities
    system.register_interrupt("critical", 200, handle_critical)
    system.register_interrupt("high_priority", 100, handle_high_priority)
    system.register_interrupt("medium_priority", 50, handle_medium_priority)
    system.register_interrupt("low_priority", 10, handle_low_priority)
    system.register_interrupt("lowest_priority", 5, handle_lowest_priority)

    # Create visualizer
    visualizer = InterruptVisualizer(system, history_seconds=30)

    # Function to trigger interrupts after visualization starts
    def trigger_sequence():
        # Wait for visualization to initialize
        time.sleep(2)

        logger.info("\n" + "="*60)
        logger.info("STARTING ENHANCED PRIORITY DEMONSTRATION")
        logger.info("="*60)

        # SCENARIO 1: Start with lowest, then trigger higher priorities
        logger.info("\nSCENARIO 1: Starting with lowest priority")
        system.trigger("lowest_priority", data="Initial lowest priority task")
        time.sleep(1)  # Give time for lowest priority to start

        # SCENARIO 2: Trigger same priority interrupts in sequence
        logger.info("\nSCENARIO 2: Triggering same priority in sequence")
        system.trigger("low_priority", data="First low priority task")
        system.trigger("low_priority", data="Second low priority task")
        time.sleep(2)  # Allow time for processing

        # SCENARIO 3: Complex nested interruption
        logger.info("\nSCENARIO 3: Complex nested interruption scenario")
        system.trigger("medium_priority", data="Starting complex scenario")
        # The medium handler will trigger high, which triggers critical

        # SCENARIO 4: Rapid-fire priority testing
        time.sleep(10)  # Wait for earlier scenarios to progress
        logger.info("\nSCENARIO 4: Rapid-fire priority testing")
        system.trigger("lowest_priority", data="Rapid fire test")
        system.trigger("critical", data="Rapid fire test")
        system.trigger("medium_priority", data="Rapid fire test")
        system.trigger("high_priority", data="Rapid fire test")

        # SCENARIO 5: Priority inversion test
        time.sleep(5)
        logger.info("\nSCENARIO 5: Testing priority handling under load")
        # First trigger lowest, then rapidly trigger others to test queue processing
        system.trigger("lowest_priority", data="Priority test - should be handled last")
        time.sleep(0.1)
        system.trigger("high_priority", data="Priority test - should preempt lower")
        time.sleep(0.1)
        system.trigger("critical", data="Priority test - should preempt all")
        time.sleep(0.1)
        system.trigger("medium_priority", data="Priority test - should wait for high")
        time.sleep(0.1)
        system.trigger("low_priority", data="Priority test - should wait for medium")

        # Wait for all processing to complete
        logger.info("\nWaiting for all interrupts to complete...")
        system.wait_for_completion(timeout=40)  # Wait up to 40 seconds for completion

        logger.info("\n" + "="*60)
        logger.info("PRIORITY DEMONSTRATION COMPLETED")
        logger.info("="*60)
        logger.info("\nKey observations:")
        logger.info("1. Higher priority interrupts always preempt lower priority ones")
        logger.info("2. Lower priority interrupts are queued when higher ones are active")
        logger.info("3. Same priority interrupts are processed in sequence (FIFO)")
        logger.info("4. The interrupt system maintains correct priority ordering under load")
        logger.info("5. Nested interrupts can go multiple levels deep")

    # Start trigger thread
    trigger_thread = threading.Thread(target=trigger_sequence, daemon=True)
    trigger_thread.start()

    try:
        # Start visualization in main thread
        logger.info("Starting visualization... (close window to exit)")
        visualizer.start(interval=150)  # Use slightly faster refresh rate
    except Exception as e:
        logger.error(f"Error in visualization: {e}")
    finally:
        logger.info("Visualization closed, exiting...")


if __name__ == "__main__":
    run_demo()