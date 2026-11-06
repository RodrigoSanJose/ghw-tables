"""The citation of the tables is the same everywhere: README.md and the website.

The website test in test_tracking.py checks that the copy button copies the same text.
Run with:  python -B -m unittest tests/test_citation.py
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CONCEPT_DOI = "10.5281/zenodo.24020768"   # all versions: the only Zenodo DOI the repository uses
VERSION_DOI = "10.5281/zenodo.24020769"   # the first version only: never used

BIBTEX = r"""@misc{sanjoseGHWTables,
  author       = {San-Jos{\'e}, Rodrigo},
  title        = {Tables of generalized {H}amming weights of
                  projective {Reed--Muller} codes},
  year         = {2026},
  howpublished = {Zenodo},
  note         = {Interactive tables:
                  \url{https://rodrigosanjose.github.io/ghw-tables/}.
                  Permanent DOI:
                  \url{https://doi.org/10.5281/zenodo.24020768}}
}"""


def read(name):
    return ROOT.joinpath(name).read_text(encoding="utf-8")


class TestCitation(unittest.TestCase):
    def test_readme_has_the_bibtex_entry(self):
        block = re.search(r"### Citation for the tables\n```\n(.*?)\n```", read("README.md"), re.S)
        self.assertIsNotNone(block)
        self.assertEqual(block.group(1), BIBTEX)

    def test_website_shows_the_bibtex_entry(self):
        block = re.search(r'<pre id="ghw-bibtex"><code>(.*?)</code></pre>', read("docs/index.html"), re.S)
        self.assertIsNotNone(block)
        self.assertEqual(block.group(1), BIBTEX)   # the entry has no characters that HTML would change

    def test_citation_cff_keeps_the_doi_field(self):
        cff = read("CITATION.cff")
        self.assertRegex(cff, r"(?m)^doi: " + re.escape(CONCEPT_DOI) + "$")
        self.assertRegex(cff, r"(?m)^url: 'https://rodrigosanjose\.github\.io/ghw-tables/'$")

    def test_only_the_concept_doi_is_used(self):
        for name in ("README.md", "CITATION.cff", "docs/index.html"):
            text = read(name)
            with self.subTest(file=name):
                self.assertNotIn(VERSION_DOI, text)
                self.assertNotIn("XXXXXXX", text)
                self.assertIn(CONCEPT_DOI, text)


if __name__ == "__main__":
    unittest.main()
