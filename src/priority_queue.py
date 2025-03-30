"""
Priority queue implementation for managing interrupts.
"""

import heapq


class PriorityQueue:
    """
    A priority queue for interrupts.
    """

    def __init__(self):
        self._queue = []
        self._entry_counter = 0

    def push(self, item, priority):
        """
        Add an item to the queue with given priority.

        Args:
            item: The item to add
            priority (int): The priority (higher means more important)
        """
        # Use negative priority since heapq is a min-heap
        # and we want higher priorities first
        heapq.heappush(self._queue, (-priority, self._entry_counter, item))
        self._entry_counter += 1

    def pop(self):
        """
        Remove and return the highest priority item.

        Returns:
            The item with highest priority or None if queue is empty
        """
        if not self._queue:
            return None

        _, _, item = heapq.heappop(self._queue)
        return item

    def peek(self):
        """
        Return (but don't remove) the highest priority item.

        Returns:
            The item with highest priority or None if queue is empty
        """
        if not self._queue:
            return None

        _, _, item = self._queue[0]
        return item

    def is_empty(self):
        """
        Check if the queue is empty.

        Returns:
            bool: True if empty, False otherwise
        """
        return len(self._queue) == 0

    def __len__(self):
        return len(self._queue)