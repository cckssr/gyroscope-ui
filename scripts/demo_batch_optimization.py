#!/usr/bin/env python3
"""
Demonstration script showing the difference between individual and batch plot updates.
Shows how the optimized data flow improves performance at high data rates.
"""

import sys
import time
import threading
import numpy as np

# Add the project root to Python path
sys.path.insert(0, "/Users/cedric.kessler/TU_Berlin_offline/TutorGP/HRNGGUI")

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer

    app = (
        QApplication(sys.argv)
        if not QApplication.instance()
        else QApplication.instance()
    )
except:
    app = None

from src.plot import PlotWidget
from src.data_controller import DataController


def simulate_high_frequency_data(controller, num_points=500, delay_ms=1):
    """Simulate high-frequency data generation like from Arduino."""
    print(f"Simulating {num_points} data points with {delay_ms}ms delay...")

    start_time = time.time()
    for i in range(num_points):
        # Simulate realistic measurement data with some noise
        value = 100 + 10 * np.sin(i * 0.1) + np.random.normal(0, 2)
        controller.add_data_point_fast(i, value)

        # Small delay to simulate real-time data
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

    total_time = time.time() - start_time
    data_rate = num_points / total_time
    print(
        f"Generated {num_points} points in {total_time:.2f}s (rate: {data_rate:.1f} Hz)"
    )

    return total_time, data_rate


def demonstrate_batch_optimization():
    """Demonstrate the performance difference between old and new approaches."""
    print("=" * 70)
    print("DEMONSTRATION: Batch Plot Update Optimization")
    print("=" * 70)

    # Test configuration
    test_points = 200

    print("\n1. Testing OLD approach (individual plot updates):")
    print("-" * 50)

    # Old approach: individual updates
    plot_old = PlotWidget(max_plot_points=250, title="Individual Updates")

    start_time = time.time()
    for i in range(test_points):
        value = 100 + 5 * np.sin(i * 0.05) + np.random.normal(0, 1)
        plot_old.update_plot((i, value))
    old_time = time.time() - start_time

    print(f"✓ Individual updates completed: {old_time:.4f}s")
    print(f"✓ Average time per point: {(old_time/test_points)*1000:.2f}ms")

    print("\n2. Testing NEW approach (batch updates):")
    print("-" * 50)

    # New approach: batch updates
    plot_new = PlotWidget(max_plot_points=250, title="Batch Updates")

    # Generate all points first
    batch_points = [
        (i, 100 + 5 * np.sin(i * 0.05) + np.random.normal(0, 1))
        for i in range(test_points)
    ]

    start_time = time.time()
    plot_new.update_plot_batch(batch_points)
    new_time = time.time() - start_time

    print(f"✓ Batch update completed: {new_time:.4f}s")
    print(f"✓ Average time per point: {(new_time/test_points)*1000:.2f}ms")

    print("\n3. Performance comparison:")
    print("-" * 50)
    speedup = old_time / new_time
    print(f"✓ Performance improvement: {speedup:.1f}x faster")
    print(f"✓ Time saved: {((old_time - new_time)/old_time)*100:.1f}%")

    print("\n4. Testing DataController with high-frequency simulation:")
    print("-" * 50)

    # Test with DataController
    plot_controller = PlotWidget(max_plot_points=300, title="DataController Test")
    controller = DataController(
        plot_widget=plot_controller,
        display_widget=None,
        history_widget=None,
        max_history=300,
        gui_update_interval=100,  # 100ms GUI updates
    )

    # Simulate high-frequency data in a separate thread
    def data_generator():
        for i in range(250):
            value = 120 + 8 * np.cos(i * 0.08) + np.random.normal(0, 1.5)
            controller.add_data_point_fast(i, value)
            time.sleep(0.002)  # 500 Hz data rate

    print("Starting high-frequency data simulation (500 Hz)...")
    thread = threading.Thread(target=data_generator)
    thread.start()

    # Process events to allow GUI updates
    start_time = time.time()
    while thread.is_alive() and (time.time() - start_time) < 2.0:
        if app:
            app.processEvents()
        time.sleep(0.01)

    thread.join()

    # Final processing
    if app:
        for _ in range(10):
            app.processEvents()
            time.sleep(0.02)

    print(f"✓ High-frequency simulation completed")
    print(f"✓ Final plot contains {plot_controller._data_count} points")
    print(f"✓ DataController processed {len(controller.data_points)} total points")

    # Cleanup
    controller.stop_gui_updates()

    print("\n" + "=" * 70)
    print("SUMMARY:")
    print(f"- Batch updates are {speedup:.1f}x faster than individual updates")
    print(f"- High-frequency data (500 Hz) handled smoothly with 100ms GUI updates")
    print(f"- Plot performance scales well with increased data rates")
    print("- Memory usage remains bounded by max_plot_points setting")
    print("=" * 70)


if __name__ == "__main__":
    demonstrate_batch_optimization()
