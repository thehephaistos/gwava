"""Visualizations for GWOSC event data."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D


def plot_masses(
    dataframe: pd.DataFrame,
    *,
    show: bool = True,
) -> tuple[Figure, Axes]:
    """Plot component and final masses for GWOSC compact-object mergers."""
    required_columns = {"mass_1_source", "mass_2_source"}
    missing = required_columns.difference(dataframe.columns)
    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(f"DataFrame is missing required columns: {names}")
    if dataframe.empty:
        raise ValueError("Cannot plot an empty DataFrame")

    blue = "#00a9e0"
    orange = "#d9901a"
    gray = "#8a8a8a"

    figure, axis = plt.subplots(figsize=(13, 7), facecolor="black")
    axis.set_facecolor("black")

    for position, (_, row) in enumerate(dataframe.iterrows()):
        mass_1 = float(row["mass_1_source"])
        mass_2 = float(row["mass_2_source"])
        final_mass = row.get("final_mass_source", np.nan)

        mass_1_color = orange if mass_1 < 3 else blue
        mass_2_color = orange if mass_2 < 3 else blue

        if pd.notna(final_mass):
            final_mass = float(final_mass)
            axis.plot(
                [position, position],
                [min(mass_1, mass_2), final_mass],
                color=gray,
                alpha=0.65,
                linewidth=1.2,
            )
            axis.scatter(
                position,
                final_mass,
                color=blue,
                s=90,
                edgecolor="black",
                linewidth=0.4,
                zorder=4,
            )

        axis.scatter(
            position,
            mass_1,
            color=mass_1_color,
            s=42,
            edgecolor="black",
            linewidth=0.4,
            zorder=5,
        )
        axis.scatter(
            position,
            mass_2,
            color=mass_2_color,
            s=42,
            edgecolor="black",
            linewidth=0.4,
            zorder=5,
        )

    axis.set_yscale("log")
    axis.set_ylim(1, 220)
    axis.set_xlim(-1, len(dataframe))
    axis.set_yticks([1, 2, 5, 10, 20, 50, 100, 200, 250])
    axis.set_yticklabels(
        ["1", "2", "5", "10", "20", "50", "100", "200", "250"],
        color="gray",
    )
    axis.set_xticks([])
    axis.set_ylabel("Solar Masses", color="gray", fontsize=14)
    axis.set_title(
        "Masses in the Stellar Graveyard",
        color="white",
        fontsize=30,
        pad=24,
    )
    axis.grid(axis="y", color="white", alpha=0.18, linewidth=1)

    for spine in axis.spines.values():
        spine.set_visible(False)

    legend_items = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            label="LIGO-Virgo-KAGRA Black Holes",
            markerfacecolor=blue,
            markersize=9,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            label="LIGO-Virgo-KAGRA Neutron Stars",
            markerfacecolor=orange,
            markersize=9,
        ),
    ]
    legend = axis.legend(
        handles=legend_items,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.05),
        ncol=2,
        frameon=False,
    )

    for text, color in zip(legend.get_texts(), [blue, orange]):
        text.set_color(color)

    figure.tight_layout()

    if show:
        plt.show()

    return figure, axis
