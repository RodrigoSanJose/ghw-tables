"""
Compute generalized Hamming weights of projective Reed-Muller codes with the package GHWs [SJ25] for
SageMath, and print the results as lines for data/manual.csv.

This is the only file of the repository that uses SageMath, and nothing else depends on it.  It needs
SageMath and the GHWs package (https://github.com/RodrigoSanJose/GHWs).  Run it from the repository
folder, with the Python of SageMath:

    sage -python sage/compute.py q d m        the weights of PRM_q(d,m) that are not known in the tables
    sage -python sage/compute.py q d m r      the weight d_r(PRM_q(d,m))
    sage -python sage/compute.py q d m all    all the weights of PRM_q(d,m), to compare them with the tables

If a weight is not known, the tables give  lower <= d_r <= upper  with lower < upper, and upper <= B_r,
the bound of [SJ26, Thm. 6.7].  By [SJ26, Conj. 6.9], d_r = B_r, so the script first asks GHW_bound
whether d_r >= upper.  GHW_bound stops as soon as it knows the answer, so this is usually much faster
than computing d_r.  If the answer is yes, then d_r = upper, and the line for data/manual.csv only gives
this lower bound (the upper bound is already justified in the tables).  If the answer is no, then
d_r < upper <= B_r, a counterexample to [SJ26, Conj. 6.9]: the script computes d_r with GHW and says so.

Add the lines printed at the end to data/manual.csv, and run  python3 src/generate.py.
"""

import csv
import io
import itertools
import json
import sys
import time
from datetime import date
from importlib.metadata import version
from pathlib import Path

from sage.all import GF, IntegerVectors, LinearCode, matrix, prod
from sage.version import version as sage_version

try:
    from GHWs import GHW, GHW_bound, hierarchy
except ImportError:
    sys.exit("The GHWs package is not installed, see https://github.com/RodrigoSanJose/GHWs")

VERBOSE = True    # GHWs prints its progress while it computes; set this to False to hide it.


def projective_points(q, m):
    """The points of P^m(F_q), each one given by its representative whose first nonzero coordinate is 1."""
    F = GF(q, "a")
    points = []
    for i in range(m + 1):                                  # i: the position of the first nonzero coordinate
        for rest in itertools.product(F, repeat=m - i):     # the m - i coordinates after it, in all possible ways
            points.append([F(0)] * i + [F(1)] + list(rest))
    return points


def prm_code(q, d, m):
    """PRM_q(d, m): the evaluations at the points of P^m(F_q) of the monomials of degree d in X_0, ..., X_m."""
    F = GF(q, "a")
    points = projective_points(q, m)
    rows = []
    for e in IntegerVectors(d, m + 1):     # the monomial X_0^e[0] * ... * X_m^e[m], where e[0] + ... + e[m] = d
        rows.append([prod(P[i]**e[i] for i in range(m + 1)) for P in points])
    basis = matrix(F, rows).row_space().basis_matrix()     # the rows may be linearly dependent: keep a basis
    return LinearCode(basis)


def read_table(q, d, m):
    """The length n of PRM_q(d, m), and its data in the tables (the file docs/data/q{q}_m{m}.json)."""
    path = Path("docs", "data", f"q{q}_m{m}.json")
    if not path.exists():
        sys.exit(f"{path} not found: run this script from the repository folder, for a code in the tables.")
    data = json.loads(path.read_text())
    for code in data["codes"]:
        if code["d"] == d:
            return data["n"], code
    sys.exit(f"PRM_{q}({d},{m}) is not in the tables.")


def csv_line(q, d, m, r, lower, upper, note):
    """A line of data/manual.csv with the source SJ25, the paper of GHWs (an empty lower or upper means no bound)."""
    text = io.StringIO()
    csv.writer(text, lineterminator="").writerow([q, d, m, r, lower, upper, "SJ25", note])
    return text.getvalue()


def report(code, q, d, m, r, computed_lower, computed_upper, note):
    """Print what was computed about d_r(PRM_q(d,m)), compared with its data in the tables (code).
    Returns the line for data/manual.csv, or None if there is nothing new."""
    value = computed_lower                                   # in every case, d_r >= computed_lower = value
    lower, upper = code["lower"][r], code["upper"][r]
    if value < lower or value > upper:
        print(f"WARNING: d_{r} = {value} contradicts the tables ({lower} <= d_{r} <= {upper}). Please report this.")
        return None
    if lower == upper:
        print(f"d_{r} = {value} agrees with the tables.", flush=True)
        return None
    if value < upper:
        print(f"d_{r} = {value} is smaller than the upper bound {upper}, so it is smaller than B_{r}: "
              f"this is a COUNTEREXAMPLE to [SJ26, Conj. 6.9]! Please check it carefully.")
    else:
        print(f"d_{r} = {value}: new value.")
    line = csv_line(q, d, m, r, computed_lower, computed_upper, f"{note}, {date.today()}")
    print(f"    {line}", flush=True)
    return line


def ghws_version():
    try:
        return version("GHWs")
    except Exception:
        return "(unknown version)"


USAGE = "usage: sage -python sage/compute.py q d m [r | all]   (see the beginning of this file)"
if len(sys.argv) not in (4, 5) or not all(argument.isdigit() for argument in sys.argv[1:4]):
    sys.exit(USAGE)
q, d, m = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
which = sys.argv[4] if len(sys.argv) > 4 else "open"
n, table = read_table(q, d, m)
k = table["k"]
if which not in ("open", "all") and not (which.isdigit() and 1 <= int(which) <= k):
    sys.exit(f"r must be a whole number between 1 and k = {k}, or all.\n{USAGE}")
C = prm_code(q, d, m)
if C.length() != n or C.dimension() != k:
    sys.exit(f"The code has length {C.length()} and dimension {C.dimension()}, but the tables say "
             f"n = {n} and k = {k}. Please report this.")
software = f"GHWs {ghws_version()}, SageMath {sage_version}"
print(f"PRM_{q}({d},{m}): length {C.length()}, dimension {k}.", flush=True)

# Each result is printed as soon as it is computed, so a long run can be stopped without losing them.
new_lines = []
if which == "all":
    start = time.time()
    H = [0] + list(hierarchy(C, verbose=VERBOSE))            # H[r] = d_r, as in the tables
    note = f"hierarchy(C), {software}, {time.time() - start:.0f} s for all the weights"
    for r in range(1, k + 1):
        new_lines.append(report(table, q, d, m, r, H[r], H[r], note))
else:
    if which == "open":
        rs = [r for r in range(1, k + 1) if table["lower"][r] < table["upper"][r]]
    else:
        rs = [int(which)]
    for r in rs:
        lower, upper = table["lower"][r], table["upper"][r]
        print(f"d_{r}: the tables say {lower} <= d_{r} <= {upper}. Computing...", flush=True)
        start = time.time()
        if lower < upper and GHW_bound(C, r, upper, bound_type="lower", verbose=VERBOSE):
            # GHWs proves d_r >= upper; the tables already have d_r <= upper, so d_r = upper.
            note = f"GHW_bound(C, {r}, {upper}) = True, {software}, {time.time() - start:.0f} s"
            new_lines.append(report(table, q, d, m, r, upper, "", note))
        else:
            value = GHW(C, r, verbose=VERBOSE)
            note = f"GHW(C, {r}), {software}, {time.time() - start:.0f} s"
            new_lines.append(report(table, q, d, m, r, value, value, note))

new_lines = [line for line in new_lines if line is not None]
print()
if new_lines:
    print("Add these lines to data/manual.csv, then run  python3 src/generate.py :")
    print()
    for line in new_lines:
        print(line)
else:
    print("Nothing new to add to data/manual.csv.")
