"""Functions for reading YAML configuration and specification files."""

from pathlib import Path
from typing import Any

import yaml


def load_config(yaml_path: str | Path) -> dict[str, Any]:
    """Load a YAML file and return its top-level mapping.

    Parameters
    ----------
    yaml_path:
        Path to the YAML file.

    Raises
    ------
    FileNotFoundError
        If ``yaml_path`` does not exist.
    ValueError
        If the YAML document does not contain a mapping at its top level.
    """
    path = Path(yaml_path).expanduser()

    if not path.is_file():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if config is None:
        return {}
    if not isinstance(config, dict):
        raise ValueError(f"Expected a YAML mapping in {path}, got {type(config).__name__}")

    return config


def get_yaml(yaml_path: str | Path) -> dict[str, Any]:
    """Return the parsed contents of a YAML file.

    This name is kept for compatibility with the original script.
    """
    return load_config(yaml_path)
