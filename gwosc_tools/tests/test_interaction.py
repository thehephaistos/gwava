"""Tests for clickable event details."""

import unittest
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import pandas as pd

from gwosc_tools.interaction import format_event_details
from gwosc_tools.plotting import plot_masses
from gwosc_tools.sorting import create_diamond_layout


class InteractionTests(unittest.TestCase):
    def setUp(self):
        self.dataframe = pd.DataFrame(
            {
                "name": ["GW-test"],
                "shortName": ["GW-test-v1"],
                "gps": [1234567890.5],
                "catalog": ["GWTC-test"],
                "detectors": ["H1,L1"],
                "detail_url": ["https://example.test/GW-test"],
                "mass_1_source": [30.0],
                "mass_1_source_upper_error": [3.0],
                "mass_1_source_lower_error": [-2.0],
                "mass_2_source": [20.0],
                "final_mass_source": [47.0],
                "chirp_mass_source": [21.0],
                "chi_eff": [0.1],
                "redshift": [0.2],
                "luminosity_distance": [900.0],
                "network_matched_filter_snr": [14.2],
            }
        )

    def test_event_detail_text_contains_key_fields(self):
        text = format_event_details(
            self.dataframe.iloc[0],
            selected_column="mass_1_source",
        )

        self.assertIn("Name: GW-test-v1", text)
        self.assertIn("m_1: 30 (+3 -2)", text)
        self.assertIn("catalog: GWTC-test", text)
        self.assertIn("SNR: 14.2", text)
        self.assertIn("Reference: https://example.test/GW-test", text)

    def test_plot_registers_every_mass_marker(self):
        figure, _ = plot_masses(self.dataframe, show=False, interactive=True)
        state = figure._gwosc_point_details

        self.assertEqual(len(state["point_records"]), 3)
        self.assertFalse(state["annotation"].get_visible())

    def test_pick_event_displays_annotation(self):
        figure, _ = plot_masses(self.dataframe, show=False, interactive=True)
        state = figure._gwosc_point_details
        artist = next(iter(state["point_records"]))
        event = SimpleNamespace(artist=artist, ind=[0])

        state["on_pick"](event)

        self.assertTrue(state["annotation"].get_visible())
        self.assertIn("GW-test-v1", state["annotation"].get_text())

    def test_diamond_markers_retain_source_event_details(self):
        second = self.dataframe.copy()
        second.loc[0, "name"] = "GW-second"
        second.loc[0, "shortName"] = "GW-second-v1"
        second.loc[0, "mass_1_source"] = 60.0
        second.loc[0, "mass_2_source"] = 10.0
        second.loc[0, "final_mass_source"] = 66.0
        combined = pd.concat([self.dataframe, second], ignore_index=True)

        diamond = create_diamond_layout(combined)
        figure, _ = plot_masses(diamond, show=False, interactive=True)
        names = {
            record[0].get("shortName")
            for record in figure._gwosc_point_details["point_records"].values()
        }

        self.assertEqual(names, {"GW-test-v1", "GW-second-v1"})


if __name__ == "__main__":
    unittest.main()
