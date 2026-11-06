"""Reference metadata survives CSV loading and website export without computing tables."""

import csv
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.joinpath("src")
sys.path.insert(0, str(SRC))

from generate import read_references, write_website_data  # noqa: E402
from table import Table  # noqa: E402


class TestReferenceMetadata(unittest.TestCase):

    def write_references(self, folder, columns, row):
        path = Path(folder).joinpath("references.csv")
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerow(row)
        return path

    def test_legacy_three_columns_remain_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_references(folder, ["key", "citation", "link"],
                                         ["Old", "A. Author, Original title, Journal.", "https://example.org/paper"])
            self.assertEqual(read_references(path), {"Old": {
                "citation": "A. Author, Original title, Journal.",
                "link": "https://example.org/paper"}})

    def test_comma_title_and_short_title_survive_export(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_references(folder, ["key", "citation", "link", "title", "short_title"],
                                         ["New", "A. Author, Codes, weights, and bounds, Journal.",
                                          "https://example.org/new", "Codes, weights, and bounds", "Codes and bounds"])
            references = read_references(path)
            output = Path(folder).joinpath("website")
            with redirect_stdout(io.StringIO()):
                write_website_data(Table([(2, 1, 1)]), references, output)
            exported = json.loads(output.joinpath("index.json").read_text(encoding="utf-8"))["references"]
            self.assertEqual(exported["New"], {
                "citation": "A. Author, Codes, weights, and bounds, Journal.",
                "link": "https://example.org/new",
                "title": "Codes, weights, and bounds", "short_title": "Codes and bounds"})

    def test_empty_optional_metadata_is_omitted(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_references(folder, ["key", "citation", "link", "title", "short_title"],
                                         ["Empty", "Citation", "https://example.org", "", "  "])
            self.assertEqual(read_references(path)["Empty"], {
                "citation": "Citation", "link": "https://example.org"})

    def test_arbitrary_metadata_columns_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_references(folder, ["key", "citation", "link", "visitor_id"],
                                         ["Bad", "Citation", "https://example.org", "never-export"])
            with self.assertRaises(SystemExit):
                read_references(path)


if __name__ == "__main__":
    unittest.main()
