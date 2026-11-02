"""File, folder and group names (CONCEPT 6.2); pure string logic, no file system access.

The rules are those of version 1.1.x, except where a docstring says otherwise. Errors are
``NamingError`` carrying a message key.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from datetime import date

WEEKDAYS_DE: tuple[str, ...] = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")

_GROUP_RE = re.compile(r"[A-Z]")
_TK_RE = re.compile(r"TK[0-9]{1,2}")


class NamingError(ValueError):
    """Invalid input for a name; ``key`` is the message key (``group_invalid``...)."""

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


def sanitize_subterm(subterm: str, max_length: int = 20) -> str:
    """Make a free-text sub-group label usable in folder names.

    Characters outside ``[A-Za-z0-9 _-]`` and the German letters become ``_``, runs of ``_`` and
    white space collapse to one ``_`` and the ends are trimmed. A result longer than
    ``max_length`` is shortened by cutting every word to 3 letters; if that is still too long it
    becomes the first ``max_length - 4`` characters plus ``_xxx``.
    """
    if not subterm:
        return ""
    sanitized = re.sub(r"[^a-zA-Z0-9\s\-_äöüÄÖÜß]", "_", subterm)
    sanitized = re.sub(r"[_\s]+", "_", sanitized).strip("_")
    if len(sanitized) <= max_length:
        return sanitized
    abbreviated = "_".join(word[:3] for word in sanitized.split("_") if word)
    if len(abbreviated) <= max_length:
        return abbreviated
    return abbreviated[: max_length - 4] + "_xxx"


def sanitize_suffix(suffix: str) -> str:
    """Make the free-text file name suffix safe: the character rules of
    :func:`sanitize_subterm` (no path separators, no characters Windows forbids), no shortening."""
    sanitized = re.sub(r"[^a-zA-Z0-9\s\-_äöüÄÖÜß]", "_", suffix)
    return re.sub(r"[_\s]+", "_", sanitized).strip("_-")


def is_valid_group(group: str) -> bool:
    """``group`` is a single letter A-Z."""
    return bool(_GROUP_RE.fullmatch(group))


def group_folder_name(group: str, subterm: str, max_length: int = 20) -> str:
    """Auto-save folder ``<GROUP>[_<subterm>]``, e.g. ``A_Aufbau_1``."""
    if not group:
        raise NamingError("group_invalid")
    parts = [group.upper()]
    clean = sanitize_subterm(subterm, max_length)
    if clean:
        parts.append(clean)
    return "_".join(parts)


def auto_file_name(
    day: date,
    number: int,
    measurement_name: str,
    suffix: str = "",
    extension: str = ".csv",
) -> str:
    """Auto-save file name ``<YYYY_MM_DD>-<NN>-<name>[-<suffix>]<ext>``."""
    if not measurement_name:
        raise NamingError("name_empty")
    suffix = sanitize_suffix(suffix)
    if suffix:
        suffix = "-" + suffix
    return f"{day:%Y_%m_%d}-{number:02d}-{measurement_name}{suffix}{extension}"


def next_number(existing_names: Iterable[str], day: date) -> int:
    """Next free ``NN`` for ``day``: one more than the highest used, 1 if none."""
    pattern = re.compile(rf"{day:%Y_%m_%d}-([0-9]{{2,}})-")
    used = [int(m.group(1)) for name in existing_names if (m := pattern.match(name))]
    return max(used, default=0) + 1


def weekday_abbreviation(day: date, abbreviations: Sequence[str] = WEEKDAYS_DE) -> str:
    """Abbreviation of the weekday of ``day`` (Monday first), independent of the OS locale."""
    if len(abbreviations) != 7:
        raise NamingError("weekdays_invalid")
    return abbreviations[day.weekday()]


def dropbox_folder_name(
    day: date,
    group: str,
    tk: str,
    subterm_sanitised: str = "",
    abbreviations: Sequence[str] = WEEKDAYS_DE,
) -> str:
    """Dropbox folder ``<Wd><GROUP><TK>[-<subterm>]``, e.g. ``MoATK8-Aufbau_1``."""
    if not _GROUP_RE.fullmatch(group):
        raise NamingError("group_invalid")
    if not _TK_RE.fullmatch(tk):
        raise NamingError("tk_invalid")
    name = f"{weekday_abbreviation(day, abbreviations)}{group}{tk}"
    return f"{name}-{subterm_sanitised}" if subterm_sanitised else name


def semester(day: date) -> str:
    """Semester label: October to March ``WiSe<start year>``, April to September ``SoSe<year>``.

    Fix: version 1.1.x labelled January to March as ``SoSe``.
    """
    if day.month >= 10:
        return f"WiSe{day.year}"
    if day.month <= 3:
        return f"WiSe{day.year - 1}"
    return f"SoSe{day.year}"


def group_name(day: date, letter: str, abbreviations: Sequence[str] = WEEKDAYS_DE) -> str:
    """Group name ``<semester>_<Wd>_<letter>``, e.g. ``WiSe2026_Mo_A``."""
    if not _GROUP_RE.fullmatch(letter):
        raise NamingError("group_invalid")
    return f"{semester(day)}_{weekday_abbreviation(day, abbreviations)}_{letter}"
