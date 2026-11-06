"""
Tests for src/formulas.py.  Run them from the repository folder with

    python3 -m unittest discover -s tests -v

They reproduce the examples and the computational checks of [SJ26] (see the docstring of
src/formulas.py for the references).  The checks over many codes use the parameter range of the
tables (src/parameters.py) and take a few seconds.  To use instead the range checked in the last
remark of [SJ26] (all prime powers q <= 9 and m <= 5), run

    FULL_CHECK=1 python3 -m unittest discover -s tests -v

which takes about a minute.
"""

import ast
import os
import random
import sys
import unittest
from itertools import product
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent.joinpath("src")
sys.path.insert(0, str(SRC))

from formulas import (A, B, affine_hierarchy, attaining_set, bdg_hierarchy, binom,  # noqa: E402
                      bounds_after_adding_a_vector, digit_sum,
                      dim_PRM, dim_RM, dual_degree, h, high_degree_hierarchy, known_hierarchy,
                      large_degree_hierarchy, lifted_weights, macaulay, p, recursive_lower_bound,
                      sorensen_minimum_distance, upper_bound_hierarchy, wei_duality_bounds)
from parameters import codes  # noqa: E402

PAPER_RANGE = {q: 5 for q in (2, 3, 4, 5, 7, 8, 9)}
CHECKED_CODES = list(codes(PAPER_RANGE) if os.environ.get("FULL_CHECK") else codes())


class TestBasicFunctions(unittest.TestCase):

    def test_binom_convention(self):
        """binom(a, b) = 0 unless 0 <= b <= a, as in [SJ26] (Sage gives binomial(-2, 5) = -6)."""
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
        """The Macaulay tuple satisfies the defining properties of [SJ26], eq. (1.2)."""
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
        """k_d(m) = A(q^m, d-1) + k_d(m-1)  and  k_d(m) = A(q^m, d) + k_{d-q+1}(m-1)  ([SJ26], Section 6)."""
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
        """0 = B_0 < B_1 < B_2 < ... < B_k = p_m, as for any weight hierarchy (necessary for Conj. 6.9)."""
        for q, d, m in CHECKED_CODES:
            H = upper_bound_hierarchy(q, d, m)
            self.assertEqual(len(H), dim_PRM(q, d, m) + 1)
            self.assertEqual(H[0], 0)
            self.assertTrue(all(H[r] < H[r + 1] for r in range(len(H) - 1)), (q, d, m))
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
                self.assertEqual(upper_bound_hierarchy(q, d, m), large_degree_hierarchy(q, d, m), (q, d, m))

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
    """The weights of the affine codes RM_q(d, m): Heijnen-Pellikaan [HP98, Thm 5.10], in the form of [SJ24, Thm 6]."""

    AFFINE = [(q, d, m) for q, top in ((2, 9), (3, 6), (4, 4), (5, 4), (7, 3), (8, 3), (9, 3))
              for m in range(1, top + 1) for d in range(0, m * (q - 1) + 1)]

    def test_length_is_dimension(self):
        for q, d, m in self.AFFINE:
            self.assertEqual(len(affine_hierarchy(q, d, m)), dim_RM(q, d, m) + 1)

    def test_minimum_distance(self):
        """d_1(RM_q(d, m)) = (q - b) q^(m-a-1) for d = a(q-1) + b, 0 <= b < q-1, d < m(q-1)."""
        for q, d, m in self.AFFINE:
            if d < m * (q - 1):
                a = d // (q - 1)
                b = d % (q - 1)
                self.assertEqual(affine_hierarchy(q, d, m)[1], (q - b) * q**(m - a - 1), (q, d, m))

    def test_against_A(self):
        """A cross-check of affine_hierarchy ([SJ24, Thm 6]) with the counting function A:
        d_r(RM_q(d, m)) = q^m - max{t : A(t, d) <= dim RM_q(d, m) - r}, the affine analogue of B_r."""
        for q, d, m in self.AFFINE:
            k = dim_RM(q, d, m)
            # A(t+1, d) - A(t, d) is 0 or 1, with A(0, d) = 0 and A(q^m, d) = k, so every v = 0, ..., k
            # is attained, and max{t : A(t, d) = v} = max{t : A(t, d) <= v}.
            largest = [0] * (k + 1)              # largest[v] = max{t <= q^m : A(t, d) <= v}
            for t in range(q**m + 1):
                largest[A(q, t, d)] = t
            expected = (0,) + tuple(q**m - largest[k - r] for r in range(1, k + 1))
            self.assertEqual(affine_hierarchy(q, d, m), expected, (q, d, m))

    def test_corollary_5_2(self):
        """[SJ26] Cor 5.2: for d < q, the weights of PRM_q(d, m) are those of RM_q(d-1, m),
        followed by q^m + (the weights of PRM_q(d, m-1))."""
        for q, d, m in codes():
            if d < q:
                first = affine_hierarchy(q, d - 1, m)
                rest = tuple(q**m + w for w in bdg_hierarchy(q, d, m - 1)[1:])
                self.assertEqual(bdg_hierarchy(q, d, m), first + rest, (q, d, m))


class TestHelpers(unittest.TestCase):

    def test_known_hierarchy(self):
        """The complete hierarchy is known for m <= 2, and it is the bound B_r there."""
        for q, d, m in codes():
            H, result = known_hierarchy(q, d, m)
            if m <= 2:
                self.assertIsNotNone(H, (q, d, m))
            if H is not None:
                self.assertEqual(H, upper_bound_hierarchy(q, d, m), (q, d, m))
        for d in (0, -1, -5):
            self.assertEqual(known_hierarchy(3, d, 2), (None, None))

    def test_attaining_set(self):
        """Example 6.4 (q=4): Z_6^+ gives h_2(6), Z_15^- gives h_4(15); Z_9^- = Z_9^+ (q=4, d=2)."""
        self.assertEqual(attaining_set(4, 2, 6), "+")
        self.assertEqual(attaining_set(4, 4, 15), "-")
        self.assertEqual(attaining_set(4, 2, 9), "-+")


# Entries "a-b" of [SJ24, Tables II-V]: a is the value of [SJ24, Thm 7], and b is the best upper bound
# used in [SJ24] (Lemma 1 and monotonicity).  [SJ24] writes a range when Thm 7 is not sharp OR when the
# true value was not known (see the text after the tables), so a may be the true value: for instance
# d_2(PRM_3(3,2)) = 4 [SJ24, p. 8522] and d_3(PRM_3(3,3)) = 13 [SJ24, Example 6].  At all the other
# entries with r >= 2, the paper states that Thm 7 gives the true value.  Only a is tested here.
# Keys: (q, m) -> {(d, r): a}.
SJ24_TABLE_RANGES = {
    (3, 2): {(3, 2): 4},                                                              # Table II
    (4, 2): {(3, 2): 10, (3, 3): 11, (4, 2): 5, (4, 4): 9, (4, 5): 10, (5, 3): 5},    # Table IV
    (5, 2): {(3, 2): 18, (3, 3): 19, (4, 2): 12, (4, 3): 13, (4, 4): 17, (4, 5): 18,  # Table V
             (4, 6): 19, (5, 2): 6, (5, 4): 11, (5, 5): 12, (5, 7): 16, (5, 8): 17,
             (5, 9): 18, (6, 3): 6, (6, 6): 11, (6, 7): 12, (7, 4): 6},
    (3, 3): {(2, 2): 23, (2, 5): 32, (2, 6): 35, (2, 7): 36, (3, 3): 13, (3, 6): 22,  # Table III
             (3, 11): 30, (3, 12): 31, (4, 4): 11, (4, 5): 12, (4, 6): 13, (4, 7): 15,
             (5, 2): 4, (5, 7): 10, (5, 8): 11, (5, 9): 12, (5, 10): 13},
}


def thm7_with_exact_inputs(q, d, m, r):
    """[SJ24, Thm 7] for d_r(PRM_q(d, m)), using the exact hierarchies of the two smaller codes
    (they are known for m - 1 <= 2).  For d - q + 1 <= 0, PRM_q(d-q+1, m-1) = {0}, as in [SJ24]."""
    PRM_d = known_hierarchy(q, d, m - 1)[0]
    PRM_d_minus_q_plus_1 = known_hierarchy(q, d - q + 1, m - 1)[0] if d - q + 1 >= 1 else (0,)
    return recursive_lower_bound(q, d, m, r, PRM_d, PRM_d_minus_q_plus_1)


class TestRecursiveBound(unittest.TestCase):
    """The lower bound of [SJ24, Thm 7], compared with the examples and tables of [SJ24]."""

    def test_examples(self):
        self.assertEqual(thm7_with_exact_inputs(4, 5, 2, 2)[0], 4)     # Example 2
        self.assertEqual(thm7_with_exact_inputs(4, 3, 2, 2)[0], 10)    # Example 3 (the true value is 11)
        self.assertEqual(B(4, 3, 2, 2), 11)
        self.assertEqual(thm7_with_exact_inputs(3, 1, 2, 2)[0], 12)    # Example 4
        self.assertEqual(thm7_with_exact_inputs(3, 3, 3, 2)[0], 12)    # Example 4
        self.assertEqual(thm7_with_exact_inputs(4, 5, 2, 5)[0], 8)     # Example 5

    def test_tables(self):
        """[SJ24, Tables II, III, IV, V].  The true values are the exact hierarchies for m = 2, and
        B_r for q = 3, m = 3 (where [SJ26] verified Conj. 6.9)."""
        for (q, m), ranges in SJ24_TABLE_RANGES.items():
            for d in range(1, m * (q - 1) + 1):
                true_values = upper_bound_hierarchy(q, d, m)
                for r in range(2, dim_PRM(q, d, m) + 1):
                    expected = ranges.get((d, r), true_values[r])
                    self.assertEqual(thm7_with_exact_inputs(q, d, m, r)[0], expected, (q, d, m, r))

    def test_bound_is_attained_in_Y(self):
        """The returned pair (alpha, gamma) satisfies the conditions defining Y in [SJ24, Thm 7]."""
        for q, d, m in [(3, 3, 3), (3, 4, 3), (4, 5, 3), (2, 2, 3)]:
            for r in range(2, dim_PRM(q, d, m) + 1):
                bound, alpha, gamma = thm7_with_exact_inputs(q, d, m, r)
                self.assertTrue(max(r - dim_RM(q, d - 1, m), 0) <= alpha <= min(dim_PRM(q, d, m - 1), r))
                self.assertTrue(max(r - dim_RM(q, d, m), 0) <= gamma <= min(dim_PRM(q, d - q + 1, m - 1), alpha))
                self.assertLessEqual(bound, B(q, d, m, r))


def rank(vectors, q):
    """The rank over GF(q), q prime, of a list of vectors (lists of integers modulo q)."""
    rows = [list(vector) for vector in vectors]
    rank = 0
    for column in range(len(rows[0]) if rows else 0):
        pivot = next((i for i in range(rank, len(rows)) if rows[i][column] % q), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        inverse = pow(rows[rank][column], q - 2, q)               # 1/a = a^(q-2) in GF(q)
        rows[rank] = [x * inverse % q for x in rows[rank]]
        for i in range(len(rows)):
            if i != rank and rows[i][column] % q:
                factor = rows[i][column]
                rows[i] = [(x - factor * y) % q for x, y in zip(rows[i], rows[rank])]
        rank += 1
    return rank


def brute_force_hierarchy(G, q):
    """The weight hierarchy (0, d_1, ..., d_k) of the code over GF(q), q prime, with generator matrix G
    (k linearly independent rows of length n), by brute force over the sets S of coordinates: the
    codewords vanishing on S form a subcode of dimension k - rank(G_S), where G_S are the columns of G
    in S, and it is supported outside S.  Hence  d_r = n - max{ |S| : rank(G_S) <= k - r }."""
    k, n = len(G), len(G[0])
    largest = [-1] * (k + 1)               # largest[j] = max{ |S| : rank(G_S) <= j }
    for S in product([False, True], repeat=n):
        columns = [i for i in range(n) if S[i]]
        j = rank([[row[i] for i in columns] for row in G], q) if columns else 0
        largest[j] = max(largest[j], len(columns))
    for j in range(1, k + 1):
        largest[j] = max(largest[j], largest[j - 1])
    return [0] + [n - largest[k - r] for r in range(1, k + 1)]


def random_code(generator, q, n, k):
    """A random generator matrix over GF(q), q prime, with k linearly independent rows of length n."""
    while True:
        G = [[generator.randrange(q) for i in range(n)] for j in range(k)]
        if rank(G, q) == k:
            return G


def dual_code(G, q):
    """A generator matrix of the dual of the code generated by G, over GF(q), q prime: a basis of
    the vectors x with  G x = 0, found by bringing G to reduced row echelon form."""
    k, n = len(G), len(G[0])
    rows = [list(row) for row in G]
    pivots = []
    for column in range(n):
        pivot = next((i for i in range(len(pivots), k) if rows[i][column] % q), None)
        if pivot is None:
            continue
        top = len(pivots)
        rows[top], rows[pivot] = rows[pivot], rows[top]
        inverse = pow(rows[top][column], q - 2, q)
        rows[top] = [x * inverse % q for x in rows[top]]
        for i in range(k):
            if i != top and rows[i][column] % q:
                factor = rows[i][column]
                rows[i] = [(x - factor * y) % q for x, y in zip(rows[i], rows[top])]
        pivots.append(column)
    basis = []
    for free in range(n):                  # one dual vector for each non-pivot column
        if free in pivots:
            continue
        x = [0] * n
        x[free] = 1
        for i, column in enumerate(pivots):
            x[column] = -rows[i][free] % q
        basis.append(x)
    return basis


class TestBruteForce(unittest.TestCase):
    """The brute-force hierarchies used to check the bounds below."""

    def test_brute_force_satisfies_wei_duality(self):
        """For random codes over GF(2), GF(3) and GF(5), the brute-force hierarchies of a code and of its
        dual satisfy Wei duality [Wei91, Thm 3], and the dual has the right dimension."""
        generator = random.Random(2026)
        for trial in range(60):
            q = generator.choice([2, 3, 5])
            n = generator.randint(2, 7 if q == 2 else 6)
            k = generator.randint(1, n - 1)
            G = random_code(generator, q, n, k)
            H = dual_code(G, q)
            self.assertEqual(len(H), n - k)
            self.assertTrue(all(sum(a * b for a, b in zip(g, h)) % q == 0 for g in G for h in H))
            weights = set(brute_force_hierarchy(G, q)[1:])
            dual_weights = set(brute_force_hierarchy(H, q)[1:])
            self.assertEqual(weights | {n + 1 - w for w in dual_weights}, set(range(1, n + 1)))
            self.assertEqual(len(weights) + len(dual_weights), n)


class TestDuality(unittest.TestCase):
    """Wei duality applied to bounds ([SJ24, Thm 9 and Section V-C])."""

    def test_dual_degree(self):
        """For 1 <= d <= m(q-1)-1 the dual is PRM_q(e, m), e = m(q-1)-d, plus the all-ones vector if q-1
        divides d: the dimensions add up to p_m, or to p_m - 1."""
        for q, d, m in codes():
            e = dual_degree(q, d, m)
            if d >= m * (q - 1):
                self.assertIsNone(e, (q, d, m))
                continue
            self.assertEqual(e, m * (q - 1) - d)
            self.assertEqual(dual_degree(q, e, m), d)
            plus_ones = 1 if d % (q - 1) == 0 else 0
            self.assertEqual(dim_PRM(q, d, m) + dim_PRM(q, e, m) + plus_ones, p(q, m), (q, d, m))

    def test_bounds_after_adding_a_vector(self):
        """d_{s-1}(D) <= d_s(D + <v>) <= d_s(D), checked by brute force for random codes D over GF(2) and
        GF(3) (the last row of the random matrix is v)."""
        generator = random.Random(2026)
        for trial in range(40):
            q = generator.choice([2, 3])
            n = 7 if q == 2 else 6
            G = random_code(generator, q, n, generator.randint(2, 4))
            D, extended = brute_force_hierarchy(G[:-1], q), brute_force_hierarchy(G, q)
            lower, upper = bounds_after_adding_a_vector(n, D, D)
            for s in range(1, len(G) + 1):
                self.assertTrue(lower[s] <= extended[s] <= upper[s], (G, s))

    def test_exact_dual_gives_exact_hierarchy(self):
        """If the dual hierarchy is known exactly, so is the hierarchy of the code (Wei duality)."""
        for q, d, m in codes():
            e = dual_degree(q, d, m)
            if e is None or d % (q - 1) == 0:          # we need the dual to be exactly PRM_q(e, m)
                continue
            if known_hierarchy(q, d, m)[0] is None or known_hierarchy(q, e, m)[0] is None:
                continue
            dual = known_hierarchy(q, e, m)[0]
            lower, upper = wei_duality_bounds(p(q, m), dim_PRM(q, d, m), dual, dual)
            expected = list(known_hierarchy(q, d, m)[0][1:])
            self.assertEqual([lower[r][0] for r in range(1, len(lower))], expected, (q, d, m))
            self.assertEqual([upper[r][0] for r in range(1, len(upper))], expected, (q, d, m))

    def test_bounds_contain_the_true_values(self):
        """Random intervals around the true weights of PRM_q(e, m) give intervals around the true weights
        of PRM_q(d, m), also when the dual is PRM_q(e, m) + <(1, ..., 1)> (here, when d = e = q-1, m = 2)."""
        generator = random.Random(2026)
        for q, d, m in codes():
            e = dual_degree(q, d, m)
            if e is None or known_hierarchy(q, d, m)[0] is None or known_hierarchy(q, e, m)[0] is None:
                continue
            n, true, dual = p(q, m), known_hierarchy(q, d, m)[0], known_hierarchy(q, e, m)[0]
            for trial in range(5):
                dual_lower = [0] + [generator.randint(s, dual[s]) for s in range(1, len(dual))]
                dual_upper = [0] + [generator.randint(dual[s], n) for s in range(1, len(dual))]
                if d % (q - 1) == 0:
                    dual_lower, dual_upper = bounds_after_adding_a_vector(n, dual_lower, dual_upper)
                lower, upper = wei_duality_bounds(n, dim_PRM(q, d, m), dual_lower, dual_upper)
                for r in range(1, len(true)):
                    self.assertTrue(lower[r][0] <= true[r] <= upper[r][0], (q, d, m, r, trial))

    def test_SJ24_example_6(self):
        """[SJ24, Example 6]: for the self-dual code PRM_3(3,3), duality and monotonicity turn the bounds of
        [SJ24, Table III] (row d = 3) into the exact values of [SJ24, Table VI]."""
        lower = [0, 9, 12, 13, 18, 21, 22, 24, 25, 26, 27, 30, 31, 33, 34, 35, 36, 37, 38, 39, 40]
        upper = [0, 9, 12, 17, 18, 21, 23, 24, 25, 26, 27, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]
        table_VI = [0, 9, 12, 13, 18, 21, 22, 24, 25, 26, 27, 30, 31, 33, 34, 35, 36, 37, 38, 39, 40]
        self.assertEqual(dual_degree(3, 3, 3), 3)
        for step in range(10):
            new_lower, new_upper = wei_duality_bounds(40, 20, lower, upper)
            new_lower = [0] + [max(lower[r], new_lower[r][0]) for r in range(1, 21)]
            new_upper = [0] + [min(upper[r], new_upper[r][0]) for r in range(1, 21)]
            for r in range(2, 21):                       # monotonicity, [SJ24, Thm 5]
                new_lower[r] = max(new_lower[r], new_lower[r - 1] + 1)
            for r in range(19, 0, -1):
                new_upper[r] = min(new_upper[r], new_upper[r + 1] - 1)
            if (new_lower, new_upper) == (lower, upper):
                break
            lower, upper = new_lower, new_upper
        self.assertEqual(lower, table_VI)
        self.assertEqual(upper, table_VI)


class TestCodeStyle(unittest.TestCase):

    def test_no_division_or_xor(self):
        """In Python, "/" gives decimal numbers and "^" is XOR: neither may appear in src/."""
        for path in sorted(SRC.glob("*.py")):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, (ast.BinOp, ast.AugAssign)) and isinstance(node.op, (ast.Div, ast.BitXor)):
                    self.fail(f'{path.name}, line {node.lineno}: use // instead of "/", and ** instead of "^"')


if __name__ == "__main__":
    unittest.main()
