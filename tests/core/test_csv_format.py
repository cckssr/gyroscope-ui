from __future__ import annotations

import csv
import io
import math

import numpy as np
from batches import make_sample

from gyroscope_ui.core.csv_format import CSV_HEADER, csv_rows, csv_rows_from_recording
from gyroscope_ui.core.models import SampleBatch
from gyroscope_ui.core.recording import Recording

OLD_HEADER = ["Time (s)", "Disk rotation frequency (Hz)", "Gyro Z rate (rad/s)"]


def test_header_is_unchanged():
    assert list(CSV_HEADER) == OLD_HEADER


def test_rows_equal_the_old_format():
    """Golden rows produced by the 1.1.x ``get_csv_data`` formatting."""
    rows = csv_rows(
        [0.0, 0.01, 12.3456789],
        [14.9876543, math.nan, 0.0],
        [2.1, -0.5, math.nan],
    )
    assert rows == [
        OLD_HEADER,
        ["0.000000", "14.987654", "2.100000"],
        ["0.010000", "", "-0.500000"],
        ["12.345679", "0.000000", ""],
    ]


def test_rows_accept_numpy_arrays_and_empty_input():
    assert csv_rows(np.array([1.5]), np.array([2.0]), np.array([3.0]))[1] == [
        "1.500000",
        "2.000000",
        "3.000000",
    ]
    assert csv_rows([], [], []) == [OLD_HEADER]


def test_csv_writer_defaults_give_the_expected_bytes():
    buffer = io.StringIO(newline="")
    csv.writer(buffer).writerows(csv_rows([0.0], [14.5], [math.nan]))
    assert buffer.getvalue() == (
        "Time (s),Disk rotation frequency (Hz),Gyro Z rate (rad/s)\r\n0.000000,14.500000,\r\n"
    )


def test_rows_from_a_recording():
    rec = Recording()
    rec.start(0.0)
    rec.append(
        SampleBatch.from_samples(
            [
                make_sample(100, frequency_hz=10.0, gyro_z_rad_s=1.5),
                make_sample(110, frequency_hz=9.5, gyro_z_rad_s=math.nan),
            ]
        )
    )
    assert csv_rows_from_recording(rec) == [
        OLD_HEADER,
        ["0.000000", "10.000000", "1.500000"],
        ["0.010000", "9.500000", ""],
    ]
