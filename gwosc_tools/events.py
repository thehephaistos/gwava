"""Transform GWOSC event responses into analysis-ready tables."""

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd
import requests

from .api import DEFAULT_RELEASES, fetch_event_versions


def event_to_row(event: Mapping[str, Any]) -> dict[str, Any]:
    """Flatten one GWOSC event and its default parameters into one row."""
    detectors = event.get("detectors") or []
    row = {
        "name": event.get("name"),
        "shortName": event.get("shortName"),
        "gps": event.get("gps"),
        "version": event.get("version"),
        "catalog": event.get("catalog"),
        "detectors": ",".join(detectors),
        "detail_url": event.get("detail_url"),
    }

    for parameter in event.get("default_parameters") or []:
        name = parameter.get("name")
        if not name:
            continue

        row[name] = parameter.get("best")
        row[f"{name}_upper_error"] = parameter.get("upper_error")
        row[f"{name}_lower_error"] = parameter.get("lower_error")
        row[f"{name}_unit"] = parameter.get("unit")

    return row


def events_to_dataframe(
    events: Sequence[Mapping[str, Any]],
    *,
    require_component_masses: bool = True,
    sort_by_gps: bool = True,
) -> pd.DataFrame:
    """Convert GWOSC events into a flattened pandas DataFrame."""
    dataframe = pd.DataFrame(event_to_row(event) for event in events)

    if dataframe.empty:
        return dataframe

    if require_component_masses:
        required_columns = {"mass_1_source", "mass_2_source"}
        missing = required_columns.difference(dataframe.columns)
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"Event data is missing required mass columns: {names}")
        dataframe = dataframe.dropna(subset=sorted(required_columns))

    if sort_by_gps and "gps" in dataframe.columns:
        dataframe = dataframe.sort_values("gps")

    return dataframe.reset_index(drop=True)


def fetch_events_dataframe(
    releases: Sequence[str] = DEFAULT_RELEASES,
    *,
    session: requests.Session | None = None,
    timeout: float = 30,
) -> pd.DataFrame:
    """Fetch GWOSC events and return an analysis-ready DataFrame."""
    events = fetch_event_versions(
        releases,
        session=session,
        timeout=timeout,
    )
    return events_to_dataframe(events)
