"""Tests for the peaked and valley event layouts."""

import unittest

import numpy as np
import pandas as pd

from gwosc_tools import (
    create_peaked_layout,
    create_valley_layout,
    sort_events,
)


class MassLayoutTests(unittest.TestCase):
    def setUp(self):
        self.dataframe = pd.DataFrame(
            {
                "name": ["one", "two", "three", "four", "five"],
                "final_mass_source": [1.0, 2.0, 3.0, 4.0, 5.0],
            }
        )

    def test_peaked_layout_has_largest_mass_at_center(self):
        result = create_peaked_layout(self.dataframe)

        self.assertEqual(result["final_mass_source"].tolist(), [1, 3, 5, 4, 2])
        self.assertEqual(result.iloc[len(result) // 2]["name"], "five")

    def test_valley_layout_has_smallest_mass_at_center(self):
        result = create_valley_layout(self.dataframe)

        self.assertEqual(result["final_mass_source"].tolist(), [5, 3, 1, 2, 4])
        self.assertEqual(result.iloc[len(result) // 2]["name"], "one")

    def test_even_number_of_events_forms_two_center_extrema(self):
        dataframe = self.dataframe.iloc[:4]

        peaked = create_peaked_layout(dataframe)
        valley = create_valley_layout(dataframe)

        self.assertEqual(peaked["final_mass_source"].tolist(), [1, 3, 4, 2])
        self.assertEqual(valley["final_mass_source"].tolist(), [4, 2, 1, 3])

    def test_layouts_do_not_modify_input(self):
        original = self.dataframe.copy(deep=True)

        create_peaked_layout(self.dataframe)
        create_valley_layout(self.dataframe)

        pd.testing.assert_frame_equal(self.dataframe, original)

    def test_missing_mass_is_preserved_at_end(self):
        dataframe = pd.concat(
            [
                self.dataframe,
                pd.DataFrame({"name": ["missing"], "final_mass_source": [np.nan]}),
            ],
            ignore_index=True,
        )

        peaked = create_peaked_layout(dataframe)
        valley = create_valley_layout(dataframe)

        self.assertEqual(peaked.iloc[-1]["name"], "missing")
        self.assertEqual(valley.iloc[-1]["name"], "missing")
        self.assertEqual(len(peaked), len(dataframe))
        self.assertEqual(len(valley), len(dataframe))

    def test_sort_events_uses_public_layout_behavior(self):
        pd.testing.assert_frame_equal(
            sort_events(self.dataframe, "peaked"),
            create_peaked_layout(self.dataframe),
        )
        pd.testing.assert_frame_equal(
            sort_events(self.dataframe, "valley"),
            create_valley_layout(self.dataframe),
        )


if __name__ == "__main__":
    unittest.main()
