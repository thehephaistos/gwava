"""Backward-compatible command for the original YAML-loading script."""

from gwava.cli import main
from gwava.config import get_yaml, load_config

__all__ = ["get_yaml", "load_config"]


if __name__ == "__main__":
    raise SystemExit(main())
