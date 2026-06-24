"""Reusable event-ordering functions for GWOSC visualizations.

Sorting is kept separate from plotting so the same ordering can be used by a
static figure, an interactive widget, or a future web application.
"""

from typing import Literal

import pandas as pd

SortMode = Literal[
    "rising",
    "falling",
    "peaked",
    "valley",
    "random",
    "date",
    "distance",
    "chirp_mass",
    "chi_eff",
    "snr",
]

SORT_MODES: tuple[SortMode, ...] = (
    "rising",
    "falling",
    "peaked",
    "valley",
    "random",
    "date",
    "distance",
    "chirp_mass",
    "chi_eff",
    "snr",
)

_COLUMN_BY_MODE = {
    "date": "gps",
    "distance": "luminosity_distance",
    "chirp_mass": "chirp_mass_source",
    "chi_eff": "chi_eff",
    "snr": "network_matched_filter_snr",
}


def _normalize_mode(mode: str) -> str:
    """Normalize user-facing spellings such as ``chirp-mass``."""
    normalized = mode.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in SORT_MODES:
        choices = ", ".join(SORT_MODES)
        raise ValueError(f"Unknown sort mode {mode!r}. Choose one of: {choices}")
    return normalized


def _numeric_column(dataframe: pd.DataFrame, column: str) -> pd.Series:
    """Return one column as numeric values with invalid entries set to NaN."""
    if column not in dataframe.columns:
        raise ValueError(f"Sort mode requires the DataFrame column {column!r}")
    return pd.to_numeric(dataframe[column], errors="coerce")


def _sorting_mass(dataframe: pd.DataFrame) -> pd.Series:
    """Build the preferred mass used by the visual layout modes.

    The value is selected in this order:

    1. ``final_mass_source``
    2. ``total_mass_source``
    3. ``mass_1_source + mass_2_source``
    """
    candidates: list[pd.Series] = []

    for column in ("final_mass_source", "total_mass_source"):
        if column in dataframe.columns:
            candidates.append(pd.to_numeric(dataframe[column], errors="coerce"))

    component_columns = {"mass_1_source", "mass_2_source"}
    if component_columns.issubset(dataframe.columns):
        component_total = (
            pd.to_numeric(dataframe["mass_1_source"], errors="coerce")
            + pd.to_numeric(dataframe["mass_2_source"], errors="coerce")
        )
        candidates.append(component_total)

    if not candidates:
        raise ValueError(
            "Mass sorting requires final_mass_source, total_mass_source, "
            "or both component-mass columns"
        )

    values = candidates[0].astype(float)
    for fallback in candidates[1:]:
        values = values.where(values.notna(), fallback)

    return values


def _linear_order(values: pd.Series, *, ascending: bool) -> list[int]:
    """Return stable row positions, always placing missing values last."""
    return values.sort_values(
        ascending=ascending,
        na_position="last",
        kind="stable",
    ).index.tolist()


def _center_weighted_order(
    values: pd.Series,
    *,
    largest_at_center: bool,
) -> list[int]:
    """Arrange extrema at the center and the opposite values at the edges."""
    valid = values[values.notna()]
    missing_positions = values[values.isna()].index.tolist()
    sorted_positions = valid.sort_values(
        ascending=largest_at_center,
        kind="stable",
    ).index.tolist()

    # Alternating values between the left and right edges creates a symmetric
    # peak or valley without changing any event values.
    arranged = sorted_positions[::2] + sorted_positions[1::2][::-1]
    return arranged + missing_positions


def create_peaked_layout(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with low masses at the edges and high masses at center.

    The mass used for ordering follows the standard fallback sequence:
    ``final_mass_source``, then ``total_mass_source``, then the sum of
    ``mass_1_source`` and ``mass_2_source``.
    """
    working = dataframe.copy(deep=True).reset_index(drop=True)

    if working.empty:
        return working

    positions = _center_weighted_order(
        _sorting_mass(working),
        largest_at_center=True,
    )
    return working.iloc[positions].reset_index(drop=True)


def create_valley_layout(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with high masses at the edges and low masses at center.

    The mass used for ordering follows the standard fallback sequence:
    ``final_mass_source``, then ``total_mass_source``, then the sum of
    ``mass_1_source`` and ``mass_2_source``.
    """
    working = dataframe.copy(deep=True).reset_index(drop=True)

    if working.empty:
        return working

    positions = _center_weighted_order(
        _sorting_mass(working),
        largest_at_center=False,
    )
    return working.iloc[positions].reset_index(drop=True)


def sort_events(
    dataframe: pd.DataFrame,
    mode: str = "date",
    *,
    random_seed: int | None = 42,
) -> pd.DataFrame:
    """Return a reordered copy of a GWOSC event DataFrame.

    Parameters
    ----------
    dataframe:
        Event table to reorder. The input is never modified.
    mode:
        One of :data:`SORT_MODES`. Hyphens and spaces are accepted in names,
        so ``"chirp-mass"`` and ``"chirp mass"`` both select
        ``"chirp_mass"``.
    random_seed:
        Seed for reproducible random ordering. Use ``None`` for a different
        random ordering each time.

    Notes
    -----
    ``rising``, ``falling``, ``peaked``, and ``valley`` use final mass when
    available, then total mass, then the sum of the two component masses.
    Missing sort values are kept and placed at the end.
    """
    normalized_mode = _normalize_mode(mode)

    if normalized_mode == "peaked":
        return create_peaked_layout(dataframe)
    if normalized_mode == "valley":
        return create_valley_layout(dataframe)

    working = dataframe.copy(deep=True).reset_index(drop=True)

    if working.empty:
        return working

    if normalized_mode == "random":
        return working.sample(frac=1, random_state=random_seed).reset_index(drop=True)

    if normalized_mode in {"rising", "falling"}:
        values = _sorting_mass(working)
    else:
        values = _numeric_column(working, _COLUMN_BY_MODE[normalized_mode])

    if normalized_mode == "falling":
        positions = _linear_order(values, ascending=False)
    else:
        positions = _linear_order(values, ascending=True)

    return working.iloc[positions].reset_index(drop=True)
