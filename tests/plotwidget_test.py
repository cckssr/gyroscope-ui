import numpy as np
import pytest
from src.plot import PlotWidget


class DummyDebug:
    @staticmethod
    def info(msg):
        pass

    @staticmethod
    def debug(msg):
        pass


# Patch Debug to avoid side effects during tests
import src.plot

src.plot.Debug = DummyDebug


@pytest.fixture
def plot_widget():
    return PlotWidget(
        max_plot_points=5, fontsize=12, xlabel="Time", ylabel="Value", title="Test Plot"
    )


def test_initialization(plot_widget):
    assert plot_widget.max_plot_points == 5
    assert plot_widget.fontsize == 12
    assert plot_widget._x_data.shape == (5,)
    assert plot_widget._y_data.shape == (5,)
    assert plot_widget._data_count == 0
    assert plot_widget._plot_config["xlabel"] == "Time"
    assert plot_widget._plot_config["ylabel"] == "Value"
    assert plot_widget._plot_config["title"] == "Test Plot"


def test_update_plot_adds_points(plot_widget):
    plot_widget.update_plot((1.0, 2.0))
    assert plot_widget._data_count == 1
    np.testing.assert_array_equal(plot_widget._x_data[:1], [1.0])
    np.testing.assert_array_equal(plot_widget._y_data[:1], [2.0])

    plot_widget.update_plot((2.0, 3.0))
    assert plot_widget._data_count == 2
    np.testing.assert_array_equal(plot_widget._x_data[:2], [1.0, 2.0])
    np.testing.assert_array_equal(plot_widget._y_data[:2], [2.0, 3.0])


def test_update_plot_rolls_when_full(plot_widget):
    # Fill up to max_plot_points
    for i in range(5):
        plot_widget.update_plot((i, i * 10))
    assert plot_widget._data_count == 5
    np.testing.assert_array_equal(plot_widget._x_data, [0, 1, 2, 3, 4])
    np.testing.assert_array_equal(plot_widget._y_data, [0, 10, 20, 30, 40])

    # Add one more, should roll
    plot_widget.update_plot((5, 50))
    assert plot_widget._data_count == 5
    np.testing.assert_array_equal(plot_widget._x_data, [1, 2, 3, 4, 5])
    np.testing.assert_array_equal(plot_widget._y_data, [10, 20, 30, 40, 50])


def test_clear_resets_data(plot_widget):
    for i in range(3):
        plot_widget.update_plot((i, i))
    plot_widget.clear()
    assert plot_widget._data_count == 0
    assert np.all(plot_widget._x_data == 0)
    assert np.all(plot_widget._y_data == 0)


def test_set_title(plot_widget):
    plot_widget.set_title("New Title")
    assert plot_widget._plot_config["title"] == "New Title"


def test_set_axis_labels(plot_widget):
    plot_widget.set_axis_labels(xlabel="New X", ylabel="New Y")
    assert plot_widget._plot_config["xlabel"] == "New X"
    assert plot_widget._plot_config["ylabel"] == "New Y"

    plot_widget.set_axis_labels(xlabel="Only X")
    assert plot_widget._plot_config["xlabel"] == "Only X"
    assert plot_widget._plot_config["ylabel"] == "New Y"

    plot_widget.set_axis_labels(ylabel="Only Y")
    assert plot_widget._plot_config["xlabel"] == "Only X"
    assert plot_widget._plot_config["ylabel"] == "Only Y"


def test_set_max_points_increases_and_decreases(plot_widget):
    # Add 3 points
    for i in range(3):
        plot_widget.update_plot((i, i * 2))
    plot_widget.set_max_points(6)
    assert plot_widget.max_plot_points == 6
    assert plot_widget._data_count == 3
    assert plot_widget._x_data.shape == (6,)
    assert plot_widget._y_data.shape == (6,)
    np.testing.assert_array_equal(plot_widget._x_data[:3], [0, 1, 2])
    np.testing.assert_array_equal(plot_widget._y_data[:3], [0, 2, 4])

    # Add more points to fill
    for i in range(3, 6):
        plot_widget.update_plot((i, i * 2))
    assert plot_widget._data_count == 6

    # Now decrease max points
    plot_widget.set_max_points(4)
    assert plot_widget.max_plot_points == 4
    assert plot_widget._data_count == 4
    np.testing.assert_array_equal(plot_widget._x_data[:4], [2, 3, 4, 5])
    np.testing.assert_array_equal(plot_widget._y_data[:4], [4, 6, 8, 10])


def test_set_max_points_zero_or_negative(plot_widget):
    plot_widget.set_max_points(0)
    assert plot_widget.max_plot_points == 5  # Should not change

    plot_widget.set_max_points(-3)
    assert plot_widget.max_plot_points == 5  # Should not change
