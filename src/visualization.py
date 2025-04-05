"""
Fixed visualization module for the nested interrupt system.
"""

import time
import threading
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.animation as animation
import numpy as np
from collections import deque

# Set a lighter style for better visibility
plt.style.use('default')  # Reset to default style

class InterruptVisualizer:
    """
    Visualizes the state and flow of interrupts in real-time with a Gantt chart style.
    """

    def __init__(self, interrupt_system, history_seconds=15):
        """
        Initialize the visualizer.

        Args:
            interrupt_system: The InterruptSystem to visualize
            history_seconds: Number of seconds to show in history
        """
        self.system = interrupt_system
        self.history_seconds = history_seconds
        self.start_time = time.time()

        # History of interrupt events
        self.interrupt_events = []  # List of (time, interrupt_name, event_type, priority)
                                   # where event_type is 'start' or 'end'

        # Current state
        self.active_interrupts = {}  # name -> start_time

        # Setup figure with light background
        plt.rcParams.update({
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'savefig.facecolor': 'white',
            'text.color': 'black',
            'axes.labelcolor': 'black',
            'xtick.color': 'black',
            'ytick.color': 'black',
        })

        self.fig, self.ax = plt.subplots(figsize=(12, 7))
        self.fig.suptitle('Nested Interrupt System Timeline', fontsize=16)

        # Setup colors - use vibrant colors
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
                       '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
                       '#bcbd22', '#17becf']
        self.interrupt_colors = {}  # name -> color

        # Animation
        self.ani = None

        # Patch system methods to collect data
        self._patch_system()

    def _patch_system(self):
        """
        Patch the interrupt system to collect visualization data.
        """
        # Store original methods
        original_handle = self.system._handle_interrupt
        original_finish = self.system._finish_interrupt

        # Create wrapper for handle method
        def handle_wrapper(interrupt):
            current_time = time.time() - self.start_time

            # Record start event
            self.interrupt_events.append((current_time, interrupt.name, 'start', interrupt.priority))
            self.active_interrupts[interrupt.name] = current_time

            # Assign a color if not already assigned
            if interrupt.name not in self.interrupt_colors:
                # Assign a unique color based on priority or name
                if interrupt.name == "critical":
                    self.interrupt_colors[interrupt.name] = '#d62728'  # Red
                elif interrupt.name == "high_priority":
                    self.interrupt_colors[interrupt.name] = '#ff7f0e'  # Orange
                elif interrupt.name == "medium_priority":
                    self.interrupt_colors[interrupt.name] = '#2ca02c'  # Green
                elif interrupt.name == "low_priority":
                    self.interrupt_colors[interrupt.name] = '#1f77b4'  # Blue
                else:
                    color_idx = len(self.interrupt_colors) % len(self.colors)
                    self.interrupt_colors[interrupt.name] = self.colors[color_idx]

            # Call original method
            return original_handle(interrupt)

        # Create wrapper for finish method
        def finish_wrapper(interrupt):
            current_time = time.time() - self.start_time

            # Record end event
            self.interrupt_events.append((current_time, interrupt.name, 'end', interrupt.priority))

            # Remove from active
            if interrupt.name in self.active_interrupts:
                del self.active_interrupts[interrupt.name]

            # Call original method
            return original_finish(interrupt)

        # Apply patches
        self.system._handle_interrupt = handle_wrapper
        self.system._finish_interrupt = finish_wrapper

    def _update_plot(self, frame):
        """
        Update animation frame.
        """
        # Clear axes
        self.ax.clear()

        # Set up the plot
        self.ax.set_title('Interrupt Timeline (Higher = Higher Priority)')
        self.ax.set_xlabel('Time (seconds)')
        self.ax.set_ylabel('Interrupt Name (priority)')

        # Current time
        current_time = time.time() - self.start_time

        # Filter events for display window
        display_events = [e for e in self.interrupt_events if current_time - self.history_seconds <= e[0] <= current_time]

        # Get all unique interrupt names in display window, sorted by priority (highest first)
        active_names = set()

        # Add registered interrupts that might not have been triggered yet
        if hasattr(self.system, 'interrupts'):
            active_names.update(self.system.interrupts.keys())

        # Add names from display events
        for e in display_events:
            active_names.add(e[1])

        # Create name to priority mapping
        name_to_priority = {}
        for e in display_events:
            name_to_priority[e[1]] = e[3]

        # Add priorities for registered interrupts
        if hasattr(self.system, 'interrupts'):
            for name, interrupt in self.system.interrupts.items():
                name_to_priority[name] = interrupt.priority

        sorted_names = sorted(active_names, key=lambda name: name_to_priority.get(name, 0), reverse=True)

        # Create y-position mapping
        name_to_y = {name: i for i, name in enumerate(sorted_names)}

        # Draw periods when interrupts were active
        active_periods = {}  # name -> list of (start, end) tuples

        # Process events to build active periods
        for i, event in enumerate(display_events):
            timestamp, name, event_type, _ = event

            if event_type == 'start':
                # Find the matching end event
                end_time = None
                for j in range(i+1, len(display_events)):
                    if (display_events[j][1] == name and
                        display_events[j][2] == 'end'):
                        end_time = display_events[j][0]
                        break

                # If no end found, use current time (still active)
                if end_time is None and name in self.active_interrupts:
                    end_time = current_time

                if end_time is not None:
                    if name not in active_periods:
                        active_periods[name] = []
                    active_periods[name].append((timestamp, end_time))

        # Also draw currently active interrupts that don't have a start in our window
        for name, start_time in self.active_interrupts.items():
            if name not in active_periods:
                active_periods[name] = []

            # Check if this period is already represented
            is_represented = False
            for start, end in active_periods.get(name, []):
                if abs(start - start_time) < 0.01:  # Close enough to be the same period
                    is_represented = True
                    break

            if not is_represented:
                # Only add the part visible in our window
                visible_start = max(start_time, current_time - self.history_seconds)
                active_periods[name].append((visible_start, current_time))

        # Draw active periods as rectangles
        for name, periods in active_periods.items():
            if name not in name_to_y:
                # This can happen if we have active interrupts not in our display window
                # Add it to our y-position mapping
                name_to_y[name] = len(name_to_y)

            y_pos = name_to_y[name]

            # Ensure we have a color for this interrupt
            if name not in self.interrupt_colors:
                color_idx = len(self.interrupt_colors) % len(self.colors)
                self.interrupt_colors[name] = self.colors[color_idx]

            color = self.interrupt_colors.get(name, 'gray')

            for start, end in periods:
                if start >= end:
                    continue  # Skip invalid periods

                rect = Rectangle((start, y_pos - 0.3), end - start, 0.6,
                                color=color, alpha=0.7)
                self.ax.add_patch(rect)

                # Add interrupt name if it's long enough to fit text
                if end - start > 0.5:
                    self.ax.text(start + (end - start)/2, y_pos,
                               name.replace('_', ' ').title(),
                               ha='center', va='center', color='white',
                               fontweight='bold', fontsize=9)

        # Add y-axis labels with priorities
        yticks = []
        yticklabels = []

        # Ensure we have all sorted_names in our mapping
        for name in sorted(name_to_y.keys(), key=lambda n: name_to_priority.get(n, 0), reverse=True):
            y_pos = name_to_y[name]
            yticks.append(y_pos)

            # Get priority if available
            priority = name_to_priority.get(name, 0)
            if name in self.system.interrupts:
                priority = self.system.interrupts[name].priority

            yticklabels.append(f"{name} (p={priority})")

        self.ax.set_yticks(yticks)
        self.ax.set_yticklabels(yticklabels)

        # Set x-axis limits
        self.ax.set_xlim(current_time - self.history_seconds, current_time + 0.5)

        # Set y-axis limits with some padding
        if name_to_y:
            self.ax.set_ylim(-0.5, len(name_to_y) - 0.5)
        else:
            self.ax.set_ylim(-0.5, 3.5)  # Default if no interrupts

        # Add a moving time indicator (vertical line)
        self.ax.axvline(x=current_time, color='red', linestyle='--', alpha=0.7)

        # Add 'Now' label
        self.ax.text(current_time, -0.5, 'Now',
                   ha='center', va='bottom', color='red',
                   fontweight='bold')

        # Add grid for better readability
        self.ax.grid(True, linestyle='--', alpha=0.3)

        # Draw early message if no events
        if not display_events and not self.active_interrupts:
            self.ax.text(current_time - self.history_seconds/2, len(sorted_names)/2 if sorted_names else 1.5,
                       "Waiting for interrupts...",
                       ha='center', va='center', color='gray',
                       fontsize=14, alpha=0.7)

    def start(self, interval=100):
        """
        Start the visualization.

        Args:
            interval: Update interval in milliseconds
        """
        # Create animation with explicit save_count to avoid warning
        self.ani = animation.FuncAnimation(
            self.fig, self._update_plot, interval=interval,
            cache_frame_data=False,  # Disable frame caching
            save_count=100  # Limit saved frames
        )

        plt.tight_layout()
        plt.subplots_adjust(top=0.92)  # Make room for the title

        # Draw initial frame to make sure something is visible
        self._update_plot(0)

        # Use blocking show to keep window open
        plt.show(block=True)

    def stop(self):
        """
        Stop the visualization.
        """
        if self.ani:
            self.ani.event_source.stop()

    def save_snapshot(self, filename="interrupt_timeline.png"):
        """
        Save current visualization state to file.

        Args:
            filename: Output filename
        """
        self._update_plot(0)
        plt.tight_layout()
        plt.savefig(filename)
        print(f"Saved visualization to {filename}")