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
    "diamond",
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
    "diamond",
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


def create_diamond_layout(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Create a filled diamond by independently arranging plotted masses.

    Unlike the other sort modes, this is a visual layout rather than an event
    sort. Component masses are pooled, paired from opposite ends of their
    distribution, and placed with the widest pairs at the center. Remnant
    masses are independently arranged into a peak.

    Consequently, values in a displayed column no longer belong to the event
    metadata stored on the same row. Use this mode for the visual overview,
    not for event-by-event scientific analysis.
    """
    working = dataframe.copy(deep=True).reset_index(drop=True)

    if working.empty:
        return working

    required = {"mass_1_source", "mass_2_source"}
    missing = required.difference(working.columns)

    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(f"Diamond layout requires these columns: {names}")

    mass_1 = pd.to_numeric(working["mass_1_source"], errors="coerce")
    mass_2 = pd.to_numeric(working["mass_2_source"], errors="coerce")
    component_masses = pd.concat([mass_1, mass_2], ignore_index=True)

    if component_masses.isna().any():
        raise ValueError("Diamond layout requires non-missing component masses")

    event_count = len(working)
    sorted_components = component_masses.sort_values(
        kind="stable",
    ).to_numpy()

    lower_components = sorted_components[:event_count]
    upper_components = sorted_components[event_count:][::-1]
    component_spans = pd.Series(
        upper_components - lower_components,
        dtype=float,
    )
    pair_positions = _center_weighted_order(
        component_spans,
        largest_at_center=True,
    )

    remnant_masses = _sorting_mass(working)
    remnant_positions = _center_weighted_order(
        remnant_masses,
        largest_at_center=True,
    )

    working["mass_1_source"] = upper_components[pair_positions]
    working["mass_2_source"] = lower_components[pair_positions]
    working["final_mass_source"] = (
        remnant_masses.iloc[remnant_positions].reset_index(drop=True)
    )
    working.attrs["preserves_event_associations"] = False

    return working


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
    if normalized_mode == "diamond":
        return create_diamond_layout(dataframe)

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
