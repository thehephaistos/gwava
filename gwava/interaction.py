"""Interactive event-detail tooltips for Matplotlib figures."""

from collections.abc import Mapping
from typing import Any

import pandas as pd
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure

PointRecord = tuple[Mapping[str, Any], str]

_MEASUREMENTS = (
    ("final_mass_source", "m_final", "Solar Masses"),
    ("total_mass_source", "m_total", "Solar Masses"),
    ("mass_1_source", "m_1", "Solar Masses"),
    ("mass_2_source", "m_2", "Solar Masses"),
    ("chirp_mass_source", "chirp mass", "Solar Masses"),
    ("chi_eff", "chi_eff", ""),
    ("redshift", "redshift", ""),
    ("luminosity_distance", "D_L", "Mpc"),
)


def _has_value(value: Any) -> bool:
    """Return whether a value is suitable for display."""
    if value is None:
        return False
    try:
        return bool(pd.notna(value))
    except (TypeError, ValueError):
        return True


def _format_number(value: Any) -> str:
    """Format numeric values compactly while preserving useful precision."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    if abs(number) >= 1000:
        return f"{number:.0f}"
    if abs(number) >= 100:
        return f"{number:.1f}"
    if abs(number) >= 10:
        return f"{number:.2f}".rstrip("0").rstrip(".")
    return f"{number:.3f}".rstrip("0").rstrip(".")


def _format_measurement(
    row: Mapping[str, Any],
    column: str,
    label: str,
    default_unit: str,
) -> str | None:
    """Format one best value with its upper and lower uncertainty."""
    value = row.get(column)
    if not _has_value(value):
        return None

    text = f"{label}: {_format_number(value)}"
    upper = row.get(f"{column}_upper_error")
    lower = row.get(f"{column}_lower_error")

    if _has_value(upper) or _has_value(lower):
        upper_text = _format_number(abs(float(upper))) if _has_value(upper) else "?"
        lower_text = _format_number(abs(float(lower))) if _has_value(lower) else "?"
        text += f" (+{upper_text} -{lower_text})"

    unit = row.get(f"{column}_unit") or default_unit
    if _has_value(unit) and str(unit).strip():
        text += f" {unit}"

    return text


def format_event_details(
    row: Mapping[str, Any],
    *,
    selected_column: str | None = None,
) -> str:
    """Build the text displayed after an event marker is clicked."""
    name = row.get("shortName") or row.get("name") or "Unknown event"
    lines = [f"Name: {name}", "messenger: Gravitational Waves"]

    if selected_column:
        selected_labels = {
            "final_mass_source": "final mass",
            "mass_1_source": "primary component",
            "mass_2_source": "secondary component",
        }
        lines.append(
            f"selected point: {selected_labels.get(selected_column, selected_column)}"
        )

    for column, label, default_unit in _MEASUREMENTS:
        measurement = _format_measurement(row, column, label, default_unit)
        if measurement:
            lines.append(measurement)

    catalog = row.get("catalog")
    if _has_value(catalog):
        lines.append(f"catalog: {catalog}")

    gps = row.get("gps")
    if _has_value(gps):
        lines.append(f"GPS: {_format_number(gps)}")

    snr = row.get("network_matched_filter_snr")
    if _has_value(snr):
        lines.append(f"SNR: {_format_number(snr)}")

    detectors = row.get("detectors")
    if _has_value(detectors) and str(detectors).strip():
        lines.append(f"detectors: {detectors}")

    reference = row.get("detail_url")
    if _has_value(reference):
        reference = str(reference)
        if len(reference) > 65:
            reference = reference[:62] + "..."
            lines.append(f"Reference: {reference}")

    return "\n".join(lines)


def enable_point_details(
    figure: Figure,
    axis: Axes,
    point_records: Mapping[PathCollection, PointRecord],
) -> int:
    """Display an event-detail box when one of the registered dots is clicked.

    Parameters
    ----------
    figure, axis:
        Matplotlib objects containing the plotted event markers.
    point_records:
        Mapping from each clickable scatter artist to its source event row and
        displayed mass column.

    Returns
    -------
    int
        Matplotlib callback connection identifier.
    """
    annotation = axis.annotate(
        "",
        xy=(0, 0),
        xytext=(16, 18),
        textcoords="offset points",
        ha="left",
        va="bottom",
        fontsize=9,
        color="black",
        bbox={
            "boxstyle": "round,pad=0.55",
            "facecolor": "#f2f2f2",
            "edgecolor": "#555555",
            "alpha": 0.97,
        },
        arrowprops={
            "arrowstyle": "->",
            "color": "white",
            "linewidth": 1.2,
        },
        zorder=20,
        annotation_clip=False,
    )
    annotation.set_visible(False)

    def on_pick(event: Any) -> None:
        artist = event.artist
        if artist not in point_records:
            return

        offsets = artist.get_offsets()
        point_index = int(event.ind[0]) if len(event.ind) else 0
        x, y = offsets[point_index]
        row, selected_column = point_records[artist]

        annotation.xy = (float(x), float(y))
        annotation.set_text(
            format_event_details(row, selected_column=selected_column)
        )

        x_min, x_max = axis.get_xlim()
        y_min, y_max = axis.get_ylim()

        x_fraction = (x-x_min) / (x_max - x_min)

        # The y-axis is logarithmic, so calculating the fraction in display coordinates

        point_display = axis.transData.transform((x, y))
        axes_box = axis.get_window_extent()
        y_fraction = (
            (point_display[1] - axes_box.y0)
            / axes_box.height
        )
        # Moving the box left or right depending on horizontal position.
        if x_fraction > 0.60:
            x_offset = -20
            horizontal_alignment = "right"
        else:
            x_offset = 20
            horizontal_alignment = "left"

        # Put the box below points near the top of the plot.
        if y_fraction > 0.65:
            y_offset = -20
            vertical_alignment = "top"
        else:
            y_offset = 20
            vertical_alignment = "bottom"

        annotation.set_position((x_offset, y_offset))
        annotation.set_horizontalalignment(horizontal_alignment)
        annotation.set_verticalalignment(vertical_alignment)

        annotation.set_visible(True)
        figure.canvas.draw_idle()

    def on_key(event: Any) -> None:
        if event.key == "escape" and annotation.get_visible():
            annotation.set_visible(False)
            figure.canvas.draw_idle()

    pick_connection = figure.canvas.mpl_connect("pick_event", on_pick)
    key_connection = figure.canvas.mpl_connect("key_press_event", on_key)

    # Retaining callback and artist references for the lifetime of the figure.
    figure._gwosc_point_details = {
        "annotation": annotation,
        "point_records": point_records,
        "on_pick": on_pick,
        "on_key": on_key,
        "connections": (pick_connection, key_connection),
    }

    return pick_connection
