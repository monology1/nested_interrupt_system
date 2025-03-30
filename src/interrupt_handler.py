"""
Interrupt handler system implementation.
"""

import threading
import logging
from .priority_queue import PriorityQueue
from .interrupt import Interrupt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("InterruptSystem")


class InterruptHandler:
    """
    Handles a specific type of interrupt.
    """

    def __init__(self, interrupt_name, callback=None):
        """
        Initialize an interrupt handler.

        Args:
            interrupt_name (str): Name of the interrupt this handles
            callback (callable): Function to call when this interrupt is triggered
        """
        self.interrupt_name = interrupt_name
        self.callback = callback

    def handle(self, interrupt):
        """
        Handle the given interrupt.

        Args:
            interrupt (Interrupt): The interrupt to handle

        Returns:
            bool: True if handled successfully, False otherwise
        """
        if self.callback is not None:
            try:
                self.callback(interrupt)
                return True
            except Exception as e:
                logger.error(f"Error handling interrupt {interrupt.name}: {e}")
                return False

        logger.warning(f"No callback defined for interrupt {interrupt.name}")
        return False


class InterruptSystem:
    """
    System for managing nested interrupts with different priority levels.
    """

    def __init__(self):
        """Initialize the interrupt system."""
        self.interrupts = {}  # name -> Interrupt
        self.handlers = {}  # name -> InterruptHandler
        self.pending_queue = PriorityQueue()
        self.active_stack = []
        self.global_mask = False
        self._lock = threading.RLock()

    def register_interrupt(self, name, priority, handler=None):
        """
        Register a new interrupt type.

        Args:
            name (str): Unique name for the interrupt
            priority (int): Priority level (higher is more important)
            handler (callable, optional): Function to handle this interrupt

        Returns:
            Interrupt: The registered interrupt
        """
        with self._lock:
            if name in self.interrupts:
                logger.warning(f"Interrupt {name} already registered, updating priority")
                self.interrupts[name].priority = priority
                return self.interrupts[name]

            interrupt = Interrupt(name, priority)
            self.interrupts[name] = interrupt

            if handler:
                self.register_handler(name, handler)

            logger.info(f"Registered interrupt: {interrupt}")
            return interrupt

    def register_handler(self, interrupt_name, callback):
        """
        Register a handler for an interrupt.

        Args:
            interrupt_name (str): Name of the interrupt
            callback (callable): Function to call when interrupt is triggered

        Returns:
            InterruptHandler: The registered handler
        """
        with self._lock:
            handler = InterruptHandler(interrupt_name, callback)
            self.handlers[interrupt_name] = handler

            logger.info(f"Registered handler for interrupt: {interrupt_name}")
            return handler

    def trigger(self, interrupt_name, data=None):
        """
        Trigger an interrupt by name.

        Args:
            interrupt_name (str): Name of the interrupt to trigger
            data (any, optional): Data to associate with this interrupt instance

        Returns:
            bool: True if the interrupt was triggered, False otherwise
        """
        with self._lock:
            if self.global_mask:
                logger.info(f"Interrupt {interrupt_name} ignored (globally masked)")
                return False

            if interrupt_name not in self.interrupts:
                logger.error(f"Unknown interrupt: {interrupt_name}")
                return False

            interrupt = self.interrupts[interrupt_name]

            if interrupt.is_masked:
                logger.info(f"Interrupt {interrupt_name} ignored (masked)")
                return False

            # Create a new instance of the interrupt with the provided data
            instance = Interrupt(
                interrupt.name,
                interrupt.priority,
                handler=interrupt.handler,
                data=data
            )

            # Add to pending queue
            self.pending_queue.push(instance, instance.priority)
            logger.info(f"Triggered interrupt: {instance}")

            # Process pending interrupts
            self._process_pending()
            return True

    def _process_pending(self):
        """
        Process pending interrupts according to priority.
        """
        with self._lock:
            # If there are no pending interrupts, return
            if self.pending_queue.is_empty():
                return

            # Get the highest priority pending interrupt
            pending = self.pending_queue.peek()

            # If there's an active interrupt, check priority
            if self.active_stack:
                current = self.active_stack[-1]

                # If pending has higher priority, interrupt current
                if pending.priority > current.priority:
                    self._handle_interrupt(pending)
                # Otherwise, leave in queue for later
            else:
                # No active interrupts, handle the pending one
                self._handle_interrupt(pending)

    def _handle_interrupt(self, interrupt):
        """
        Handle an interrupt by calling its handler.

        Args:
            interrupt (Interrupt): The interrupt to handle
        """
        with self._lock:
            # Remove from pending queue
            self.pending_queue.pop()

            # Set as active
            interrupt.is_active = True
            self.active_stack.append(interrupt)

            logger.info(f"Handling interrupt: {interrupt}")

            # Find the handler
            handler = self.handlers.get(interrupt.name)

            if handler:
                # Handle in a new thread to allow for non-blocking operation
                threading.Thread(
                    target=self._execute_handler,
                    args=(handler, interrupt),
                    daemon=True
                ).start()
            else:
                logger.warning(f"No handler for interrupt: {interrupt.name}")
                self._finish_interrupt(interrupt)

    def _execute_handler(self, handler, interrupt):
        """
        Execute the interrupt handler and mark as complete when done.

        Args:
            handler (InterruptHandler): The handler to execute
            interrupt (Interrupt): The interrupt being handled
        """
        try:
            handler.handle(interrupt)
        except Exception as e:
            logger.error(f"Error in interrupt handler for {interrupt.name}: {e}")
        finally:
            self._finish_interrupt(interrupt)

    def _finish_interrupt(self, interrupt):
        """
        Mark an interrupt as finished and process any pending interrupts.

        Args:
            interrupt (Interrupt): The interrupt that has finished
        """
        with self._lock:
            # Remove from active stack
            if interrupt in self.active_stack:
                self.active_stack.remove(interrupt)

            interrupt.is_active = False
            logger.info(f"Finished interrupt: {interrupt}")

            # Process any pending interrupts
            self._process_pending()

    def mask_interrupt(self, interrupt_name, masked=True):
        """
        Mask or unmask a specific interrupt.

        Args:
            interrupt_name (str): Name of the interrupt
            masked (bool): Whether to mask (True) or unmask (False)

        Returns:
            bool: True if successful, False otherwise
        """
        with self._lock:
            if interrupt_name not in self.interrupts:
                logger.error(f"Unknown interrupt: {interrupt_name}")
                return False

            self.interrupts[interrupt_name].is_masked = masked
            action = "Masked" if masked else "Unmasked"
            logger.info(f"{action} interrupt: {interrupt_name}")
            return True

    def mask_all(self, masked=True):
        """
        Mask or unmask all interrupts globally.

        Args:
            masked (bool): Whether to mask (True) or unmask (False)
        """
        with self._lock:
            self.global_mask = masked
            action = "Masked" if masked else "Unmasked"
            logger.info(f"{action} all interrupts")