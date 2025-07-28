import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_controller import DataController


class DummyLCD:
    def __init__(self):
        self.value = None

    def display(self, value):
        self.value = value


class DummyItem:
    def __init__(self, text):
        self.text = text
        self.alignment = None

    def setTextAlignment(self, alignment):
        self.alignment = alignment


class DummyHistory:
    def __init__(self):
        self.items = []

    def insertItem(self, index, text):
        self.items.insert(index, DummyItem(text))

    def item(self, index):
        return self.items[index]

    def count(self):
        return len(self.items)

    def takeItem(self, index):
        if 0 <= index < len(self.items):
            self.items.pop(index)

    def clear(self):
        self.items.clear()


class DummyPlot:
    def __init__(self):
        self.data = []

    def update_plot(self, point):
        self.data.append(point)

    def update_plot_batch(self, points):
        """Support for batch updates"""
        for point in points:
            self.data.append(point)

    def clear(self):
        self.data.clear()


class DataControllerTests(unittest.TestCase):
    def setUp(self):
        self.lcd = DummyLCD()
        self.history = DummyHistory()
        self.plot = DummyPlot()
        self.ctrl = DataController(
            plot_widget=self.plot,
            display_widget=self.lcd,
            history_widget=self.history,
            table_widget=None,
            max_history=3,
        )

    def test_add_data_point(self):
        self.ctrl.add_data_point(1, 0.5)
        self.assertEqual(self.lcd.value, 0.5)
        self.assertEqual(len(self.history.items), 1)
        # Check both full data storage and GUI data storage
        self.assertEqual(len(self.ctrl.data_points), 1)  # Full storage
        self.assertEqual(len(self.ctrl.gui_data_points), 1)  # GUI storage
        self.assertEqual(self.ctrl.data_points[0], (1, 0.5))
        self.assertEqual(self.ctrl.gui_data_points[0], (1, 0.5))

    def test_add_data_point_fast(self):
        """Test the new fast data point method with queue processing"""
        # Add data points using the fast method (only 3 due to max_history limit)
        for i in range(3):
            self.ctrl.add_data_point_fast(i, float(i * 0.1))

        # Verify data is queued but not yet processed
        self.assertEqual(self.ctrl.data_queue.qsize(), 3)
        self.assertEqual(len(self.ctrl.data_points), 0)

        # Manually trigger queue processing (simulates timer)
        self.ctrl._process_queued_data()

        # Verify data was processed
        self.assertEqual(self.ctrl.data_queue.qsize(), 0)
        self.assertEqual(len(self.ctrl.data_points), 3)
        self.assertEqual(len(self.plot.data), 3)

        # Check specific data points
        self.assertEqual(self.ctrl.data_points[0], (0, 0.0))
        self.assertEqual(self.ctrl.data_points[2], (2, 0.2))

    def test_history_limit(self):
        for i in range(5):
            self.ctrl.add_data_point(i, i * 0.1)
        self.assertEqual(len(self.history.items), 3)

    def test_clear_data(self):
        self.ctrl.add_data_point(1, 1.0)
        self.ctrl.clear_data()
        self.assertEqual(len(self.ctrl.data_points), 0)
        self.assertEqual(len(self.history.items), 0)
        self.assertEqual(self.lcd.value, 0)

    def test_get_statistics(self):
        self.ctrl.add_data_point(1, 1)
        self.ctrl.add_data_point(2, 3)
        stats = self.ctrl.get_statistics()
        self.assertEqual(stats["count"], 2.0)
        self.assertEqual(stats["min"], 1.0)
        self.assertEqual(stats["max"], 3.0)
        self.assertAlmostEqual(stats["avg"], 2.0)

    def test_get_csv_data(self):
        self.ctrl.add_data_point(1, 2)
        csv_data = self.ctrl.get_csv_data()
        self.assertEqual(csv_data[0], ["Index", "Value (µs)", "Time"])
        self.assertEqual(csv_data[1][0], "1")
        self.assertEqual(csv_data[1][1], "2.0")


if __name__ == "__main__":
    unittest.main()
