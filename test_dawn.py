#!/usr/bin/env python3
"""Unit tests for validating dawn_report_enhanced.sh script."""

import os
import subprocess
import unittest


class TestDawnScript(unittest.TestCase):
    """Test suite for dawn_report_enhanced.sh script validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.script_path = os.path.expanduser("~/imperial_network/dawn_report_enhanced.sh")

    def test_script_exists(self):
        """Test that the dawn_report_enhanced.sh script exists."""
        self.assertTrue(
            os.path.exists(self.script_path),
            f"Script does not exist at {self.script_path}"
        )

    def test_script_is_executable(self):
        """Test that the script has executable permissions."""
        self.assertTrue(
            os.access(self.script_path, os.X_OK),
            f"Script is not executable: {self.script_path}"
        )

    def test_script_syntax_valid(self):
        """Test that the script passes bash syntax validation."""
        result = subprocess.run(
            ["bash", "-n", self.script_path],
            capture_output=True,
            text=True
        )
        self.assertEqual(
            result.returncode, 0,
            f"Bash syntax validation failed for {self.script_path}\n"
            f"Error output: {result.stderr}"
        )


if __name__ == "__main__":
    unittest.main()
