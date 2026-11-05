"""
Tests for the table, the rules and generate.py.  Run them with the other tests:

    python3 -m unittest discover -s tests -v

They use a small range of codes, so that they take a few seconds.
"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.joinpath("src")
sys.path.insert(0, str(SRC))

from formulas import B, dim_PRM  # noqa: E402
from generate import (MANUAL, REFERENCES, check, fill, read_computed_values,  # noqa: E402
                      read_references, write_website_data)
from parameters import codes  # noqa: E402
from table import TRIVIAL, Table  # noqa: E402

SMALL = {2: 4, 3: 4, 4: 3}            # for each q, the largest m used in these tests
HEADER = "q,d,m,r,lower,upper,source,note\n"


def small_table(manual_text=None):
    """The filled table for the codes of SMALL, with the computed values of data/manual.csv,
    or with those of the text manual_text (in the format of data/manual.csv)."""
    table = Table(codes(SMALL))
    references = read_references(REFERENCES)
    if manual_text is None:
        read_computed_values(table, MANUAL, references)
    else:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder).joinpath("manual.csv")
            path.write_text(manual_text, encoding="utf-8")
            read_computed_values(table, path, references)
    with redirect_stdout(io.StringIO()):          # do not print the passes
        fill(table)
    return table


class TestTables(unittest.TestCase):

    def test_conjecture_verified_for_q3_m3(self):
        """[PRM], end of Section 6.3: with d_7(PRM_3(4,3)) = 16, all the weights of PRM_3(d,3) are known,
        and they are the bounds B_r(3, d, 3)."""
        table = small_table()
        for d in range(1, 8):
            for r in range(1, dim_PRM(3, d, 3) + 1):
                self.assertTrue(table.is_exact((3, d, 3), r), (d, r))
                self.assertEqual(table.lower[3, d, 3][r], B(3, d, 3, r), (d, r))
        self.assertEqual(table.lower_reason[3, 4, 3][7]["rule"], "computed")
        self.assertEqual(table.upper_reason[3, 4, 3][7]["rule"], "PRM Thm 6.7")

    def test_without_the_computed_value(self):
        """Without the computation, [SJ24, Thm 7] and B_r only give 15 <= d_7(PRM_3(4,3)) <= 16."""
        table = small_table(HEADER)
        self.assertEqual(table.lower[3, 4, 3][7], 15)
        self.assertEqual(table.upper[3, 4, 3][7], 16)

    def test_new_value_propagates(self):
        """The value d_7(PRM_3(4,3)) = 16 improves [SJ24, Thm 7] for the larger code PRM_3(6,4)."""
        self.assertEqual(small_table(HEADER).lower[3, 6, 4][30], 42)
        self.assertEqual(small_table().lower[3, 6, 4][30], 43)

    def test_bounds_are_consistent(self):
        """lower <= upper, lower <= B_r, and no trivial bound survives."""
        table = small_table()
        for code in table.codes:
            q, d, m = code
            for r in range(1, dim_PRM(q, d, m) + 1):
                self.assertLessEqual(table.lower[code][r], table.upper[code][r], (code, r))
                self.assertLessEqual(table.lower[code][r], B(q, d, m, r), (code, r))
                self.assertIsNot(table.lower_reason[code][r], TRIVIAL, (code, r))
                self.assertIsNot(table.upper_reason[code][r], TRIVIAL, (code, r))

    def test_contradiction_stops(self):
        """A computed lower bound above B_r is impossible: generate.py must stop."""
        table = small_table(HEADER + "3,4,3,7,17,,GHWs,a wrong value\n")
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            check(table)

    def test_counterexample_is_reported(self):
        """An upper bound below B_r would be a counterexample to [PRM, Conj. 6.9] (this one is invented)."""
        table = small_table(HEADER + "3,4,3,7,,15,GHWs,an invented value\n")
        counterexamples = check(table)
        self.assertEqual(len(counterexamples), 1)
        self.assertIn("d_7(PRM_3(4,3))", counterexamples[0])

    def test_invalid_lines(self):
        """generate.py stops with a message when a line of data/manual.csv is not valid."""
        for line in ["5,4,3,7,16,16,GHWs,x",       # PRM_5(4,3) is not among the codes of SMALL
                     "3,4,3,30,16,16,GHWs,x",      # r = 30 > k_4(3) = 29
                     "3,4,3,7,,,GHWs,x",           # no bound at all
                     "3,4,3,7,17,16,GHWs,x",       # lower > upper
                     "3,4,3,7,16,16,Nobody,x"]:    # unknown source
            with self.assertRaises(SystemExit):
                small_table(HEADER + line + "\n")

    def test_website_files(self):
        """The files for the website contain the table, and the same table gives the same files."""
        table = small_table()
        references = read_references(REFERENCES)
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            with redirect_stdout(io.StringIO()):
                write_website_data(table, references, Path(first))
                write_website_data(table, references, Path(second))
            for path in Path(first).glob("*.json"):
                self.assertEqual(path.read_bytes(), Path(second).joinpath(path.name).read_bytes())
            data = json.loads(Path(first).joinpath("q3_m3.json").read_text())
            code = [c for c in data["codes"] if c["d"] == 4][0]
            self.assertEqual(code["k"], 29)
            self.assertEqual((code["lower"][7], code["upper"][7]), (16, 16))
            index = json.loads(Path(first).joinpath("index.json").read_text())
            self.assertIn("SJ24", index["references"])


if __name__ == "__main__":
    unittest.main()
