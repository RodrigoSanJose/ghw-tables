"""
Tests for sage/compute.py that do not need SageMath.  Run them with the other tests:

    python3 -m unittest discover -s tests -v

Small stand-ins for Sage and GHWs are written to a temporary folder, and the script runs in a separate
process (it reads its arguments as soon as it starts), from a folder with an invented table.  The
stand-in for GF() stops the script, so these tests only cover what happens before the code is built:
the arguments, and whether there is anything to compute.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent.joinpath("sage", "compute.py")
STAND_INS = {
    "sage/__init__.py": "",
    "sage/all.py": "def GF(*args):\n    raise SystemExit('BUILDING THE CODE')\n\n"
                   "IntegerVectors = LinearCode = matrix = prod = None\n",
    "sage/version.py": "version = 'stand-in'\n",
    "GHWs.py": "GHW = GHW_bound = hierarchy = None\n",
}
# An invented table q = 2, m = 1 in the format of docs/data: d_2 of the first code is not known.
TABLE = {"q": 2, "m": 1, "n": 3, "codes": [
    {"d": 1, "k": 2, "lower": [0, 2, 2], "upper": [0, 2, 3]},
    {"d": 2, "k": 3, "lower": [0, 1, 2, 3], "upper": [0, 1, 2, 3]}]}


class TestCompute(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.root = Path(cls.folder.name)
        for name, text in STAND_INS.items():
            path = cls.root.joinpath("stand-ins", name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        cls.root.joinpath("docs", "data").mkdir(parents=True)
        cls.root.joinpath("docs", "data", "q2_m1.json").write_text(json.dumps(TABLE))

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def run_script(self, *arguments):
        """The exit status of `python3 sage/compute.py arguments`, and everything it printed."""
        environment = dict(os.environ, PYTHONPATH=str(self.root.joinpath("stand-ins")))
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), *arguments], cwd=self.root,
                                env=environment, capture_output=True, text=True, timeout=60)
        return result.returncode, result.stdout + result.stderr

    def test_nothing_to_compute(self):
        """Without r, the script stops before building the code when every weight is known."""
        status, output = self.run_script("2", "2", "1")
        self.assertEqual(status, 0, output)
        self.assertIn("nothing to compute", output)
        self.assertNotIn("BUILDING THE CODE", output)

    def test_something_to_compute(self):
        """An unknown weight, a given r (to check a known value) and all build the code."""
        for arguments in (["2", "1", "1"], ["2", "2", "1", "3"], ["2", "2", "1", "all"]):
            with self.subTest(arguments=arguments):
                self.assertIn("BUILDING THE CODE", self.run_script(*arguments)[1])

    def test_invalid_arguments(self):
        """Invalid arguments give the usage, not a Python error, before building the code."""
        for arguments in ([], ["2", "1"], ["2", "x", "1"], ["2", "1", "1", "0"], ["2", "1", "1", "3"],
                          ["2", "1", "1", "x"], ["2", "1", "1", "²"], ["2", "1", "1", "1", "1"]):
            with self.subTest(arguments=arguments):
                status, output = self.run_script(*arguments)
                self.assertNotEqual(status, 0, output)
                self.assertIn("usage:", output)
                self.assertNotIn("Traceback", output)
                self.assertNotIn("BUILDING THE CODE", output)


if __name__ == "__main__":
    unittest.main()
