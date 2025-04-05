import time
import logging
import sys
import os
import threading

# Add the parent directory to the path so we can import our package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from src directly (match your project structure)
from src.interrupt_handler import InterruptSystem
from src.visualization import InterruptVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VisualizedExample")


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
    time.sleep(1.5)  # Simulate work
    logger.info("Low priority interrupt completed")


def trigger_interrupts():
    """
    Function to trigger interrupts after visualization starts.
    Run in a separate thread.
    """
    # Wait for visualization to initialize
    time.sleep(2)

    logger.info("Starting to trigger interrupts...")

    # First, trigger low priority
    system.trigger("low_priority", data="Initial low priority task")
    time.sleep(0.5)

    # This medium priority should preempt the low one
    system.trigger("medium_priority", data="Medium priority task")
    time.sleep(4)  # Wait for medium & high to complete

    # More low priority interrupts
    system.trigger("low_priority", data="Second low priority task")
    time.sleep(0.3)

    # Trigger a critical interrupt that preempts everything
    system.trigger("critical", data="Critical emergency")
    time.sleep(2)

    # Trigger several in sequence to show queueing
    system.trigger("low_priority", data="Queued low task 1")
    system.trigger("low_priority", data="Queued low task 2")
    system.trigger("medium_priority", data="Queued medium task")

    # Allow some time for processing the queued interrupts
    time.sleep(8)

    logger.info("Finished triggering interrupts")


if __name__ == "__main__":
    # Create interrupt system
    system = InterruptSystem()

    # Register interrupts with priorities
    system.register_interrupt("critical", 200, handle_high_priority)
    system.register_interrupt("high_priority", 100, handle_high_priority)
    system.register_interrupt("medium_priority", 50, handle_medium_priority)
    system.register_interrupt("low_priority", 10, handle_low_priority)

    # Create visualizer with shorter history window for better visibility
    visualizer = InterruptVisualizer(system, history_seconds=10)

    # Start trigger thread
    trigger_thread = threading.Thread(target=trigger_interrupts, daemon=True)
    trigger_thread.start()

    # Start visualization in main thread (this blocks until window is closed)
    logger.info("Starting visualization... (close window to exit)")
    visualizer.start()

    logger.info("Visualization closed, exiting...")