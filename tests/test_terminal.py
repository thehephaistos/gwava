"""Tests for terminal loading indicators."""

import io
import time
import unittest

from gwava.terminal import loading_indicator


class FakeTerminal(io.StringIO):
    def isatty(self):
        return True


class LoadingIndicatorTests(unittest.TestCase):
    def test_spinner_is_quiet_for_non_terminal_output(self):
        stream = io.StringIO()

        with loading_indicator("Working...", stream=stream, interval=0.001):
            pass

        self.assertEqual(stream.getvalue(), "")

    def test_spinner_prints_completion_in_terminal(self):
        stream = FakeTerminal()

        with loading_indicator("Working...", stream=stream, interval=0.001):
            time.sleep(0.005)

        output = stream.getvalue()
        self.assertIn("Working...", output)
        self.assertIn("✓", output)

    def test_spinner_reports_failure_and_reraises(self):
        stream = FakeTerminal()

        with self.assertRaisesRegex(RuntimeError, "failed"):
            with loading_indicator("Working...", stream=stream, interval=0.001):
                raise RuntimeError("failed")

        self.assertIn("✗", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
