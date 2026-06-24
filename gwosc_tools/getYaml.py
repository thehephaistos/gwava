"""Backward-compatible command for the original YAML-loading script."""

<<<<<<< HEAD
from gwosc_tools.gwosc_tools.cli import main
from gwosc_tools.gwosc_tools.config import get_yaml, load_config
=======
from gwosc_tools.cli import main
from gwosc_tools.config import get_yaml, load_config
>>>>>>> 3ccc7cab659efba6f9891c3fae990022e08689f7

__all__ = ["get_yaml", "load_config"]


if __name__ == "__main__":
    raise SystemExit(main())
