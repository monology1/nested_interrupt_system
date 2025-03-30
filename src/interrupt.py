"""
Interrupt class definition.
"""


class Interrupt:
    """
    Represents an interrupt with a priority level and handler function.

    Higher priority value means the interrupt is more important.
    """

    def __init__(self, name, priority, handler=None, data=None):
        """
        Initialize an interrupt.

        Args:
            name (str): Name of the interrupt
            priority (int): Priority level (higher is more important)
            handler (callable, optional): Function to call when interrupt is triggered
            data (any, optional): Data to pass to the handler
        """
        self.name = name
        self.priority = priority
        self.handler = handler
        self.data = data
        self.is_active = False
        self.is_masked = False

    def __lt__(self, other):
        """
        Comparison for priority queue ordering.
        Higher priority means it should be processed first.
        """
        return self.priority > other.priority

    def __str__(self):
        return f"Interrupt({self.name}, priority={self.priority}, active={self.is_active})"