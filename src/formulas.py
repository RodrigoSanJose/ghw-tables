"""
Formulas and bounds for the generalized Hamming weights of projective Reed-Muller codes PRM_q(d, m).

Each function implements one formula, with the notation of the papers:

  [PRM]   R. San-Jose, Common zeros of homogeneous polynomials and the weight hierarchy of
          projective Reed-Muller codes (preprint, 2026).
  [SJ24]  R. San-Jose, A recursive construction for projective Reed-Muller codes,
          IEEE Trans. Inform. Theory 70(12) (2024), 8511-8523.

How to read this file:

  * A weight hierarchy is stored as a tuple H = (0, d_1, d_2, ..., d_k), so that H[r] is d_r.
    Position 0 holds d_0 = 0, the convention of [SJ24].  Hence len(H) = k + 1.
  * All numbers are Python integers, which are exact and have no size limit.
  * We never use "/" (in Python it produces decimal numbers) nor "^" (in Python it is not a
    power).  We write q**j for q^j, and a // b and a % b for the quotient and the remainder of
    the division of a by b.  The tests check that "/" and "^" do not appear.
  * The field size q always comes first: for instance B(q, d, m, r) is B_r(q, d, m) of [PRM].
  * range(a, b) is the list of integers a, a+1, ..., b-1 (b is NOT included).

To use these functions in Sage, start Sage in the repository folder and type
load("src/formulas.py").  Sage reads .py files without modifying them.
"""

from functools import cache
from math import comb


# ---------------------------------------------------------------------------------------------
# Basic integer functions
# ---------------------------------------------------------------------------------------------

def binom(a, b):
    """The binomial coefficient, with the convention of [PRM]: it is 0 unless 0 <= b <= a."""
    if b < 0 or a < b:
        return 0
    return comb(a, b)


def p(q, j):
    """p_j = 1 + q + ... + q^j if j >= 0, and p_j = 0 if j < 0.

    p_m is the number of points of P^m(F_q), that is, the length of PRM_q(d, m).
    """
    return sum(q**i for i in range(j + 1))


def floor_q_power(q, mu):
    """floor(q^mu) for an integer mu >= -1: it is q^mu if mu >= 0, and 0 if mu = -1."""
    if mu >= 0:
        return q**mu
    return 0


def digit_sum(q, i):
    """sigma_q(i): the sum of the digits of the integer i >= 0 in base q."""
    total = 0
    while i > 0:
        total += i % q       # the last digit of i
        i = i // q           # remove the last digit
    return total


def leading_term(q, n):
    """For n >= 1, the numbers (a, s, b) with n = a q^s + b, 1 <= a <= q-1, 0 <= b < q^s  ([PRM], (6.1)).

    In other words, a is the leading digit of n in base q, at position s, and b is the rest.
    """
    s = 0
    while q**(s + 1) <= n:
        s += 1
    a = n // q**s
    b = n % q**s
    return a, s, b


def macaulay(h, d):
    """The Macaulay tuple (mu_1, ..., mu_d) of an integer h >= 0 in degree d  ([PRM], (1.2)).

    It is the unique tuple with -1 <= mu_1 <= ... <= mu_d such that
        h = binom(mu_1 + 1, 1) + binom(mu_2 + 2, 2) + ... + binom(mu_d + d, d).
    We compute nu_i = mu_i + i for i = d, d-1, ..., 1: nu_i is the largest integer
    with binom(nu_i, i) <= (what is left of h).
    """
    mu = [0] * (d + 1)               # mu[i] will be mu_i; position 0 is not used
    for i in range(d, 0, -1):        # i = d, d-1, ..., 1
        nu = i - 1                   # binom(i - 1, i) = 0, which is always <= h
        while binom(nu + 1, i) <= h:
            nu += 1
        mu[i] = nu - i
        h -= binom(nu, i)
    return tuple(mu[1:])             # (mu_1, ..., mu_d)


# ---------------------------------------------------------------------------------------------
# Dimensions, and the counting function A(t, D)
# ---------------------------------------------------------------------------------------------

@cache
def dim_RM(q, d, m):
    """dim RM_q(d, m) = the number of tuples u in {0, ..., q-1}^m with u_1 + ... + u_m <= d.

    We count according to the last coordinate c = u_m, which leaves u_1 + ... + u_(m-1) <= d - c.
    (@cache makes Python remember the results, because this function is called very often.)
    """
    if d < 0:
        return 0
    if m == 0:
        return 1
    return sum(dim_RM(q, d - c, m - 1) for c in range(q))


def A(q, t, D):
    """A(t, D) = the number of integers 0 <= i < t with sigma_q(i) <= D  ([PRM], Section 6.2).

    Write t = a q^s + b.  The integers i < a q^s are i = c q^s + j with 0 <= c < a and
    0 <= j < q^s, and sigma_q(i) = c + sigma_q(j); for each c there are dim RM_q(D - c, s)
    of them.  The integers a q^s <= i < t are i = a q^s + j with 0 <= j < b, and
    sigma_q(i) = a + sigma_q(j).
    """
    if t == 0 or D < 0:
        return 0
    a, s, b = leading_term(q, t)
    return sum(dim_RM(q, D - c, s) for c in range(a)) + A(q, b, D - a)


def dim_PRM(q, d, m):
    """k_d(m) = dim PRM_q(d, m) = dim RM_q(d-1, 0) + dim RM_q(d-1, 1) + ... + dim RM_q(d-1, m).

    This is [SJ24, Cor. 1] applied m times (also in [PRM], Section 6.2, with A(q^j, d-1) =
    dim RM_q(d-1, j)).  At the levels j with d > j(q-1), where Cor. 1 is not stated, both codes are
    whole spaces and the identity is p_j = q^j + p_{j-1}; the last term is dim RM_q(d-1, 0) = 1 =
    dim PRM_q(d, 0), since P^0 is a single point.  The result agrees with the closed formula of
    [SJ24, Thm 1].  As in [SJ24], PRM_q(d, m) = {0} for d <= 0.
    """
    if d <= 0:
        return 0
    return sum(dim_RM(q, d - 1, j) for j in range(m + 1))


# ---------------------------------------------------------------------------------------------
# The upper bound B_r(q, d, m) of [PRM, Thm 6.7]
# ---------------------------------------------------------------------------------------------

def h(q, d, n):
    """h_d(n) = min{ H_{Z_n^-}(d), H_{Z_n^+}(d) }, with the recursion of [PRM, Prop. 6.6].

    Write n = a q^s + b.
      If b <= p_{s-1}:   h_d(n) = A(a q^s, d) + h_{d-q+1}(b).
      If b >  p_{s-1}:   h_d(n) = min{ A(n, d),  k_d(s) + A(n - p_s, d - 1) }.
    As in [PRM], h_D(t) = 0 if D <= 0.  Also h_d(0) = 0: the empty set imposes no conditions.
    """
    if d <= 0 or n == 0:
        return 0
    a, s, b = leading_term(q, n)
    if b <= p(q, s - 1):
        return A(q, a * q**s, d) + h(q, d - q + 1, b)
    return min(A(q, n, d), dim_PRM(q, d, s) + A(q, n - p(q, s), d - 1))


def attaining_set(q, d, n):
    """Which of the two sets of [PRM, Section 6.2] gives h_d(n): "-" for Z_n^-, "+" for Z_n^+,
    and "-+" if both have the same Hilbert function.  (Used only to explain the bounds.)

    It follows the recursion of h: in the first case Z_n^- and Z_n^+ differ only in Z_b^- and Z_b^+.
    """
    if d <= 0 or n == 0:
        return "-+"
    a, s, b = leading_term(q, n)
    if b <= p(q, s - 1):
        return attaining_set(q, d - q + 1, b)
    minus = A(q, n, d)                                    # H_{Z_n^-}(d)
    plus = dim_PRM(q, d, s) + A(q, n - p(q, s), d - 1)    # H_{Z_n^+}(d)
    if minus < plus:
        return "-"
    if plus < minus:
        return "+"
    return "-+"


@cache
def largest_point_sets(q, d, m):
    """The tuple N with N[v] = max{ 0 <= n <= p_m : h_d(n) <= v }, for v = 0, 1, ..., k_d(m)."""
    k = dim_PRM(q, d, m)
    N = [0] * (k + 1)
    for n in range(p(q, m) + 1):
        N[h(q, d, n)] = n                # n increases, so at the end N[v] = max{ n : h_d(n) = v }
    for v in range(1, k + 1):            # now pass from "h_d(n) = v" to "h_d(n) <= v"
        N[v] = max(N[v], N[v - 1])
    return tuple(N)


def upper_bound_hierarchy(q, d, m):
    """(0, B_1, ..., B_k), where k = k_d(m) and   ([PRM], Thm 6.7)

        B_r(q, d, m) = p_m - max{ 0 <= n <= p_m : h_d(n) <= k_d(m) - r }.

    It is an upper bound for d_r(PRM_q(d, m)) for every d >= 1, with equality if d < q.
    [PRM, Conj. 6.9] says that equality always holds.
    """
    k = dim_PRM(q, d, m)
    N = largest_point_sets(q, d, m)
    return (0,) + tuple(p(q, m) - N[k - r] for r in range(1, k + 1))


def B(q, d, m, r):
    """B_r(q, d, m) of [PRM, Thm 6.7], for 1 <= r <= k_d(m)."""
    return upper_bound_hierarchy(q, d, m)[r]


# ---------------------------------------------------------------------------------------------
# Exact values
# ---------------------------------------------------------------------------------------------

def bdg_weight(q, d, m, r):
    """d_r(PRM_q(d, m)) for 1 <= d < q and 1 <= r <= binom(m + d, d)  ([PRM], Thm 1.1).

    With (mu_1, ..., mu_d) the Macaulay tuple of binom(m + d, d) - r,
        d_r = p_m - p_{mu_d} - ( floor(q^mu_1) + ... + floor(q^mu_{d-1}) ).
    """
    mu = macaulay(binom(m + d, d) - r, d)       # mu[0] is mu_1, ..., mu[d-1] is mu_d
    zeros = p(q, mu[d - 1]) + sum(floor_q_power(q, mu[i]) for i in range(d - 1))
    return p(q, m) - zeros


def bdg_hierarchy(q, d, m):
    """(0, d_1, ..., d_k) for PRM_q(d, m) with 1 <= d < q  ([PRM], Thm 1.1)."""
    return (0,) + tuple(bdg_weight(q, d, m, r) for r in range(1, binom(m + d, d) + 1))


def sorensen_minimum_distance(q, d, m):
    """d_1(PRM_q(d, m)) for d >= 1 (Sorensen 1991; see also [SJ24, Thm 1]).

    If d <= m(q-1), write d - 1 = a(q-1) + b with 0 <= b < q-1; then d_1 = (q - b) q^(m-a-1).
    If d > m(q-1), the code is the whole space and d_1 = 1.
    """
    if d > m * (q - 1):
        return 1
    a = (d - 1) // (q - 1)
    b = (d - 1) % (q - 1)
    return (q - b) * q**(m - a - 1)


def wei_dual(dual_hierarchy, n):
    """Wei duality (Wei 1991; [SJ24, Thm 9]): the hierarchy of a code C of length n,
    from the hierarchy (0, d_1(C^perp), d_2(C^perp), ...) of its dual.

    The weights of C are the integers in {1, ..., n} that are not of the form n + 1 - d_s(C^perp).
    """
    excluded = {n + 1 - w for w in dual_hierarchy[1:]}
    return (0,) + tuple(w for w in range(1, n + 1) if w not in excluded)


def high_degree_hierarchy(q, d, m):
    """(0, d_1, ..., d_k) for PRM_q(d, m) with (m-1)(q-1) < d < m(q-1)  ([PRM], Cor. 4.2).

    The dual is PRM_q(e, m) with e = m(q-1) - d < q-1 (Sorensen; [SJ24, Thm 2]), whose
    weights are given by Thm 1.1, and we apply Wei duality.  In this range d lies strictly between
    the multiples (m-1)(q-1) and m(q-1) of q-1, so d is not a multiple of q-1, and by [SJ24, Thm 2]
    the dual is exactly PRM_q(e, m), with no all-ones vector added.
    """
    e = m * (q - 1) - d
    return wei_dual(bdg_hierarchy(q, e, m), p(q, m))


def large_degree_hierarchy(q, d, m):
    """(0, d_1, ..., d_k) for PRM_q(d, m) with d >= m(q-1).

    If d > m(q-1), the code is the whole space F_q^{p_m}, so d_r = r.
    If d = m(q-1), the dual code is spanned by the all-ones vector (Sorensen; [SJ24, Thm 2]),
    whose only weight is p_m, and Wei duality gives d_r = r + 1.
    """
    n = p(q, m)
    if d > m * (q - 1):
        return tuple(range(0, n + 1))
    return wei_dual((0, n), n)


def known_hierarchy(q, d, m):
    """For d >= 1: the complete hierarchy (0, d_1, ..., d_k) of PRM_q(d, m) when one of the results
    above gives it (d < q, or d > (m-1)(q-1)), together with the name of the result.
    Otherwise, and also for d <= 0, it returns (None, None).
    """
    if d <= 0:
        return None, None
    if d < q:
        return bdg_hierarchy(q, d, m), "PRM Thm 1.1"
    if (m - 1) * (q - 1) < d < m * (q - 1):
        return high_degree_hierarchy(q, d, m), "PRM Cor 4.2"
    if d >= m * (q - 1):
        return large_degree_hierarchy(q, d, m), "large degree"
    return None, None


def lifted_weights(q, d, m):
    """The weights given by [PRM, Prop. 6.12], as a dictionary {r: d_r}.  Empty if it does not apply.

    Let 0 <= t <= m-1 and h = m - t.
      (a) If d = 1 + t(q-1):              d_r = q^h + q^(h-1) + ... + q^(h-r+1)  for 1 <= r <= h+1.
      (b) If q >= 3 and d = 2 + t(q-1):   d_r = q^h - q^(h-r)  for 1 <= r <= h,  and  d_(h+1) = q^h.
    (Below, hh stands for the h of the paper, because h is already the name of a function.)
    """
    for t in range(m):
        hh = m - t
        if d == 1 + t * (q - 1):
            # q^h + ... + q^(h-r+1) = p_h - p_(h-r), as in the proof of [PRM, Prop. 6.12]
            # (for r = h+1 this is p_h, because p_(-1) = 0).
            return {r: p(q, hh) - p(q, hh - r) for r in range(1, hh + 2)}
        if q >= 3 and d == 2 + t * (q - 1):
            weights = {r: q**hh - q**(hh - r) for r in range(1, hh + 1)}
            weights[hh + 1] = q**hh
            return weights
    return {}


# ---------------------------------------------------------------------------------------------
# Affine Reed-Muller codes, and the recursive lower bound of [SJ24, Thm 7]
# ---------------------------------------------------------------------------------------------

@cache
def affine_hierarchy(q, d, m):
    """(0, d_1, ..., d_k) for the affine Reed-Muller code RM_q(d, m), d >= 0.

    By Heijnen and Pellikaan, in the form of [SJ24, Thm 6]: d_r - 1 is the r-th smallest
    integer i in {0, ..., q^m - 1} whose base-q digit sum is larger than m(q-1) - d - 1.
    (The base-q digits of i, from the most significant one, are the tuple beta of [SJ24],
    and the lexicographic order of these tuples is the usual order of the integers.)
    """
    if d < 0:
        return (0,)
    return (0,) + tuple(i + 1 for i in range(q**m) if digit_sum(q, i) > m * (q - 1) - d - 1)


def recursive_lower_bound(q, d, m, r, same_degree, lower_degree):
    """The lower bound of [SJ24, Thm 7] for d_r(PRM_q(d, m)), where m >= 2, 1 <= d <= m(q-1)
    and 2 <= r <= k_d(m).  Returns (bound, alpha, gamma), with (alpha, gamma) attaining the minimum.

    The inputs are lower bounds for the weights of the two smaller codes:
        same_degree[alpha]  <=  d_alpha(PRM_q(d, m-1))          for 0 <= alpha <= k_d(m-1),
        lower_degree[gamma] <=  d_gamma(PRM_q(d-q+1, m-1))      for 0 <= gamma <= k_{d-q+1}(m-1),
    with same_degree[0] = lower_degree[0] = 0.  We may use lower bounds instead of the true values
    because B_{alpha,gamma} below can only decrease when they decrease.

    The bound is the minimum of
        B_{alpha,gamma} = max( d_{r-gamma}(RM_q(d, m)), d_{r-alpha}(RM_q(d-1, m)) )
                          + max( same_degree[alpha], lower_degree[gamma] )
    over the set Y of pairs (alpha, gamma) with
        max(r - dim RM_q(d-1, m), 0)  <=  alpha  <=  min(k_d(m-1), r),
        max(r - dim RM_q(d, m), 0)    <=  gamma  <=  min(k_{d-q+1}(m-1), alpha).
    """
    RM_d = affine_hierarchy(q, d, m)              # RM_d[i] = d_i(RM_q(d, m))
    RM_d_minus_1 = affine_hierarchy(q, d - 1, m)  # RM_d_minus_1[i] = d_i(RM_q(d-1, m))
    k_same = len(same_degree) - 1                 # = k_d(m-1)
    k_lower = len(lower_degree) - 1               # = k_{d-q+1}(m-1)
    best = None
    for alpha in range(max(r - dim_RM(q, d - 1, m), 0), min(k_same, r) + 1):
        for gamma in range(max(r - dim_RM(q, d, m), 0), min(k_lower, alpha) + 1):
            value = (max(RM_d[r - gamma], RM_d_minus_1[r - alpha])
                     + max(same_degree[alpha], lower_degree[gamma]))
            if best is None or value < best[0]:
                best = (value, alpha, gamma)
    return best
