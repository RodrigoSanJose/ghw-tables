"""
The table of bounds.

For every code PRM_q(d, m) in the tables and every 0 <= r <= k_d(m), the table stores

    table.lower[q, d, m][r]   <=   d_r(PRM_q(d, m))   <=   table.upper[q, d, m][r],

and the reason for each of the two bounds, in table.lower_reason and table.upper_reason.
As for the hierarchies in formulas.py, position r = 0 holds d_0 = 0.

These four are Python dictionaries whose keys are the triples (q, d, m): table.lower[q, d, m] is
the same as table.lower[(q, d, m)], and as table.lower[code] with code = (q, d, m).  Each value is
a list indexed by r.

A reason is a small dictionary such as {"rule": "PRM Thm 6.7", "n": 24, "set": "-"}: the name of
the result used, and the data needed to explain it.  The website turns it into a sentence.
"""

from formulas import dim_PRM, p

# The reason of the bounds we start with: d_r >= r (an r-dimensional subcode has at least r
# coordinates in its support) and d_r <= p_m (the length).  They never survive in the final tables.
TRIVIAL = {"rule": "trivial"}


def q_then_m_then_d(code):
    """The key used to sort the codes (q, d, m): by q, then m, then d."""
    q, d, m = code
    return (q, m, d)


class Table:

    def __init__(self, codes):
        """Start with the bounds  r <= d_r <= p_m  for every code (q, d, m) in the list `codes`."""
        # The rules use the bounds for m - 1 to obtain those for m, so we treat the codes by
        # increasing m (for each q).
        self.codes = sorted(codes, key=q_then_m_then_d)
        self.lower = {}
        self.upper = {}
        self.lower_reason = {}
        self.upper_reason = {}
        for q, d, m in self.codes:
            k = dim_PRM(q, d, m)
            n = p(q, m)
            self.lower[q, d, m] = list(range(k + 1))              # [0, 1, 2, ..., k]
            self.upper[q, d, m] = [0] + [n] * k                   # [0, n, n, ..., n]
            self.lower_reason[q, d, m] = [None] + [TRIVIAL] * k
            self.upper_reason[q, d, m] = [None] + [TRIVIAL] * k
        # Values computed outside this program, read from data/manual.csv: for each code, the list of
        # its lines, as dictionaries (see generate.py).
        self.computed = {}
        # For the recursive bound: the inputs it used the last time, for each code (see rules.py).
        self.recursive_inputs = {}

    def improve_lower(self, code, r, value, reason):
        """Use  d_r >= value  if it is better than the current lower bound.  (code is the triple (q, d, m).)

        A rule giving the same value as a trivial bound takes its place, so that the tables show the
        actual result (for instance d_r = r for the whole space).  Returns 1 if the table changed
        (a better bound, or a trivial reason replaced) and 0 otherwise.
        """
        current = self.lower[code][r]
        if value > current or (value == current and self.lower_reason[code][r]["rule"] == "trivial"):
            self.lower[code][r] = value
            self.lower_reason[code][r] = reason
            return 1
        return 0

    def improve_upper(self, code, r, value, reason):
        """Use  d_r <= value  if it is better than the current upper bound.  As above, a rule replaces
        a trivial bound with the same value.  Returns 1 if the table changed and 0 otherwise."""
        current = self.upper[code][r]
        if value < current or (value == current and self.upper_reason[code][r]["rule"] == "trivial"):
            self.upper[code][r] = value
            self.upper_reason[code][r] = reason
            return 1
        return 0

    def is_exact(self, code, r):
        """True if the lower and upper bounds for d_r coincide."""
        return self.lower[code][r] == self.upper[code][r]

    def lower_bounds(self, q, d, m):
        """The tuple (0, lower_1, ..., lower_k) of current lower bounds for PRM_q(d, m).

        It also works for the codes outside the tables that the rules may need:
        PRM_q(d, m) = {0} if d <= 0, and PRM_q(d, m) is the whole space if d > m(q-1),
        in which case d_r = r.
        """
        if d <= 0:
            return (0,)
        if d > m * (q - 1):
            return tuple(range(p(q, m) + 1))
        return tuple(self.lower[q, d, m])
