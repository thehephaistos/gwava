"""Command-line interface for inspecting the YAML spec and plotting events."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from .terminal import loading_indicator


def build_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser.
    
    Builds an ```argparse.ArgumentParser`` for loading the GWOSC YAML
    specification and controlling option plotting behavior.

    Supported command-line options include:
        --plot-masses : Fetch GWOSC event data and display a mass plot.
        --save        : Save the generated mass plot to a file.
        --no-show     : Suppress opening the plot window.
        --sort        : Choose how events are ordered in the plot.
        --random-seed : Set the random seed when using random sorting.

    Args: 
        None

    Returns: 
        argparse.ArgumentParser: A configured paruser for the CLI.
    """
    parser = argparse.ArgumentParser(
        description="Load the GWOSC YAML specification and optionally plot event masses."
    )

    parser.add_argument(
        "--plot-masses",
        action="store_true",
        help="Fetch GWOSC events and display the stellar-mass plot",
    )
    parser.add_argument(
        "--save",
        type=Path,
        metavar="IMAGE_PATH",
        help="Save the mass plot to this path",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open the plot window (useful together with --save)",
    )

    parser.add_argument(
        '--sort',
        default='date',
        choices=[
            'rising', 
            'peaked', 
            'valley',
            'falling',
            'random',
            'diamond',
            'date',
            'distance',
            'chirp_mass',
            'chi_eff',
            'snr'
            
            ],
            help="choose how events are sorted in the plot. Default is 'date'.",
    )
    parser.add_argument(
        '--random-seed',
        type=int,
        default=391,
        help="Random seed for sorting events when --sort=random is used. Default is 391"
    )
    return parser


def run_argument(argv: Sequence[str] | None = None) -> int:
        """Run the command-line application.

    Parses command-line arguments, fetches and sorts gravitational-wave
    event data when plotting is requested, and generates or saves the
    corresponding mass plot.

    Behavior depends on the parsed options:
        - ``--plot-masses`` triggers event fetching and plotting.
        - ``--save`` writes the plot image to disk.
        - ``--no-show`` suppresses displaying the interactive plot window.
        - ``--sort`` controls event ordering.
        - ``--random-seed`` sets the seed for random sorting.

    Args:
        argv (Sequence[str] | None): Optional sequence of command-line
            arguments. If ``None``, arguments are read from ``sys.argv``.

    Returns:
        int: Exit status code (0 for successful execution).
    """

    if args.plot_masses or args.save:
        with loading_indicator("Fetching and preparing GWOSC plot..."):
            from .events import fetch_events_dataframe
            from .plotting import plot_masses
            from .sorting import sort_events

            dataframe = fetch_events_dataframe()

            dataframe = sort_events(
                dataframe,
                mode=args.sort,
                random_seed=args.random_seed
            )

            # Stop the terminal spinner before opening the interactive window.
            figure, _ = plot_masses(dataframe, show=False)

            if args.save:
                args.save.parent.mkdir(parents=True, exist_ok=True)
                figure.savefig(args.save, dpi=200, bbox_inches="tight")

        if args.save:
            print(f"Saved plot: {args.save}")

        if not args.no_show:
            import matplotlib.pyplot as plt

            plt.show()

    return 0


def main() -> int:
    """CLI entry point."""
    return run_argument()
