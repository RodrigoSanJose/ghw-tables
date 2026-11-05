"""
Compute the tables and write them for the website.  From the repository folder, run

    python3 src/generate.py

It does the following:
  1. start with the trivial bounds  r <= d_r <= p_m  for every code of src/parameters.py;
  2. read the computed values of data/manual.csv;
  3. apply all the rules of src/rules.py to all the codes, again and again, until a full pass
     improves nothing;
  4. check that every lower bound is at most the corresponding upper bound;
  5. print a summary, and write the tables for the website in docs/data/.

Everything is computed from scratch every time, so never edit the files in docs/data/ by hand.
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

from formulas import B, dim_PRM, p
from parameters import codes
from rules import RULES
from table import TRIVIAL, Table

REPOSITORY = Path(__file__).resolve().parent.parent
MANUAL = REPOSITORY.joinpath("data", "manual.csv")
REFERENCES = REPOSITORY.joinpath("data", "references.csv")
OUTPUT = REPOSITORY.joinpath("docs", "data")


def read_references(path):
    """The references of data/references.csv, as a dictionary  key -> {"citation": ..., "link": ...}."""
    references = {}
    with open(path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            references[row["key"]] = {"citation": row["citation"], "link": row["link"]}
    return references


def read_computed_values(table, path, references):
    """Read data/manual.csv into table.computed, checking every line.

    The columns are  q, d, m, r, lower, upper, source, note.  An empty `lower` (or `upper`) means
    that the line only gives an upper (or a lower) bound.  The source must be a key of
    data/references.csv.  The program stops with a message if a line is not valid.
    """
    with open(path, newline="", encoding="utf-8") as file:
        for line, row in enumerate(csv.DictReader(file), start=2):     # line 1 is the header
            where = f"{path.name}, line {line}"
            q, d, m, r = int(row["q"]), int(row["d"]), int(row["m"]), int(row["r"])
            lower = int(row["lower"]) if row["lower"].strip() else None
            upper = int(row["upper"]) if row["upper"].strip() else None
            if (q, d, m) not in table.lower:
                sys.exit(f"{where}: PRM_{q}({d},{m}) is not in the tables (see src/parameters.py).")
            if not 1 <= r <= dim_PRM(q, d, m):
                sys.exit(f"{where}: r must be between 1 and k_d(m) = {dim_PRM(q, d, m)}.")
            if lower is None and upper is None:
                sys.exit(f"{where}: give a lower bound, an upper bound, or both.")
            if lower is not None and upper is not None and lower > upper:
                sys.exit(f"{where}: the lower bound is larger than the upper bound.")
            if row["source"] not in references:
                sys.exit(f"{where}: the source '{row['source']}' is not a key of {REFERENCES.name}.")
            entry = {"r": r, "lower": lower, "upper": upper, "source": row["source"], "note": row["note"]}
            # Add the entry to the list of entries of this code (creating the list if needed).
            table.computed.setdefault((q, d, m), []).append(entry)


def fill(table):
    """Apply all the rules to all the codes, again and again, until a full pass improves nothing.
    Returns the number of passes."""
    passes = 0
    while True:
        passes += 1
        changes = 0
        for q, d, m in table.codes:             # by q, then m, then d (see table.py)
            for rule in RULES:
                changes += rule(table, q, d, m)
        print(f"Pass {passes}: {changes} bounds improved.")
        if changes == 0:
            return passes


def all_entries(table):
    """All the pairs (code, r) of the table, with code = (q, d, m) and 1 <= r <= k_d(m)."""
    for code in table.codes:
        for r in range(1, len(table.lower[code])):
            yield code, r


def check(table):
    """Stop if some lower bound is larger than the corresponding upper bound.  Otherwise return the
    list of counterexamples to [PRM, Conj. 6.9], i.e. the upper bounds smaller than B_r(q, d, m)."""
    contradictions = []
    counterexamples = []
    for code, r in all_entries(table):
        q, d, m = code
        name = f"d_{r}(PRM_{q}({d},{m}))"
        lower, upper = table.lower[code][r], table.upper[code][r]
        if lower > upper:
            contradictions.append(f"{name}: lower bound {lower} {table.lower_reason[code][r]} is larger "
                                  f"than the upper bound {upper} {table.upper_reason[code][r]}")
        if upper < B(q, d, m, r):
            counterexamples.append(f"{name} <= {upper} < B_r = {B(q, d, m, r)}, "
                                   f"by {table.upper_reason[code][r]}")
    if contradictions:
        print("\nCONTRADICTIONS (a computed value or a formula must be wrong):")
        for text in contradictions:
            print("  " + text)
        sys.exit(1)
    return counterexamples


def print_report(table, counterexamples):
    """Print a summary of the tables."""
    weights = Counter()           # number of weights, for each q
    exact = Counter()             # number of exact weights, for each q
    lower_rules = Counter()       # how many lower bounds come from each rule
    upper_rules = Counter()
    trivial = 0
    for code, r in all_entries(table):
        q = code[0]
        weights[q] += 1
        if table.is_exact(code, r):
            exact[q] += 1
        lower_rules[table.lower_reason[code][r]["rule"]] += 1
        upper_rules[table.upper_reason[code][r]["rule"]] += 1
        if table.lower_reason[code][r] is TRIVIAL or table.upper_reason[code][r] is TRIVIAL:
            trivial += 1

    total, total_exact = sum(weights.values()), sum(exact.values())
    print(f"\n{len(table.codes)} codes, {total} weights: {total_exact} exact, {total - total_exact} open.")
    for q in sorted(weights):
        print(f"  q = {q}: {weights[q]} weights, {exact[q]} exact, {weights[q] - exact[q]} open.")
    print("Lower bounds by rule: " + ", ".join(f"{rule}: {n}" for rule, n in lower_rules.most_common()))
    print("Upper bounds by rule: " + ", ".join(f"{rule}: {n}" for rule, n in upper_rules.most_common()))
    if trivial:
        print(f"WARNING: {trivial} weights still have a trivial bound.")
    if counterexamples:
        print("\nCOUNTEREXAMPLES TO [PRM, Conj. 6.9]:")
        for text in counterexamples:
            print("  " + text)
    else:
        print("No counterexample to [PRM, Conj. 6.9]: every upper bound is at least B_r(q, d, m).")


def write_json(path, data):
    """Write data to a JSON file, in a compact form.  The same data always gives the same file."""
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, separators=(",", ":"))
        file.write("\n")


def write_website_data(table, references, folder):
    """Write one file q{q}_m{m}.json for each pair (q, m), with all the codes PRM_q(d, m), and an
    index file index.json.  The files of a previous run are deleted first."""
    folder.mkdir(parents=True, exist_ok=True)
    for old_file in folder.glob("*.json"):
        old_file.unlink()

    degrees = {}                                  # degrees[q, m] = the list of degrees d
    for q, d, m in table.codes:
        degrees.setdefault((q, m), []).append(d)

    index = {"references": references, "tables": []}
    for (q, m), ds in degrees.items():
        data = {"q": q, "m": m, "n": p(q, m), "codes": []}
        exact = total = 0
        for d in ds:
            code = (q, d, m)
            data["codes"].append({"d": d, "k": dim_PRM(q, d, m),
                                  "lower": table.lower[code], "upper": table.upper[code],
                                  "lower_reason": table.lower_reason[code],
                                  "upper_reason": table.upper_reason[code]})
            for r in range(1, dim_PRM(q, d, m) + 1):
                total += 1
                exact += table.is_exact(code, r)
        file_name = f"q{q}_m{m}.json"
        write_json(folder.joinpath(file_name), data)
        index["tables"].append({"q": q, "m": m, "n": p(q, m), "degrees": ds, "file": file_name,
                                "weights": total, "exact": exact})
    write_json(folder.joinpath("index.json"), index)
    print(f"\nWrote {len(index['tables'])} tables and index.json in {folder}.")


def main():
    table = Table(codes())
    references = read_references(REFERENCES)
    read_computed_values(table, MANUAL, references)
    passes = fill(table)
    print(f"No bound improved in pass {passes}, so the tables are complete.")
    counterexamples = check(table)
    print_report(table, counterexamples)
    write_website_data(table, references, OUTPUT)


if __name__ == "__main__":
    main()
