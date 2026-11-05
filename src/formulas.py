"""
Exact formulas and upper bounds for the generalized Hamming weights of
projective Reed-Muller codes PRM_q(d, m).

Each function implements one formula, with the notation of the papers:

  [PRM]   R. San-Jose, Common zeros of homogeneous polynomials and the weight
          hierarchy of projective Reed-Muller codes (preprint, 2026).
  [SJ24]  R. San-Jose, A recursive construction for projective Reed-Muller
          codes, IEEE Trans. Inform. Theory 70(12) (2024), 8511-8523.
          Its theorem numbers here follow the arXiv version, arXiv:2312.05072v2.

Conventions used in all files of this project:

  * Python integers are exact and unbounded, so all computations are exact.
  * We never use "/" (in Python it produces decimal numbers) nor "^" (in
    Python it is the bitwise XOR, not a power).  We write q**j for powers,
    a // b for the floor of a/b and ceil_div(a, b) for the ceiling of a/b.
    The test suite checks that "/" and "^" do not appear in the code.
  * A weight hierarchy is a tuple (d_1, d_2, ..., d_k).  Python counts
    positions from 0, so d_r is hierarchy[r - 1].
  * The field size q always comes first in the arguments.

To use these functions from Sage, start Sage in the repository folder and run
load("src/formulas.py").  Sage does not preparse .py files, so the code runs
exactly as written here.
"""

from functools import cache
from math import comb


# ---------------------------------------------------------------------------
# Basic integer functions
# ---------------------------------------------------------------------------

def ceil_div(a, b):
    """The ceiling of a/b, for integers a and b > 0."""
    return -((-a) // b)


def binom(a, b):
    """Binomial coefficient with the convention of [PRM]: it is 0 unless 0 <= b <= a."""
    if b < 0 or a < b:
        return 0
    return comb(a, b)


def p(q, j):
    """p_j = 1 + q + ... + q^j for j >= 0, and p_j = 0 for j < 0.

    p_m is the number of points of the projective space P^m(F_q), i.e. the length of PRM_q(d, m).
    """
    return sum(q**i for i in range(j + 1))


def floor_q_power(q, mu):
    """floor(q^mu) for an integer mu >= -1: it is q^mu if mu >= 0, and 0 if mu = -1."""
    return q**mu if mu >= 0 else 0


def digit_sum(q, i):
    """sigma_q(i): the sum of the digits of i in base q."""
    s = 0
    while i > 0:
        s += i % q
        i //= q
    return s


def leading_term(q, n):
    """For n >= 1, write n = a q^s + b with 1 <= a <= q-1 and 0 <= b < q^s ([PRM], eq. (6.1)).

    Returns (a, s, b).
    """
    s = 0
    while q**(s + 1) <= n:
        s += 1
    a, b = divmod(n, q**s)
    return a, s, b


def macaulay(h, d):
    """The Macaulay tuple (mu_1, ..., mu_d) of an integer h >= 0 in degree d ([PRM], eq. (1.2)).

    It is the unique tuple with -1 <= mu_1 <= ... <= mu_d such that
        h = binom(mu_1 + 1, 1) + binom(mu_2 + 2, 2) + ... + binom(mu_d + d, d).
    We find nu_i = mu_i + i greedily, starting with i = d: nu_i is the largest
    integer with binom(nu_i, i) <= (what is left of h).
    """
    mu = [0] * d                     # mu[i - 1] will be mu_i
    for i in range(d, 0, -1):        # i = d, d-1, ..., 1
        nu = i - 1                   # binom(i - 1, i) = 0, which is always <= h
        while binom(nu + 1, i) <= h:
            nu += 1
        mu[i - 1] = nu - i
        h -= binom(nu, i)
    return tuple(mu)


# ---------------------------------------------------------------------------
# Dimensions and the counting function A(t, D)
# ---------------------------------------------------------------------------

@cache
def dim_RM(q, d, m):
    """dim RM_q(d, m): the number of tuples u in {0, ..., q-1}^m with u_1 + ... + u_m <= d.

    We choose the last coordinate c = u_m and count the possibilities for the others.
    (@cache makes Python remember the results, since this function is called very often.)
    """
    if d < 0:
        return 0
    if m == 0:
        return 1
    return sum(dim_RM(q, d - c, m - 1) for c in range(q))


def A(q, t, D):
    """A(t, D) = #{0 <= i < t : sigma_q(i) <= D}  ([PRM], Section 6.2).

    Write t = a q^s + b.  The integers i < a q^s are i = c q^s + j with c < a and
    j < q^s, and sigma_q(i) = c + sigma_q(j); for each c they contribute
    dim RM_q(D - c, s).  The integers a q^s <= i < t are i = a q^s + j with j < b.
    """
    if t == 0 or D < 0:
        return 0
    a, s, b = leading_term(q, t)
    return sum(dim_RM(q, D - c, s) for c in range(a)) + A(q, b, D - a)


def dim_PRM(q, d, m):
    """k_d(m) = dim PRM_q(d, m) = A(1, d-1) + A(q, d-1) + ... + A(q^m, d-1)  ([SJ24, Cor. 3.3], [PRM] Section 6.2).

    Note that A(q^j, d-1) = dim RM_q(d-1, j).  As in [SJ24], PRM_q(d, m) = {0} for d <= 0.
    """
    if d <= 0:
        return 0
    return sum(dim_RM(q, d - 1, j) for j in range(m + 1))


# ---------------------------------------------------------------------------
# The upper bound B_r(q, d, m) of [PRM, Thm 6.7]
# ---------------------------------------------------------------------------

def h(q, d, n):
    """h_d(n) = min{ H_{Z_n^-}(d), H_{Z_n^+}(d) }, by the recursion of [PRM, Prop. 6.6].

    Write n = a q^s + b.  If b <= p_{s-1}:  h_d(n) = A(a q^s, d) + h_{d-q+1}(b).
    If b > p_{s-1}:  h_d(n) = min{ A(n, d), k_d(s) + A(n - p_s, d - 1) }.
    As in [PRM], h_D(t) = 0 if D <= 0.  Also h_d(0) = 0 (the empty set imposes no conditions).
    """
    if d <= 0 or n == 0:
        return 0
    a, s, b = leading_term(q, n)
    if b <= p(q, s - 1):
        return A(q, a * q**s, d) + h(q, d - q + 1, b)
    return min(A(q, n, d), dim_PRM(q, d, s) + A(q, n - p(q, s), d - 1))


def largest_point_sets(q, d, m):
    """The list L with L[v] = max{ 0 <= n <= p_m : h_d(n) <= v }, for v = 0, 1, ..., k_d(m)."""
    k = dim_PRM(q, d, m)
    L = [0] * (k + 1)
    for n in range(p(q, m) + 1):
        L[h(q, d, n)] = n                # n increases, so L[v] is the largest n with h_d(n) = v
    for v in range(1, k + 1):            # from "h_d(n) = v" to "h_d(n) <= v"
        L[v] = max(L[v], L[v - 1])
    return L


@cache
def upper_bound_hierarchy(q, d, m):
    """(B_1, ..., B_k), where k = k_d(m) and  ([PRM], Thm 6.7)

        B_r(q, d, m) = p_m - max{ 0 <= n <= p_m : h_d(n) <= k_d(m) - r }.

    It is an upper bound for d_r(PRM_q(d, m)) for every d >= 1, with equality if d < q,
    and Conjecture 6.9 of [PRM] says that equality always holds.
    """
    k = dim_PRM(q, d, m)
    L = largest_point_sets(q, d, m)
    return tuple(p(q, m) - L[k - r] for r in range(1, k + 1))


def B(q, d, m, r):
    """B_r(q, d, m) of [PRM, Thm 6.7], for 1 <= r <= k_d(m)."""
    return upper_bound_hierarchy(q, d, m)[r - 1]


# ---------------------------------------------------------------------------
# Exact values
# ---------------------------------------------------------------------------

def bdg_weight(q, d, m, r):
    """d_r(PRM_q(d, m)) for 1 <= d < q and 1 <= r <= binom(m + d, d)  ([PRM], Thm 1.1).

    With (mu_1, ..., mu_d) the Macaulay tuple of binom(m + d, d) - r,
        d_r = p_m - p_{mu_d} - (floor(q^mu_1) + ... + floor(q^mu_{d-1})).
    """
    mu = macaulay(binom(m + d, d) - r, d)
    zeros = p(q, mu[d - 1]) + sum(floor_q_power(q, mu[i]) for i in range(d - 1))
    return p(q, m) - zeros


def bdg_hierarchy(q, d, m):
    """The weight hierarchy of PRM_q(d, m) for 1 <= d < q  ([PRM], Thm 1.1)."""
    return tuple(bdg_weight(q, d, m, r) for r in range(1, binom(m + d, d) + 1))


def sorensen_minimum_distance(q, d, m):
    """d_1(PRM_q(d, m)) for d >= 1 (Sorensen 1991).

    If d <= m(q-1), write d - 1 = a(q-1) + b with 0 <= b < q-1; then d_1 = (q - b) q^(m-a-1).
    If d > m(q-1), the code is the whole space and d_1 = 1.
    """
    if d > m * (q - 1):
        return 1
    a, b = divmod(d - 1, q - 1)
    return (q - b) * q**(m - a - 1)


def wei_dual(dual_hierarchy, n):
    """Wei duality [Wei 1991]: the weight hierarchy of a code C of length n, given that of its dual.

    The weights of C are the integers in {1, ..., n} that are not of the form
    n + 1 - d_s(C^perp).
    """
    excluded = {n + 1 - x for x in dual_hierarchy}
    return tuple(w for w in range(1, n + 1) if w not in excluded)


def high_degree_hierarchy(q, d, m):
    """The weight hierarchy of PRM_q(d, m) for (m-1)(q-1) < d < m(q-1)  ([PRM], Cor. 4.2).

    Here PRM_q(d, m)^perp = PRM_q(e, m) with e = m(q-1) - d < q-1 (Sorensen), whose weights are
    given by Thm 1.1, and we apply Wei duality.
    """
    e = m * (q - 1) - d
    return wei_dual(bdg_hierarchy(q, e, m), p(q, m))


def trivial_hierarchy(q, d, m):
    """The weight hierarchy of PRM_q(d, m) for d >= m(q-1).

    If d > m(q-1), the code is the whole space F_q^{p_m}, so d_r = r.
    If d = m(q-1), the dual code is spanned by the all-ones vector (Sorensen), whose only weight is
    p_m, and Wei duality gives d_r = r + 1.
    """
    n = p(q, m)
    if d > m * (q - 1):
        return tuple(range(1, n + 1))
    return wei_dual((n,), n)


def lifted_weights(q, d, m):
    """The weights given by [PRM, Prop. 6.12], as a dictionary {r: d_r}.  Empty if it does not apply.

    Let 0 <= t <= m-1 and h = m - t.
      (a) If d = 1 + t(q-1):              d_r = q^h + q^(h-1) + ... + q^(h-r+1)  for 1 <= r <= h+1.
      (b) If q >= 3 and d = 2 + t(q-1):   d_r = q^h - q^(h-r) for 1 <= r <= h,  and d_(h+1) = q^h.
    """
    for t in range(m):
        h_ = m - t                       # the paper's h (the name h is taken by the function h_d(n))
        if d == 1 + t * (q - 1):
            return {r: p(q, h_) - p(q, h_ - r) for r in range(1, h_ + 2)}
        if q >= 3 and d == 2 + t * (q - 1):
            weights = {r: q**h_ - q**(h_ - r) for r in range(1, h_ + 1)}
            weights[h_ + 1] = q**h_
            return weights
    return {}


# ---------------------------------------------------------------------------
# Affine Reed-Muller codes (needed by the recursive lower bound of [SJ24])
# ---------------------------------------------------------------------------

@cache
def affine_hierarchy(q, d, m):
    """The weight hierarchy of the affine Reed-Muller code RM_q(d, m), d >= 0.

    Heijnen-Pellikaan, in the form of [SJ24, Thm 5.4]: d_r - 1 is the r-th smallest integer
    i in [0, q^m) whose base-q digit sum is larger than m(q-1) - d - 1.
    (The base-q digits of i, read from the most significant one, are the tuple beta of [SJ24],
    and the lexicographic order of the tuples is the usual order of the integers.)
    """
    if d < 0:
        return ()
    return tuple(i + 1 for i in range(q**m) if digit_sum(q, i) > m * (q - 1) - d - 1)
