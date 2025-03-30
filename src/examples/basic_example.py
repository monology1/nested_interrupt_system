"""
Basic example of using the nested interrupt system.
"""

import time
import logging
import sys
import os

# Add the parent directory to the path so we can import our package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.interrupt_handler import InterruptSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Example")


def handle_high_priority(interrupt):
    """Handler for high priority interrupt."""
    logger.info(f"HIGH PRIORITY INTERRUPT: {interrupt.name} with data: {interrupt.data}")
    time.sleep(2)  # Simulate work
    logger.info("High priority interrupt completed")


def handle_medium_priority(interrupt):
    """Handler for medium priority interrupt."""
    logger.info(f"MEDIUM PRIORITY INTERRUPT: {interrupt.name} with data: {interrupt.data}")
    time.sleep(3)  # Simulate work

    # Trigger a high priority interrupt in the middle of processing
    logger.info("Triggering high priority interrupt from within medium handler")
    system.trigger("high_priority", data="Nested call from medium")

    time.sleep(2)  # Continue working
    logger.info("Medium priority interrupt completed")


def handle_low_priority(interrupt):
    """Handler for low priority interrupt."""
    logger.info(f"LOW PRIORITY INTERRUPT: {interrupt.name} with data: {interrupt.data}")
    time.sleep(1)  # Simulate work
    logger.info("Low priority interrupt completed")


if __name__ == "__main__":
    # Create interrupt system
    system = InterruptSystem()

    # Register interrupts with priorities
    system.register_interrupt("high_priority", 100, handle_high_priority)
    system.register_interrupt("medium_priority", 50, handle_medium_priority)
    system.register_interrupt("low_priority", 10, handle_low_priority)

    # Trigger interrupts in sequence
    logger.info("Starting example...")

    system.trigger("low_priority", data="Initial low priority task")
    time.sleep(0.5)

    # This should interrupt the low priority one
    system.trigger("medium_priority", data="Medium priority task")
    time.sleep(0.5)

    # This will demonstrate nested interrupts, as the medium handler
    # also triggers the high priority interrupt

    time.sleep(10)  # Wait for all to complete

    logger.info("Example completed.")