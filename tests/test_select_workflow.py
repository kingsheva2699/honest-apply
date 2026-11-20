import json
import subprocess
import sys
from pathlib import Path

import tempfile
import unittest

from select_workflow import select


CASES = [
        ({}, "core"),
        ({"model": "gpt-5"}, "core"),
        ({"model": "unknown"}, "core"),
        ({"model": "Claude Opus 4"}, "claude"),
        ({"model": "anthropic/claude-sonnet-4-5"}, "claude"),
        ({"model": "anthropic.claude-3"}, "claude"),
        ({"model": "not-claude"}, "core"),
        ({"host": "claude"}, "claude"),
        ({"host": "other", "model": "claude-opus-4"}, "core"),
        ({"host": "claude", "board": "indeed"}, "indeed"),
        ({"board": "indeed"}, "indeed"),
        ({"board": "linkedin", "model": "claude-sonnet"}, "claude"),
        ({"board": "linkedin"}, "core"),
        ({"runtime": False, "board": "indeed", "host": "claude"}, "manual"),
]

class SelectionTest(unittest.TestCase):
    def test_selection(self):
        root = Path(__file__).resolve().parents[1]
        for settings, edition in CASES:
            with self.subTest(settings=settings):
                result = select(**settings)
                self.assertEqual(result["edition"], edition)
                self.assertEqual(result["application"], "manual")
                self.assertTrue((root / result["workflow"]).is_file())
                if result["script"]:
                    self.assertTrue((root / result["script"]).is_file())
                else:
                    self.assertEqual(edition, "manual")

    def test_cli_from_another_directory(self):
        script = Path(__file__).resolve().parents[1] / "select_workflow.py"
        with tempfile.TemporaryDirectory() as tmp:
            out = subprocess.check_output([sys.executable, str(script), "--model", "claude-opus-4"], cwd=tmp)
        self.assertEqual(json.loads(out)["edition"], "claude")
