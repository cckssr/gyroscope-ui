#!/usr/bin/env python3
"""
Debug script to check DataController queue processing.
"""

import sys
import time

# Add the project root to Python path
sys.path.insert(0, "/Users/cedric.kessler/TU_Berlin_offline/TutorGP/HRNGGUI")

# Create QApplication for QTimer support
try:
    from PySide6.QtWidgets import QApplication

    app = (
        QApplication(sys.argv)
        if not QApplication.instance()
        else QApplication.instance()
    )
except:
    app = None

from src.plot import PlotWidget
from src.data_controller import DataController


def debug_data_controller():
    """Debug the DataController queue processing."""
    print("Debugging DataController...")

    # Create a simple plot widget
    plot = PlotWidget(max_plot_points=50, title="Debug Test")

    # Create data controller
    controller = DataController(
        plot_widget=plot,
        display_widget=None,
        history_widget=None,
        max_history=50,
        gui_update_interval=100,
    )

    print(f"Timer created: {controller.gui_update_timer is not None}")
    print(
        f"Timer active: {controller.gui_update_timer.isActive() if controller.gui_update_timer else 'N/A'}"
    )

    # Add some data points
    print("Adding data points...")
    for i in range(10):
        controller.add_data_point_fast(i, float(i * 2))

    print(f"Queue size after adding: {controller.data_queue.qsize()}")
    print(f"Data points in controller: {len(controller.data_points)}")
    print(f"Total points received: {controller._total_points_received}")

    # Wait a bit for timer processing
    if controller.gui_update_timer and app:
        print("Waiting for timer processing...")
        # Process events to allow timer to fire
        for _ in range(5):  # Wait up to 500ms
            app.processEvents()
            time.sleep(0.1)
    else:
        print("Manual processing...")
        controller._process_queued_data()

    print(f"Queue size after processing: {controller.data_queue.qsize()}")
    print(f"Data points in controller: {len(controller.data_points)}")
    print(f"Plot data count: {plot._data_count}")

    # Clean up
    controller.stop_gui_updates()


if __name__ == "__main__":
    debug_data_controller()
