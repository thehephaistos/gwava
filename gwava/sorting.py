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
    """Normalize and validate a user-provided sorting mode.

    Parameters
    ----------
    mode:
        Requested sorting mode. Leading and trailing whitespace is ignored,
        letters are converted to lowercase, and spaces or hyphens are
        converted to underscores.

    Returns
    -------
    str
        Normalized mode name matching one of the values in
        :data:`SORT_MODES`.

    Raises
    ------
    ValueError
        If the normalized mode is not included in :data:`SORT_MODES`.
    """
    normalized = mode.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized not in SORT_MODES:
        choices = ", ".join(SORT_MODES)
        raise ValueError(f"Unknown sort mode {mode!r}. Choose one of: {choices}")
    return normalized


def _numeric_column(dataframe: pd.DataFrame, column: str) -> pd.Series:
    """Return a DataFrame column converted to numeric values.

    Parameters
    ----------
    dataframe:
        Event table containing the requested sorting column.
    column:
        Name of the column to convert.

    Returns
    -------
    pandas.Series
        Numeric representation of the column. Values that cannot be converted
        are represented by ``NaN``.

    Raises
    ------
    ValueError
        If ``column`` is not present in ``dataframe``.
    """
    if column not in dataframe.columns:
        raise ValueError(f"Sort mode requires the DataFrame column {column!r}")
    return pd.to_numeric(dataframe[column], errors="coerce")


def _sorting_mass(dataframe: pd.DataFrame) -> pd.Series:
    """Build the preferred mass used by the visual layout modes.

    Parameters
    ----------
    dataframe:
        Event table containing one or more supported mass columns.

    Returns
    -------
    pandas.Series
        One preferred mass value for every event, using the first available
        value in the fallback sequence.

    Raises
    ------
    ValueError
        If the DataFrame contains none of the supported mass-column
        combinations.

    Notes
    -----
    Values are selected in this order:

    1. ``final_mass_source``.
    2. ``total_mass_source``.
    3. ``mass_1_source + mass_2_source``.

    A later source fills only values that are missing from earlier sources.
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
    """Return row positions for a stable linear ordering.

    Parameters
    ----------
    values:
        Values whose index identifies the corresponding DataFrame rows.
    ascending:
        If ``True``, order values from smallest to largest. If ``False``,
        order values from largest to smallest.

    Returns
    -------
    list of int
        Ordered row-index labels.

    Notes
    -----
    Equal values retain their original relative order. Missing values are
    always placed at the end.
    """
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
    """Arrange one end of a value range near the center of a layout.

    Parameters
    ----------
    values:
        Values whose index identifies the corresponding DataFrame rows.
    largest_at_center:
        If ``True``, place the largest values near the center and the smallest
        values near the edges. If ``False``, place the smallest values near
        the center and the largest values near the edges.

    Returns
    -------
    list of int
        Row-index labels arranged from the left edge to the right edge.

    Notes
    -----
    Values are alternated between the left and right sides to create a
    symmetric peak or valley. Missing values are appended at the end.
    """
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

    Parameters
    ----------
    dataframe:
        Event table to arrange. The input is never modified.

    Returns
    -------
    pandas.DataFrame
        Reordered copy with the largest preferred masses near the center and
        the smallest preferred masses near the edges.

    Raises
    ------
    ValueError
        If no supported mass source is available.

    Notes
    -----
    The preferred mass follows the fallback sequence used by
    :func:`_sorting_mass`: final mass, total mass, then the sum of the two
    component masses.
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

    Parameters
    ----------
    dataframe:
        Event table containing component masses and a supported remnant or
        total-mass source. The input is never modified.

    Returns
    -------
    pandas.DataFrame
        Visual-layout copy whose component pairs have their widest spans near
        the center and whose remnant masses form a central peak. Internal
        source-event index columns and source metadata are included so
        interactive markers can recover the original event.

    Raises
    ------
    ValueError
        If either component-mass column is absent, if a component mass is
        missing, or if no supported remnant or total-mass source is available.

    Notes
    -----
    Unlike the other sort modes, this is a visual layout rather than an event
    sort. Component masses are pooled, paired from opposite ends of their
    distribution, and placed with the widest pairs at the center. Remnant
    masses are independently arranged into a peak.

    Warning
    -------
    Consequently, values in a displayed column no longer belong to the event
    metadata stored on the same row. Use this mode for the visual overview,
    not for event-by-event scientific analysis. Original event associations
    remain available through the internal source mapping used by interactive
    plot details.
    """
    source_events = dataframe.copy(deep=True).reset_index(drop=True)
    source_events.attrs = {}
    working = source_events.copy(deep=True)

    if working.empty:
        return working

    required = {"mass_1_source", "mass_2_source"}
    missing = required.difference(working.columns)

    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(f"Diamond layout requires these columns: {names}")

    mass_1 = pd.to_numeric(source_events["mass_1_source"], errors="coerce")
    mass_2 = pd.to_numeric(source_events["mass_2_source"], errors="coerce")
    event_indices = pd.Series(range(len(source_events)), dtype=int)
    component_masses = pd.concat(
        [
            pd.DataFrame({"value": mass_1, "event_index": event_indices}),
            pd.DataFrame({"value": mass_2, "event_index": event_indices}),
        ],
        ignore_index=True,
    )

    if component_masses["value"].isna().any():
        raise ValueError("Diamond layout requires non-missing component masses")

    event_count = len(working)
    sorted_components = component_masses.sort_values(
        "value",
        kind="stable",
    ).reset_index(drop=True)

    lower_components = sorted_components.iloc[:event_count].reset_index(drop=True)
    upper_components = (
        sorted_components.iloc[event_count:].iloc[::-1].reset_index(drop=True)
    )
    component_spans = pd.Series(
        upper_components["value"].to_numpy()
        - lower_components["value"].to_numpy(),
        dtype=float,
    )
    pair_positions = _center_weighted_order(
        component_spans,
        largest_at_center=True,
    )

    remnant_masses = _sorting_mass(source_events)
    remnant_positions = _center_weighted_order(
        remnant_masses,
        largest_at_center=True,
    )

    working["mass_1_source"] = (
        upper_components["value"].to_numpy()[pair_positions]
    )
    working["mass_2_source"] = (
        lower_components["value"].to_numpy()[pair_positions]
    )
    working["final_mass_source"] = (
        remnant_masses.iloc[remnant_positions].reset_index(drop=True)
    )
    working["_mass_1_event_index"] = (
        upper_components["event_index"].to_numpy()[pair_positions]
    )
    working["_mass_2_event_index"] = (
        lower_components["event_index"].to_numpy()[pair_positions]
    )
    working["_final_mass_event_index"] = remnant_positions
    working.attrs["source_events"] = source_events
    working.attrs["preserves_event_associations"] = False

    return working


def create_valley_layout(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with high masses at the edges and low masses at center.

    Parameters
    ----------
    dataframe:
        Event table to arrange. The input is never modified.

    Returns
    -------
    pandas.DataFrame
        Reordered copy with the smallest preferred masses near the center and
        the largest preferred masses near the edges.

    Raises
    ------
    ValueError
        If no supported mass source is available.

    Notes
    -----
    The preferred mass follows the fallback sequence used by
    :func:`_sorting_mass`: final mass, total mass, then the sum of the two
    component masses.
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

    Returns
    -------
    pandas.DataFrame
        Reordered copy with a fresh zero-based index.

    Raises
    ------
    ValueError
        If ``mode`` is unknown or the selected mode requires columns that are
        absent from ``dataframe``.

    Notes
    -----
    ``rising``, ``falling``, ``peaked``, and ``valley`` use final mass when
    available, then total mass, then the sum of the two component masses.
    Missing sort values are kept and placed at the end. ``diamond`` is a
    visual layout and does not preserve event associations row by row.
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
