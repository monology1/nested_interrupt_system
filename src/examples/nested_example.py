"""
Clear example of nested interrupt handling that demonstrates the core concept.
"""

import time
import logging
import sys
import os
import threading
import matplotlib
matplotlib.use('TkAgg')  # Use TkAgg backend

# Add the parent directory to the path so we can import our package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.interrupt_handler import InterruptSystem
from src.visualization import InterruptVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NestedExample")

# Global system instance
system = InterruptSystem()

def handle_critical(interrupt):
    """Handler for critical priority interrupt."""
    logger.info(f"⚠️ CRITICAL INTERRUPT: {interrupt.name} with data: {interrupt.data}")
    logger.info(f"⚠️ Critical handler is running for 3 seconds...")
    time.sleep(3)  # Critical operations
    logger.info(f"⚠️ Critical interrupt completed")


def handle_high_priority(interrupt):
    """Handler for high priority interrupt."""
    logger.info(f"🔴 HIGH PRIORITY INTERRUPT: {interrupt.name} with data: {interrupt.data}")
    logger.info(f"🔴 High priority handler running for 2 seconds...")
    time.sleep(2)  # Simulate work
    logger.info(f"🔴 High priority interrupt completed")


def handle_medium_priority(interrupt):
    """Handler for medium priority interrupt."""
    logger.info(f"🟠 MEDIUM PRIORITY INTERRUPT: {interrupt.name} with data: {interrupt.data}")

    # First phase of medium priority work
    logger.info(f"🟠 Medium priority handler - first phase (2 seconds)...")
    time.sleep(2)

    # Trigger a high priority interrupt in the middle of processing
    logger.info(f"🟠 Medium priority handler - triggering high priority interrupt")
    system.trigger("high_priority", data="Nested trigger from medium")

    # This will be preempted if high priority interrupt is triggered
    logger.info(f"🟠 Medium priority handler - second phase (2 seconds)...")
    time.sleep(2)

    # Trigger critical interrupt to demonstrate multiple levels of nesting
    logger.info(f"🟠 Medium priority handler - triggering critical interrupt")
    system.trigger("critical", data="Nested trigger from medium")

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

    # This part will be preempted if any higher priority interrupts occur
    logger.info(f"🟢 Low priority handler - second phase (3 seconds)...")
    time.sleep(3)

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

    # Create visualizer
    visualizer = InterruptVisualizer(system, history_seconds=15)

    # Function to trigger interrupts after visualization starts
    def trigger_sequence():
        # Wait for visualization to initialize
        time.sleep(2)

        logger.info("Starting interrupt sequence...")

        # Start with a low priority interrupt
        logger.info("1. Triggering low priority interrupt")
        system.trigger("low_priority", data="Initial low priority task")
        time.sleep(1)  # Give time for low priority to start

        # Trigger medium priority which will preempt low
        logger.info("2. Triggering medium priority interrupt (should preempt low)")
        system.trigger("medium_priority", data="Medium priority task")

        # The medium handler will trigger high priority and critical
        # which will demonstrate nested interrupts

        # Wait for all processing to complete
        logger.info("Waiting for all interrupts to complete...")
        system.wait_for_completion(timeout=20)  # Wait up to 20 seconds

        logger.info("All interrupts completed. Sequence finished.")

    # Start trigger thread
    trigger_thread = threading.Thread(target=trigger_sequence, daemon=True)
    trigger_thread.start()

    try:
        # Start visualization in main thread
        logger.info("Starting visualization... (close window to exit)")
        visualizer.start(interval=200)  # Use slightly slower refresh rate for stability
    except Exception as e:
        logger.error(f"Error in visualization: {e}")
    finally:
        logger.info("Visualization closed, exiting...")


if __name__ == "__main__":
    run_demo()