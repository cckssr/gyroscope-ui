"""Naming rules. Golden values were produced by running the 1.1.x functions once."""

from __future__ import annotations

from datetime import date

import pytest

from gyroscope_ui.core.naming import (
    WEEKDAYS_DE,
    NamingError,
    auto_file_name,
    dropbox_folder_name,
    group_folder_name,
    group_name,
    next_number,
    sanitize_subterm,
    semester,
    weekday_abbreviation,
)

MONDAY = date(2026, 11, 2)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Aufbau 1", "Aufbau_1"),
        ("Aufbau_1", "Aufbau_1"),
        ("  Müller & Söhne!  ", "Müller_Söhne"),
        ("A. Mueller", "A_Mueller"),
        ("ab/cd:ef", "ab_cd_ef"),
        ("Test--Run  2", "Test--Run_2"),
        ("Straße 5", "Straße_5"),
        ("", ""),
        ("___", ""),
        ("日本語テスト", ""),
        # longer than 20 characters: every word is cut to three letters
        ("Gyroskop Präzession Versuch Nr. 3 Gruppe", "Gyr_Prä_Ver_Nr_3_Gru"),
        ("Überprüfung der Nutation", "Übe_der_Nut"),
        ("Aufbau 1 und Aufbau 2 gemeinsam", "Auf_1_und_Auf_2_gem"),
        ("x" * 30, "xxx"),
        # still too long: first 16 characters plus "_xxx" (a trailing "_" is not trimmed)
        ("Sehr langer Name mit vielen Wörtern in der Untergruppe", "Seh_lan_Nam_mit__xxx"),
        ("a b c d e f g h i j k l m n o p q r s t u v w", "a_b_c_d_e_f_g_h__xxx"),
        ("Alpha Beta Gamma Delta Epsilon Zeta Eta", "Alp_Bet_Gam_Del__xxx"),
    ],
)
def test_sanitize_subterm_matches_the_old_output(raw, expected):
    assert sanitize_subterm(raw) == expected


def test_sanitize_subterm_with_another_max_length():
    assert sanitize_subterm("Aufbau 1 und Aufbau 2 gemeinsam", 10) == "Auf_1__xxx"
    assert sanitize_subterm("Aufbau 1", 10) == "Aufbau_1"


@pytest.mark.parametrize(
    ("group", "subterm", "expected"),
    [
        ("A", "Aufbau 1", "A_Aufbau_1"),
        ("b", "Aufbau 1", "B_Aufbau_1"),
        ("C", "", "C"),
        ("D", "日本語", "D"),
        ("E", "Gyroskop Präzession Versuch Nr. 3 Gruppe", "E_Gyr_Prä_Ver_Nr_3_Gru"),
    ],
)
def test_group_folder_name(group, subterm, expected):
    assert group_folder_name(group, subterm) == expected


def test_group_folder_name_needs_a_group():
    with pytest.raises(NamingError) as err:
        group_folder_name("", "x")
    assert err.value.key == "group_invalid"


def test_auto_file_name():
    assert auto_file_name(MONDAY, 3, "Messung", "run1") == "2026_11_02-03-Messung-run1.csv"
    assert auto_file_name(MONDAY, 3, "Messung", "-run1") == "2026_11_02-03-Messung-run1.csv"
    assert auto_file_name(MONDAY, 12, "Messung") == "2026_11_02-12-Messung.csv"
    assert auto_file_name(date(2026, 1, 5), 1, "M", extension=".json") == "2026_01_05-01-M.json"
    assert auto_file_name(MONDAY, 100, "M") == "2026_11_02-100-M.csv"


def test_auto_file_name_needs_a_measurement_name():
    with pytest.raises(NamingError) as err:
        auto_file_name(MONDAY, 1, "")
    assert err.value.key == "name_empty"


def test_next_number():
    assert next_number([], MONDAY) == 1
    names = [
        "2026_11_02-01-Messung.csv",
        "2026_11_02-03-Messung-x.csv",
        "2026_11_02-03-Messung-x.json",
        "2026_11_01-09-Messung.csv",
        "2026_11_02-1-bad.csv",
        "2026_11_02-xx-bad.csv",
        "readme.txt",
    ]
    assert next_number(names, MONDAY) == 4
    assert next_number(names, date(2026, 11, 1)) == 10
    assert next_number(names, date(2026, 11, 3)) == 1
    assert next_number([*names, "2026_11_02-100-Messung.csv"], MONDAY) == 101
    assert next_number(iter(names), MONDAY) == 4


def test_weekday_abbreviation_is_german_and_locale_independent():
    assert date(2026, 11, 2).weekday() == 0
    assert weekday_abbreviation(MONDAY) == "Mo"
    assert [weekday_abbreviation(date(2026, 11, 2 + i)) for i in range(7)] == list(WEEKDAYS_DE)
    custom = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    assert weekday_abbreviation(date(2026, 11, 8), custom) == "Sun"


def test_weekday_table_must_have_seven_entries():
    with pytest.raises(NamingError) as err:
        weekday_abbreviation(MONDAY, ("Mo", "Di"))
    assert err.value.key == "weekdays_invalid"


def test_dropbox_folder_name():
    assert dropbox_folder_name(MONDAY, "A", "TK8", "Aufbau_1") == "MoATK8-Aufbau_1"
    assert dropbox_folder_name(MONDAY, "A", "TK8") == "MoATK8"
    assert dropbox_folder_name(date(2026, 11, 6), "Z", "TK12", "x") == "FrZTK12-x"


@pytest.mark.parametrize(
    ("group", "tk", "key"),
    [
        ("a", "TK8", "group_invalid"),
        ("AB", "TK8", "group_invalid"),
        ("", "TK8", "group_invalid"),
        ("A", "TK08x", "tk_invalid"),
        ("A", "TK", "tk_invalid"),
        ("A", "tk8", "tk_invalid"),
        ("A", "TK123", "tk_invalid"),
    ],
)
def test_dropbox_folder_name_validates(group, tk, key):
    with pytest.raises(NamingError) as err:
        dropbox_folder_name(MONDAY, group, tk)
    assert err.value.key == key
    assert isinstance(err.value, ValueError)


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 3, 31), "WiSe2025"),  # 1.1.x said SoSe for January to March
        (date(2026, 4, 1), "SoSe2026"),
        (date(2026, 9, 30), "SoSe2026"),
        (date(2026, 10, 1), "WiSe2026"),
        (date(2026, 12, 31), "WiSe2026"),
        (date(2027, 1, 1), "WiSe2026"),
    ],
)
def test_semester_boundaries(day, expected):
    assert semester(day) == expected


def test_group_name():
    assert group_name(MONDAY, "A") == "WiSe2026_Mo_A"
    assert group_name(date(2026, 5, 6), "C") == "SoSe2026_Mi_C"
    assert group_name(date(2027, 2, 4), "B") == "WiSe2026_Do_B"
    with pytest.raises(NamingError) as err:
        group_name(MONDAY, "a")
    assert err.value.key == "group_invalid"
