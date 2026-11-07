"""The citation of the tables is the same everywhere (README.md and the website), and the references
are in alphabetical order, as AGENTS.md asks.

The website test in test_tracking.py checks that the copy button copies the same text.
Run with:  python -B -m unittest tests/test_citation.py
"""

import csv
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



def authors_and_year(citation):
    """The surnames of the authors (in lower case) and the year of a citation of data/references.csv,
    such as "P. Beelen, M. Datta, S. R. Ghorpade, A combinatorial approach ..., Moscow Math. J. 22(4)
    (2022), 565–593.": the authors are the first parts, separated by commas, that start with initials,
    and the year is the last number of four digits between parentheses."""
    surnames = []
    for part in citation.split(", "):
        author = re.fullmatch(r"(?:\w\.\s*)+(\S.*)", part)      # initials, then the surname
        if author is None:
            break
        surnames.append(author.group(1).casefold())
    return surnames, int(re.findall(r"\((\d{4})\)", citation)[-1])


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

    def test_references_are_in_alphabetical_order(self):
        """The references are in alphabetical order of the surnames of their authors, then by year (as in
        the amsalpha style): in data/references.csv, whose order the website follows, and in the README."""
        with ROOT.joinpath("data", "references.csv").open(encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        keys = [row["key"] for row in rows]
        order = sorted(rows, key=lambda row: authors_and_year(row["citation"]))
        self.assertEqual(keys, [row["key"] for row in order], "keep data/references.csv in alphabetical order")
        section = read("README.md").split("## References", 1)[1]
        self.assertEqual(re.findall(r"(?m)^\* \*\*\[([^\]]+)\]\*\*", section), keys,
                         "list the references of the README in the order of data/references.csv")

    def test_authors_and_year(self):
        self.assertEqual(authors_and_year("P. Beelen, M. Datta, S. R. Ghorpade, A combinatorial approach to "
                                          "the number of solutions, Moscow Math. J. 22(4) (2022), 565–593."),
                         (["beelen", "datta", "ghorpade"], 2022))
        self.assertEqual(authors_and_year("T. Helleseth, T. Kløve, Ø. Ytrehus, Generalized Hamming weights of "
                                          "linear codes, IEEE Trans. Inform. Theory 38(3) (1992), 1133–1140."),
                         (["helleseth", "kløve", "ytrehus"], 1992))


if __name__ == "__main__":
    unittest.main()
