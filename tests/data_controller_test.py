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
            max_history=3,
        )

    def test_add_data_point(self):
        self.ctrl.add_data_point(1, 0.5)
        self.assertEqual(self.lcd.value, 0.5)
        self.assertEqual(len(self.history.items), 1)
        self.assertEqual(self.plot.data[0], (1, 0.5))

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
        self.assertEqual(csv_data[0], ["Index", "Value (µs)"])
        self.assertEqual(csv_data[1], ["1", "2.0"])


if __name__ == "__main__":
    unittest.main()
