"""
Tests for src/formulas.py.  Run them from the repository folder with

    python3 -m unittest discover -s tests -v

They reproduce the examples and the computational checks of [PRM] (see the docstring of
src/formulas.py for the references).  The checks over many codes use the parameter range of the
tables (src/parameters.py) and take a few seconds.  To use instead the range checked in the last
remark of [PRM] (all prime powers q <= 9 and m <= 5), run

    FULL_CHECK=1 python3 -m unittest discover -s tests -v

which takes about a minute.
"""

import ast
import os
import sys
import unittest
from itertools import product
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

from formulas import (A, B, affine_hierarchy, bdg_hierarchy, binom, ceil_div, digit_sum,  # noqa: E402
                      dim_PRM, dim_RM, h, high_degree_hierarchy, lifted_weights, macaulay, p,
                      sorensen_minimum_distance, trivial_hierarchy, upper_bound_hierarchy)
from parameters import codes  # noqa: E402

PAPER_RANGE = {q: 5 for q in (2, 3, 4, 5, 7, 8, 9)}
CHECKED_CODES = list(codes(PAPER_RANGE) if os.environ.get("FULL_CHECK") else codes())


class TestBasicFunctions(unittest.TestCase):

    def test_ceil_div(self):
        for a, b in product(range(-20, 21), range(1, 8)):
            self.assertEqual(ceil_div(a, b), -((-a) // b))
            self.assertTrue(ceil_div(a, b) * b >= a > (ceil_div(a, b) - 1) * b)

    def test_binom_convention(self):
        """binom(a, b) = 0 unless 0 <= b <= a, as in [PRM] (Sage would give binomial(-2, 5) = -6)."""
        self.assertEqual(binom(5, 2), 10)
        self.assertEqual(binom(2, 5), 0)
        self.assertEqual(binom(-2, 5), 0)
        self.assertEqual(binom(3, -1), 0)
        self.assertEqual(binom(0, 0), 1)

    def test_p(self):
        self.assertEqual(p(3, -1), 0)
        self.assertEqual(p(3, 0), 1)
        self.assertEqual(p(3, 2), 13)
        for q, j in product((2, 3, 4, 5, 7, 8, 9), range(8)):
            self.assertEqual(p(q, j) * (q - 1), q**(j + 1) - 1)

    def test_macaulay(self):
        """The Macaulay tuple satisfies the defining properties of [PRM], eq. (1.2)."""
        for d in range(1, 7):
            self.assertEqual(macaulay(0, d), (-1,) * d)
            for value in range(400):
                mu = macaulay(value, d)
                self.assertEqual(len(mu), d)
                self.assertGreaterEqual(mu[0], -1)
                self.assertTrue(all(mu[i] <= mu[i + 1] for i in range(d - 1)))
                self.assertEqual(sum(binom(mu[i - 1] + i, i) for i in range(1, d + 1)), value)

    def test_A_against_direct_count(self):
        """A(t, D) = #{0 <= i < t : sigma_q(i) <= D}, counted one integer at a time."""
        for q in (2, 3, 4, 5, 7, 8, 9):
            for D in range(-1, 4 * (q - 1) + 2):
                count = 0
                for t in range(min(q**4, 800) + 1):
                    self.assertEqual(A(q, t, D), count)
                    if digit_sum(q, t) <= D:
                        count += 1

    def test_dim_RM(self):
        for q, m in product((2, 3, 4, 5, 7), range(4)):
            for d in range(-1, m * (q - 1) + 2):
                direct = sum(1 for u in product(range(q), repeat=m) if sum(u) <= d)
                self.assertEqual(dim_RM(q, d, m), direct)
                self.assertEqual(dim_RM(q, d, m), A(q, q**m, d))
                if 0 <= d < q:
                    self.assertEqual(dim_RM(q, d, m), binom(m + d, d))


class TestDimensions(unittest.TestCase):

    def test_small_degrees(self):
        """k_d(m) = binom(m + d, d) for 1 <= d < q."""
        for q, d, m in codes():
            if d < q:
                self.assertEqual(dim_PRM(q, d, m), binom(m + d, d))

    def test_recursions(self):
        """k_d(m) = A(q^m, d-1) + k_d(m-1)  and  k_d(m) = A(q^m, d) + k_{d-q+1}(m-1)  ([PRM], Section 6)."""
        for q, d, m in codes():
            k = dim_PRM(q, d, m)
            self.assertEqual(k, A(q, q**m, d - 1) + dim_PRM(q, d, m - 1))
            self.assertEqual(k, A(q, q**m, d) + dim_PRM(q, d - q + 1, m - 1))

    def test_duality_and_large_degrees(self):
        """Sorensen: PRM_q(d,m)^perp = PRM_q(m(q-1)-d, m) if d is not divisible by q-1;
        the code is the whole space for d > m(q-1), and has codimension 1 for d = m(q-1)."""
        for q, d, m in codes():
            n = p(q, m)
            if d > m * (q - 1):
                self.assertEqual(dim_PRM(q, d, m), n)
            elif d == m * (q - 1):
                self.assertEqual(dim_PRM(q, d, m), n - 1)
            elif d % (q - 1) != 0:
                self.assertEqual(dim_PRM(q, d, m) + dim_PRM(q, m * (q - 1) - d, m), n)


class TestPaperExamples(unittest.TestCase):

    def test_example_6_1_and_6_8(self):
        """q=3: h_3(9) = 8 = k_3(2) - 2, so B_2(3,3,2) = 4 = d_2(PRM_3(3,2))."""
        self.assertEqual(dim_PRM(3, 3, 2), 10)
        self.assertEqual(h(3, 3, 9), 8)
        self.assertEqual(B(3, 3, 2, 2), 4)

    def test_example_6_3(self):
        """PRM_3(3,3): minimum distance 9, d_3 = 13, d_4 <= 18."""
        self.assertEqual(B(3, 3, 3, 1), 9)
        self.assertEqual(B(3, 3, 3, 3), 13)
        self.assertLessEqual(B(3, 3, 3, 4), 18)

    def test_example_6_4(self):
        """q=4: H_{Z_6^-}(2) = 5, H_{Z_6^+}(2) = 4, H_{Z_15^-}(4) = 13, H_{Z_15^+}(4) = 14."""
        self.assertEqual(A(4, 6, 2), 5)                                    # Z_6^-  = L_2(6)
        self.assertEqual(dim_PRM(4, 2, 1) + A(4, 6 - p(4, 1), 1), 4)       # Z_6^+  = H u L_2(1)
        self.assertEqual(h(4, 2, 6), 4)
        self.assertEqual(A(4, 15, 4), 13)                                  # Z_15^- = L_2(15)
        self.assertEqual(dim_PRM(4, 4, 1) + A(4, 15 - p(4, 1), 3), 14)     # Z_15^+ = H u L_2(10)
        self.assertEqual(h(4, 4, 15), 13)

    def test_remark_value_d7(self):
        """The value d_7(PRM_3(4,3)) = 16 confirmed with the GHWs package agrees with the bound."""
        self.assertEqual(B(3, 4, 3, 7), 16)


class TestUpperBound(unittest.TestCase):
    """Comparisons between B_r(q, d, m) and the known values, over many codes."""

    def test_whole_projective_space(self):
        """P^m(F_q) imposes k_d(m) conditions: h_d(p_m) = k_d(m)."""
        for q, d, m in CHECKED_CODES:
            self.assertEqual(h(q, d, p(q, m)), dim_PRM(q, d, m), (q, d, m))

    def test_strictly_increasing(self):
        """B_1 < B_2 < ... < B_k = p_m, as for any weight hierarchy (necessary for Conjecture 6.9)."""
        for q, d, m in CHECKED_CODES:
            H = upper_bound_hierarchy(q, d, m)
            self.assertEqual(len(H), dim_PRM(q, d, m))
            self.assertTrue(all(H[i] < H[i + 1] for i in range(len(H) - 1)), (q, d, m))
            self.assertEqual(H[-1], p(q, m), (q, d, m))

    def test_theorem_1_1(self):
        """Thm 6.7: B_r(q, d, m) is the formula of Thm 1.1 when d < q."""
        for q, d, m in CHECKED_CODES:
            if d < q:
                self.assertEqual(upper_bound_hierarchy(q, d, m), bdg_hierarchy(q, d, m), (q, d, m))

    def test_sorensen(self):
        """B_1(q, d, m) is Sorensen's minimum distance."""
        for q, d, m in CHECKED_CODES:
            self.assertEqual(B(q, d, m, 1), sorensen_minimum_distance(q, d, m), (q, d, m))

    def test_corollary_4_2(self):
        for q, d, m in CHECKED_CODES:
            if (m - 1) * (q - 1) < d < m * (q - 1):
                self.assertEqual(upper_bound_hierarchy(q, d, m), high_degree_hierarchy(q, d, m), (q, d, m))

    def test_large_degrees(self):
        for q, d, m in CHECKED_CODES:
            if d >= m * (q - 1):
                self.assertEqual(upper_bound_hierarchy(q, d, m), trivial_hierarchy(q, d, m), (q, d, m))

    def test_proposition_6_12(self):
        for q, d, m in CHECKED_CODES:
            for r, value in lifted_weights(q, d, m).items():
                self.assertEqual(B(q, d, m, r), value, (q, d, m, r))

    def test_lemma_6_10(self):
        """B_r(q, e + t(q-1), m) = B_r(q, e, m - t) for 1 <= r <= k_e(m - t)."""
        for q, d, m in CHECKED_CODES:
            for t in range(1, m):
                e = d - t * (q - 1)
                if e >= 1:
                    H_low = upper_bound_hierarchy(q, e, m - t)
                    self.assertEqual(upper_bound_hierarchy(q, d, m)[:len(H_low)], H_low, (q, d, m, t))


class TestAffine(unittest.TestCase):
    """The Heijnen-Pellikaan weights of the affine codes RM_q(d, m) ([SJ24, Thm 5.4])."""

    AFFINE = [(q, d, m) for q, top in ((2, 9), (3, 6), (4, 4), (5, 4), (7, 3), (8, 3), (9, 3))
              for m in range(1, top + 1) for d in range(0, m * (q - 1) + 1)]

    def test_length_is_dimension(self):
        for q, d, m in self.AFFINE:
            self.assertEqual(len(affine_hierarchy(q, d, m)), dim_RM(q, d, m))

    def test_minimum_distance(self):
        """d_1(RM_q(d, m)) = (q - b) q^(m-a-1) for d = a(q-1) + b, 0 <= b < q-1, d < m(q-1)."""
        for q, d, m in self.AFFINE:
            if d < m * (q - 1):
                a, b = divmod(d, q - 1)
                self.assertEqual(affine_hierarchy(q, d, m)[0], (q - b) * q**(m - a - 1), (q, d, m))

    def test_against_A(self):
        """Second description: d_r(RM_q(d, m)) = q^m - max{t : A(t, d) <= dim RM_q(d, m) - r}."""
        for q, d, m in self.AFFINE:
            k = dim_RM(q, d, m)
            largest = [0] * (k + 1)              # largest[v] = max{t <= q^m : A(t, d) = v}
            for t in range(q**m + 1):
                largest[A(q, t, d)] = t
            expected = tuple(q**m - largest[k - r] for r in range(1, k + 1))
            self.assertEqual(affine_hierarchy(q, d, m), expected, (q, d, m))

    def test_corollary_5_2(self):
        """[PRM] Cor 5.2: for d < q, the weights of PRM_q(d, m) are those of RM_q(d-1, m),
        followed by q^m + (the weights of PRM_q(d, m-1))."""
        for q, d, m in codes():
            if d < q:
                first = affine_hierarchy(q, d - 1, m)
                rest = tuple(q**m + w for w in bdg_hierarchy(q, d, m - 1))
                self.assertEqual(bdg_hierarchy(q, d, m), first + rest, (q, d, m))


class TestCodeStyle(unittest.TestCase):

    def test_no_division_or_xor(self):
        """In Python, "/" gives decimal numbers and "^" is XOR: neither may appear in src/."""
        for path in sorted(SRC.glob("*.py")):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, (ast.BinOp, ast.AugAssign)) and isinstance(node.op, (ast.Div, ast.BitXor)):
                    self.fail(f'{path.name}, line {node.lineno}: use // or ceil_div instead of "/", '
                              f'and ** instead of "^"')


if __name__ == "__main__":
    unittest.main()
