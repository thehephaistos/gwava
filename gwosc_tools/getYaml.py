"""Backward-compatible command for the original YAML-loading script."""

from gwosc_tools.gwosc_tools.cli import main
from gwosc_tools.gwosc_tools.config import get_yaml, load_config

__all__ = ["get_yaml", "load_config"]


if __name__ == "__main__":
    raise SystemExit(main())
