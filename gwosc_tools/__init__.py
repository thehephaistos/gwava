"""Utilities for loading GWOSC metadata, querying events, and plotting masses.

The public functions are imported lazily so that YAML and API helpers can be
used without importing the heavier data-analysis and plotting dependencies.
"""

from importlib import import_module
from typing import Any

__all__ = [
    "event_to_row",
    "events_to_dataframe",
    "fetch_all",
    "fetch_event_versions",
    "fetch_events_dataframe",
    "get_yaml",
    "load_config",
    "plot_masses",
]

_FUNCTION_MODULES = {
    "event_to_row": ".events",
    "events_to_dataframe": ".events",
    "fetch_all": ".api",
    "fetch_event_versions": ".api",
    "fetch_events_dataframe": ".events",
    "get_yaml": ".config",
    "load_config": ".config",
    "plot_masses": ".plotting",
}


def __getattr__(name: str) -> Any:
    """Load public functions only when they are first requested."""
    try:
        module_name = _FUNCTION_MODULES[name]
    except KeyError as error:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from error

    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value
