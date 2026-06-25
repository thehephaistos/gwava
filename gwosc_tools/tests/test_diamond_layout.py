"""Tests for the visual diamond-fill layout."""

import unittest

import pandas as pd

from gwosc_tools.sorting import create_diamond_layout


class DiamondLayoutTests(unittest.TestCase):
    def setUp(self):
        self.dataframe = pd.DataFrame(
            {
                "name": ["A", "B", "C", "D", "E"],
                "mass_1_source": [10.0, 20.0, 30.0, 40.0, 50.0],
                "mass_2_source": [1.0, 2.0, 3.0, 4.0, 5.0],
                "final_mass_source": [11.0, 22.0, 33.0, 44.0, 55.0],
            }
        )

    def test_remnant_mass_is_largest_at_center(self):
        result = create_diamond_layout(self.dataframe)
        center = len(result) // 2

        self.assertEqual(result.loc[center, "final_mass_source"], 55.0)

    def test_component_span_is_largest_at_center(self):
        result = create_diamond_layout(self.dataframe)
        spans = result["mass_1_source"] - result["mass_2_source"]
        center = len(result) // 2

        self.assertEqual(spans.loc[center], spans.max())

    def test_component_values_are_preserved(self):
        original_values = sorted(
            self.dataframe["mass_1_source"].tolist()
            + self.dataframe["mass_2_source"].tolist()
        )
        result = create_diamond_layout(self.dataframe)
        result_values = sorted(
            result["mass_1_source"].tolist()
            + result["mass_2_source"].tolist()
        )

        self.assertEqual(result_values, original_values)

    def test_input_is_not_modified(self):
        original = self.dataframe.copy(deep=True)

        create_diamond_layout(self.dataframe)

        pd.testing.assert_frame_equal(self.dataframe, original)

    def test_layout_marks_event_associations_as_not_preserved(self):
        result = create_diamond_layout(self.dataframe)

        self.assertFalse(result.attrs["preserves_event_associations"])


if __name__ == "__main__":
    unittest.main()
