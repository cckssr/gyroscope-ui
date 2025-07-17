#!/usr/bin/env python3
"""
Test script to verify the batch plot update functionality.
Tests both the new update_plot_batch method and the updated DataController logic.
"""

import sys
import time
import threading
from typing import List, Tuple
import numpy as np

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


class MockDisplay:
    """Mock display widget for testing."""

    def __init__(self):
        self.value = 0.0

    def display(self, value: float):
        self.value = value


class MockHistory:
    """Mock history widget for testing."""

    def __init__(self):
        self.items = []
        self.max_items = 100

    def insertItem(self, index: int, text: str):
        self.items.insert(index, text)

    def count(self):
        return len(self.items)

    def takeItem(self, index: int):
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None

    def item(self, index: int):
        return MockItem()


class MockItem:
    """Mock item for history widget."""

    def setTextAlignment(self, alignment):
        pass


def test_plot_batch_update():
    """Test the new update_plot_batch method."""
    print("Testing PlotWidget.update_plot_batch()...")

    try:
        # Create a plot widget
        plot = PlotWidget(max_plot_points=50, title="Batch Update Test")

        # Test single point update for comparison
        start_time = time.time()
        for i in range(10):
            plot.update_plot((i, i * 2))
        single_update_time = time.time() - start_time

        # Test batch update (don't clear, add more points)
        batch_points = [(i, i * 2) for i in range(10, 20)]
        start_time = time.time()
        plot.update_plot_batch(batch_points)
        batch_update_time = time.time() - start_time

        print(f"✓ Single updates (10 points): {single_update_time:.4f}s")
        print(f"✓ Batch update (10 points): {batch_update_time:.4f}s")
        print(f"✓ Speedup ratio: {single_update_time/batch_update_time:.2f}x")

        # Verify data is correctly stored
        expected_points = 20  # 10 single + 10 batch
        assert (
            plot._data_count == expected_points
        ), f"Expected {expected_points} points, got {plot._data_count}"
        print("✓ Batch update method works correctly")

        # Test that batch update works on empty plot
        plot.clear()
        test_points = [(i, i * 3) for i in range(5)]
        plot.update_plot_batch(test_points)
        assert (
            plot._data_count == 5
        ), f"Expected 5 points after batch update on empty plot, got {plot._data_count}"
        print("✓ Batch update works on empty plot")

        return True

    except Exception as e:
        print(f"✗ Batch update test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_data_controller_batch_processing():
    """Test the updated DataController with batch processing."""
    print("\nTesting DataController batch processing...")

    try:
        # Create mock widgets
        plot = PlotWidget(max_plot_points=100, title="DataController Test")
        display = MockDisplay()
        history = MockHistory()

        # Create data controller with short update interval for testing
        controller = DataController(
            plot_widget=plot,
            display_widget=display,
            history_widget=history,
            max_history=150,  # Increased to accommodate all test points
            gui_update_interval=50,  # 50ms for faster testing
        )

        # Simulate high-frequency data points
        print("Adding high-frequency data points...")
        data_points = [
            (i, float(i * 1.5 + np.random.normal(0, 0.1))) for i in range(100)
        ]

        # Add points rapidly using the fast method
        start_time = time.time()
        for index, value in data_points:
            controller.add_data_point_fast(index, value)

        # In headless mode, manually trigger processing
        if controller.gui_update_timer is None:
            print("Headless mode detected - manually processing queue")
            controller._process_queued_data()
        else:
            # Process Qt events to allow timer to fire
            print("Processing Qt events for timer...")
            for _ in range(5):  # Wait up to 500ms
                if app:
                    app.processEvents()
                time.sleep(0.1)

        processing_time = time.time() - start_time
        print(f"✓ Added 100 points in {processing_time:.4f}s")

        # Verify data was processed
        assert (
            len(controller.data_points) == 100
        ), f"Expected 100 points, got {len(controller.data_points)}"
        assert (
            plot._data_count == 100
        ), f"Expected 100 points in plot, got {plot._data_count}"

        print(f"✓ All {len(controller.data_points)} data points processed correctly")
        print(f"✓ Plot contains {plot._data_count} points")
        print(f"✓ Display shows: {display.value}")

        # Stop the controller
        controller.stop_gui_updates()

        return True

    except Exception as e:
        print(f"✗ DataController test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_performance_comparison():
    """Compare performance between old and new methods."""
    print("\nTesting performance comparison...")

    try:
        plot = PlotWidget(max_plot_points=200, title="Performance Test")

        # Test data
        test_points = [(i, float(i + np.random.normal(0, 0.5))) for i in range(100)]

        # Method 1: Individual updates (old way)
        plot.clear()
        start_time = time.time()
        for point in test_points:
            plot.update_plot(point)
        individual_time = time.time() - start_time

        # Method 2: Batch update (new way)
        plot.clear()
        start_time = time.time()
        plot.update_plot_batch(test_points)
        batch_time = time.time() - start_time

        print(f"✓ Individual updates: {individual_time:.4f}s")
        print(f"✓ Batch update: {batch_time:.4f}s")
        print(f"✓ Performance improvement: {individual_time/batch_time:.2f}x faster")

        # Both methods should result in the same data
        assert plot._data_count == 100, f"Expected 100 points, got {plot._data_count}"

        return True

    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False


def main():
    """Run all batch update tests."""
    print("=" * 60)
    print("Testing Batch Plot Update Implementation")
    print("=" * 60)

    tests = [
        test_plot_batch_update,
        test_data_controller_batch_processing,
        test_performance_comparison,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All batch update tests PASSED!")
        print("The plot update optimization is working correctly.")
        return True
    else:
        print("✗ Some tests FAILED!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
