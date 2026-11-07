"""
Formulas and bounds for the generalized Hamming weights of projective Reed-Muller codes PRM_q(d, m).

Each function implements one formula, with the notation of the papers:

  [SJ26]  R. San-Jose, Common zeros of homogeneous polynomials and the weight hierarchy of
          projective Reed-Muller codes, arXiv:2611.08203 (2026).  Its numbering is that of v1.
  [SJ24]  R. San-Jose, A recursive construction for projective Reed-Muller codes,
          IEEE Trans. Inform. Theory 70(12) (2024), 8511-8523.

How to read this file:

  * A weight hierarchy is stored as a tuple H = (0, d_1, d_2, ..., d_k), so that H[r] is d_r.
    Position 0 holds d_0 = 0, the convention of [SJ24].  Hence len(H) = k + 1.
  * All numbers are Python integers, which are exact and have no size limit.
  * We never use "/" (in Python it produces decimal numbers) nor "^" (in Python it is not a
    power).  We write q**j for q^j, and a // b and a % b for the quotient and the remainder of
    the division of a by b.  The tests check that "/" and "^" do not appear.
  * The field size q always comes first: for instance B(q, d, m, r) is B_r(q, d, m) of [SJ26].

Python notation used below:

  * range(a, b) is the list of integers a, a+1, ..., b-1 (b is NOT included), and range(b) is
    range(0, b), that is 0, 1, ..., b-1.  Both are empty if b <= a (resp. b <= 0).
    range(a, b, -1) counts down: a, a-1, ..., b+1.
  * sum(f(i) for i in range(a, b)) is the sum of f(i) for a <= i < b (an empty sum is 0), and
    tuple(f(i) for i in range(a, b)) is the tuple (f(a), f(a+1), ..., f(b-1)).  Adding
    "if condition" at the end keeps only the i satisfying the condition.
  * (0,) is the tuple with the single entry 0 (the comma is needed), and + joins two tuples:
    (0,) + (5, 7) = (0, 5, 7).  H[1:] is H without its first entry H[0].
  * A function can return several values ("return a, s, b"), and "a, s, b = leading_term(q, n)"
    gives a name to each of them.
  * {f(w) for w in S} is a set, and {r: f(r) for r in S} is a dictionary, in which weights[r] is f(r).
  * @cache, written above a function, makes Python remember its results, so that each value is
    computed only once.  It does not change the results.
  * None means "no value", and "x is None" tests it.

To use these functions in Sage, start Sage in the repository folder and type
load("src/formulas.py").  Sage reads .py files without modifying them.
"""

from functools import cache
from math import comb


# ---------------------------------------------------------------------------------------------
# Basic integer functions
# ---------------------------------------------------------------------------------------------

def binom(a, b):
    """The binomial coefficient, with the convention of [SJ26]: it is 0 unless 0 <= b <= a."""
    if b < 0 or a < b:
        return 0
    return comb(a, b)


def p(q, j):
    """p_j = 1 + q + ... + q^j if j >= 0, and p_j = 0 if j < 0.

    p_m is the number of points of P^m(F_q), that is, the length of PRM_q(d, m).
    """
    return sum(q**i for i in range(j + 1))       # for j < 0, range(j + 1) is empty and the sum is 0


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
    """For n >= 1, the numbers (a, s, b) with n = a q^s + b, 1 <= a <= q-1, 0 <= b < q^s  ([SJ26], (6.1)).

    In other words, a is the leading digit of n in base q, at position s, and b is the rest.
    """
    s = 0
    while q**(s + 1) <= n:
        s += 1
    a = n // q**s
    b = n % q**s
    return a, s, b


def macaulay(h, d):
    """The Macaulay tuple (mu_1, ..., mu_d) of an integer h >= 0 in degree d  ([SJ26], (1.2)).

    It is the unique tuple with -1 <= mu_1 <= ... <= mu_d such that
        h = binom(mu_1 + 1, 1) + binom(mu_2 + 2, 2) + ... + binom(mu_d + d, d).
    We compute nu_i = mu_i + i for i = d, d-1, ..., 1: nu_i is the largest integer
    with binom(nu_i, i) <= (what is left of h).
    (Inside this function, h is this integer, as in (1.2), and not the function h_d(n) below.)
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
        return 1                     # only the empty tuple, whose sum 0 is <= d
    return sum(dim_RM(q, d - c, m - 1) for c in range(q))


def A(q, t, D):
    """A(t, D) = the number of integers 0 <= i < t with sigma_q(i) <= D  ([SJ26], Section 6.2).

    Write t = a q^s + b.  The integers i < a q^s are i = c q^s + j with 0 <= c < a and
    0 <= j < q^s, and sigma_q(i) = c + sigma_q(j).  The s base-q digits of such a j form a tuple
    in {0, ..., q-1}^s with sum sigma_q(j), so for each c there are dim RM_q(D - c, s) of them.
    The integers a q^s <= i < t are i = a q^s + j with 0 <= j < b, and sigma_q(i) = a + sigma_q(j),
    so there are A(b, D - a) of them.  Hence
        A(t, D) = dim RM_q(D, s) + dim RM_q(D - 1, s) + ... + dim RM_q(D - a + 1, s) + A(b, D - a).
    """
    if t == 0 or D < 0:
        return 0
    a, s, b = leading_term(q, t)
    return sum(dim_RM(q, D - c, s) for c in range(a)) + A(q, b, D - a)


@cache
def dim_PRM(q, d, m):
    """k_d(m) = dim PRM_q(d, m) = dim RM_q(d-1, 0) + dim RM_q(d-1, 1) + ... + dim RM_q(d-1, m).

    This is [SJ24, Cor. 1] applied m times (also in [SJ26], Section 6.2, with A(q^j, d-1) =
    dim RM_q(d-1, j)).  At the levels j with d > j(q-1), where Cor. 1 is not stated, both codes are
    whole spaces and the identity is p_j = q^j + p_{j-1}; the last term is dim RM_q(d-1, 0) = 1 =
    dim PRM_q(d, 0), since P^0 is a single point.  The result agrees with the closed formula of
    [SJ24, Thm. 1].  As in [SJ24], PRM_q(d, m) = {0} for d <= 0.
    """
    if d <= 0:
        return 0
    return sum(dim_RM(q, d - 1, j) for j in range(m + 1))


# ---------------------------------------------------------------------------------------------
# The upper bound B_r(q, d, m) of [SJ26, Thm. 6.7]
# ---------------------------------------------------------------------------------------------

def h(q, d, n):
    """h_d(n) = min{ H_{Z_n^-}(d), H_{Z_n^+}(d) }, with the recursion of [SJ26, Prop. 6.6].

    Write n = a q^s + b.
      If b <= p_{s-1}:   h_d(n) = A(a q^s, d) + h_{d-q+1}(b).
      If b >  p_{s-1}:   h_d(n) = min{ A(n, d),  k_d(s) + A(n - p_s, d - 1) }.
    As in [SJ26], h_D(t) = 0 if D <= 0.  Also h_d(0) = 0: the empty set imposes no conditions.
    """
    if d <= 0 or n == 0:
        return 0
    a, s, b = leading_term(q, n)
    if b <= p(q, s - 1):
        return A(q, a * q**s, d) + h(q, d - q + 1, b)
    return min(A(q, n, d), dim_PRM(q, d, s) + A(q, n - p(q, s), d - 1))


def attaining_set(q, d, n):
    """Which of the two sets of [SJ26, Section 6.2] gives h_d(n): "-" for Z_n^-, "+" for Z_n^+,
    and "-+" if H_{Z_n^-}(d) = H_{Z_n^+}(d), so that both sets give h_d(n).
    (Used only to explain the bounds.)

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
def largest_n(q, d, m):
    """The tuple N with N[v] = max{ 0 <= n <= p_m : h_d(n) <= v }, for v = 0, 1, ..., k_d(m)."""
    k = dim_PRM(q, d, m)
    N = [0] * (k + 1)
    for n in range(p(q, m) + 1):
        # h_d(n) <= k_d(m), because a set of points imposes at most k_d(m) conditions on the forms
        # of degree d, so the position N[h_d(n)] exists.  Since n increases, at the end of this
        # loop N[v] = max{ n : h_d(n) = v }.
        N[h(q, d, n)] = n
    for v in range(1, k + 1):            # now pass from "h_d(n) = v" to "h_d(n) <= v"
        N[v] = max(N[v], N[v - 1])
    return tuple(N)


@cache
def upper_bound_hierarchy(q, d, m):
    """(0, B_1, ..., B_k), where k = k_d(m) and   ([SJ26], Thm. 6.7)

        B_r(q, d, m) = p_m - max{ 0 <= n <= p_m : h_d(n) <= k_d(m) - r }.

    It is an upper bound for d_r(PRM_q(d, m)) for every d >= 1, with equality if d < q.
    [SJ26, Conj. 6.9] says that equality always holds.
    """
    k = dim_PRM(q, d, m)
    N = largest_n(q, d, m)
    return (0,) + tuple(p(q, m) - N[k - r] for r in range(1, k + 1))


def B(q, d, m, r):
    """B_r(q, d, m) of [SJ26, Thm. 6.7], for 1 <= r <= k_d(m)."""
    return upper_bound_hierarchy(q, d, m)[r]


# ---------------------------------------------------------------------------------------------
# Exact values
# ---------------------------------------------------------------------------------------------

def bdg_weight(q, d, m, r):
    """d_r(PRM_q(d, m)) for 1 <= d < q and 1 <= r <= binom(m + d, d)  ([SJ26], Thm. 1.1).
    (bdg stands for Beelen, Datta and Ghorpade, who conjectured this formula [BDG22].)

    With (mu_1, ..., mu_d) the Macaulay tuple of binom(m + d, d) - r,
        e_r(d, m) = p_{mu_d} + floor(q^mu_1) + ... + floor(q^mu_{d-1})     ([SJ26], (1.3)),
        d_r = p_m - e_r(d, m)                                                ([SJ26], (1.4)).
    """
    mu = (None,) + macaulay(binom(m + d, d) - r, d)    # now mu[i] is mu_i, for 1 <= i <= d
    e_r = p(q, mu[d]) + sum(floor_q_power(q, mu[i]) for i in range(1, d))
    return p(q, m) - e_r


def bdg_hierarchy(q, d, m):
    """(0, d_1, ..., d_k) for PRM_q(d, m) with 1 <= d < q  ([SJ26], Thm. 1.1)."""
    return (0,) + tuple(bdg_weight(q, d, m, r) for r in range(1, binom(m + d, d) + 1))


def sorensen_minimum_distance(q, d, m):
    """d_1(PRM_q(d, m)) for d >= 1 (Sorensen 1991; see also [SJ24, Thm. 1]).

    If d <= m(q-1), write d - 1 = a(q-1) + b with 0 <= b < q-1; then d_1 = (q - b) q^(m-a-1).
    If d > m(q-1), the code is the whole space and d_1 = 1.
    """
    if d > m * (q - 1):
        return 1
    a = (d - 1) // (q - 1)
    b = (d - 1) % (q - 1)
    return (q - b) * q**(m - a - 1)


def wei_dual(dual_hierarchy, n):
    """Wei duality (Wei 1991; [SJ24, Thm. 9]): the hierarchy of a code C of length n,
    from the hierarchy (0, d_1(C^perp), d_2(C^perp), ...) of its dual.

    The weights of C are the integers in {1, ..., n} that are not of the form n + 1 - d_s(C^perp).
    """
    excluded = {n + 1 - w for w in dual_hierarchy[1:]}
    return (0,) + tuple(w for w in range(1, n + 1) if w not in excluded)


def high_degree_hierarchy(q, d, m):
    """(0, d_1, ..., d_k) for PRM_q(d, m) with (m-1)(q-1) < d < m(q-1)  ([SJ26], Cor. 4.2).

    The dual is PRM_q(e, m) with e = m(q-1) - d < q-1 (Sorensen; [SJ24, Thm. 2]), whose
    weights are given by Thm. 1.1, and we apply Wei duality.  In this range d lies strictly between
    the multiples (m-1)(q-1) and m(q-1) of q-1, so d is not a multiple of q-1, and by [SJ24, Thm. 2]
    the dual is exactly PRM_q(e, m), with no all-ones vector added.
    """
    e = m * (q - 1) - d
    return wei_dual(bdg_hierarchy(q, e, m), p(q, m))


def large_degree_hierarchy(q, d, m):
    """(0, d_1, ..., d_k) for PRM_q(d, m) with d >= m(q-1).

    If d > m(q-1), the code is the whole space F_q^{p_m}, so d_r = r.
    If d = m(q-1), the dual code is spanned by the all-ones vector (Sorensen; [SJ24, Thm. 2]),
    whose only weight is p_m, and Wei duality gives d_r = r + 1.
    """
    n = p(q, m)
    if d > m * (q - 1):
        return tuple(range(0, n + 1))
    return wei_dual((0, n), n)


def known_hierarchy(q, d, m):
    """For d >= 1: the complete hierarchy (0, d_1, ..., d_k) of PRM_q(d, m) when one of the results
    above gives it (d < q, or d > (m-1)(q-1)), together with the name of the result: "SJ26 Thm. 1.1",
    "SJ26 Cor. 4.2", "whole space" or "dual is all-ones".  Otherwise, and also for d <= 0, it
    returns (None, None).
    """
    if d <= 0:
        return None, None
    if d < q:
        return bdg_hierarchy(q, d, m), "SJ26 Thm. 1.1"
    if (m - 1) * (q - 1) < d < m * (q - 1):
        return high_degree_hierarchy(q, d, m), "SJ26 Cor. 4.2"
    if d > m * (q - 1):
        return large_degree_hierarchy(q, d, m), "whole space"
    if d == m * (q - 1):
        return large_degree_hierarchy(q, d, m), "dual is all-ones"
    return None, None


def lifted_weights(q, d, m):
    """The weights given by [SJ26, Prop. 6.12], as a dictionary {r: d_r}.  Empty if it does not apply.

    Let 0 <= t <= m-1 and h = m - t.
      (a) If d = 1 + t(q-1):              d_r = q^h + q^(h-1) + ... + q^(h-r+1)  for 1 <= r <= h+1.
      (b) If q >= 3 and d = 2 + t(q-1):   d_r = q^h - q^(h-r)  for 1 <= r <= h,  and  d_(h+1) = q^h.
    (Inside this function, h is the number m - t of the paper, and not the function h_d(n) above.)
    """
    for t in range(m):
        h = m - t
        if d == 1 + t * (q - 1):
            # q^h + ... + q^(h-r+1) = p_h - p_(h-r), as in the proof of [SJ26, Prop. 6.12]
            # (for r = h+1 this is p_h, because p_(-1) = 0).
            return {r: p(q, h) - p(q, h - r) for r in range(1, h + 2)}
        if q >= 3 and d == 2 + t * (q - 1):
            weights = {r: q**h - q**(h - r) for r in range(1, h + 1)}
            weights[h + 1] = q**h
            return weights
    return {}


# ---------------------------------------------------------------------------------------------
# Affine Reed-Muller codes, and the recursive lower bound of [SJ24, Thm. 7]
# ---------------------------------------------------------------------------------------------

@cache
def affine_hierarchy(q, d, m):
    """(0, d_1, ..., d_k) for the affine Reed-Muller code RM_q(d, m), d >= 0.

    By Heijnen and Pellikaan, in the form of [SJ24, Thm. 6]: d_r - 1 is the r-th smallest
    integer i in {0, ..., q^m - 1} whose base-q digit sum is larger than m(q-1) - d - 1.
    (The base-q digits of i, from the most significant one, are the tuple beta of [SJ24],
    and the lexicographic order of these tuples is the usual order of the integers.)
    """
    if d < 0:
        return (0,)
    return (0,) + tuple(i + 1 for i in range(q**m) if digit_sum(q, i) > m * (q - 1) - d - 1)


def recursive_lower_bound(q, d, m, r, PRM_d, PRM_d_minus_q_plus_1):
    """The lower bound of [SJ24, Thm. 7] for d_r(PRM_q(d, m)), where 1 <= d <= m(q-1) and
    2 <= r <= k_d(m), for m >= 2.  Returns (bound, alpha, gamma), with (alpha, gamma) attaining
    the minimum.

    The names follow [SJ24, Thm. 7], where the two smaller codes are PRM_d(m-1) and
    PRM_{d-(q-1)}(m-1), both in dimension m-1.  The inputs are lower bounds for their weights:
        PRM_d[alpha]                <= d_alpha(PRM_q(d, m-1))        for 0 <= alpha <= k_d(m-1),
        PRM_d_minus_q_plus_1[gamma] <= d_gamma(PRM_q(d-q+1, m-1))    for 0 <= gamma <= k_{d-q+1}(m-1),
    with PRM_d[0] = PRM_d_minus_q_plus_1[0] = 0.  We may use lower bounds instead of the true values
    because B_{alpha,gamma} below can only decrease when they decrease.

    The bound is the minimum of
        B_{alpha,gamma} = max( d_{r-gamma}(RM_q(d, m)), d_{r-alpha}(RM_q(d-1, m)) )
                          + max( d_alpha(PRM_q(d, m-1)), d_gamma(PRM_q(d-q+1, m-1)) )
    over the set Y of pairs (alpha, gamma) with
        max(r - dim RM_q(d-1, m), 0)  <=  alpha  <=  min(k_d(m-1), r),
        max(r - dim RM_q(d, m), 0)    <=  gamma  <=  min(k_{d-q+1}(m-1), alpha).
    Y is not empty: it contains the first pair visited below, alpha = max(r - dim RM_q(d-1, m), 0)
    and gamma = max(r - dim RM_q(d, m), 0).  This follows from r <= k_d(m), from
    k_d(m) = dim RM_q(d-1, m) + k_d(m-1) = dim RM_q(d, m) + k_{d-q+1}(m-1)  ([SJ26], Section 6.2 and
    the proof of Lemma 6.10; see test_recursions), and from dim RM_q(d, m) >= dim RM_q(d-1, m).
    If several pairs attain the minimum, the one with the smallest alpha (and then the smallest
    gamma) is returned.
    """
    RM_d = affine_hierarchy(q, d, m)                # RM_d[i] = d_i(RM_q(d, m))
    RM_d_minus_1 = affine_hierarchy(q, d - 1, m)    # RM_d_minus_1[i] = d_i(RM_q(d-1, m))
    best = None                                     # (value, alpha, gamma) of the smallest value so far
    for alpha in range(max(r - dim_RM(q, d - 1, m), 0), min(dim_PRM(q, d, m - 1), r) + 1):
        for gamma in range(max(r - dim_RM(q, d, m), 0), min(dim_PRM(q, d - q + 1, m - 1), alpha) + 1):
            value = (max(RM_d[r - gamma], RM_d_minus_1[r - alpha])
                     + max(PRM_d[alpha], PRM_d_minus_q_plus_1[gamma]))
            if best is None or value < best[0]:     # the first pair of Y, or a smaller value
                best = (value, alpha, gamma)
    return best


# ---------------------------------------------------------------------------------------------
# Duality: Wei duality applied to bounds, as in [SJ24, Section V-C]
# ---------------------------------------------------------------------------------------------

def dual_degree(q, d, m):
    """The degree e = m(q-1) - d of the dual code.  By Sorensen ([SJ24, Thm. 2]), for 1 <= d <= m(q-1) - 1,

        PRM_q(d, m)^perp = PRM_q(e, m)                     if q-1 does not divide d,
        PRM_q(d, m)^perp = PRM_q(e, m) + <(1, ..., 1)>     if q-1 divides d (for q = 2, always).

    Returns None for the other degrees (for d >= m(q-1) the hierarchy is known anyway).
    """
    if 1 <= d <= m * (q - 1) - 1:
        return m * (q - 1) - d
    return None


def bounds_after_adding_a_vector(n, lower, upper):
    """Bounds for the weights of D + <v>, where D is a code of length n and dimension k, and v is not in
    D (so D + <v> has dimension k + 1), from bounds  lower[s] <= d_s(D) <= upper[s],  1 <= s <= k:

        d_{s-1}(D) <= d_s(D + <v>) <= d_s(D).

    The second inequality holds because D is contained in D + <v>.  For the first one, a subspace of
    D + <v> of dimension s meets D in a subspace of dimension at least s - 1, whose support is contained
    in its support.  For s = 1 we use d_1 >= 1, and for s = k + 1 we use d_{k+1} <= n.
    Returns two lists, indexed by s = 0, 1, ..., k + 1 (position 0 holds 0, as for a hierarchy).
    """
    k = len(lower) - 1
    new_lower = [0, 1] + [lower[s - 1] for s in range(2, k + 2)]
    new_upper = [0] + [upper[s] for s in range(1, k + 1)] + [n]
    return new_lower, new_upper


def wei_duality_bounds(n, k, dual_lower, dual_upper):
    """Bounds for the weights of a code C of length n and dimension k, obtained from bounds for the
    weights of its dual code C^perp by Wei duality ([SJ24, Thm. 9]):

        dual_lower[s] <= d_s(C^perp) <= dual_upper[s]      for 1 <= s <= n - k.

    Let N(w) = #{r : d_r(C) <= w} be the number of weights of C that are at most w.  The weights of C
    are the integers in {1, ..., n} that are not of the form n + 1 - d_s(C^perp), so

        N(w) = w - #{s : n + 1 - d_s(C^perp) <= w} = w - (n - k) + #{s : d_s(C^perp) <= n - w}.

    The last number is at least #{s : dual_upper[s] <= n - w} and at most #{s : dual_lower[s] <= n - w}.
    Hence, for every 0 <= w <= n:
      * if  w - (n - k) + #{s : dual_upper[s] <= n - w} >= r,  then N(w) >= r, that is, d_r(C) <= w;
      * if  w - (n - k) + #{s : dual_lower[s] <= n - w} <= r - 1,  then N(w) <= r - 1, that is,
        d_r(C) >= w + 1.
    For each r we take the best w.  Returns two lists, lower and upper, indexed by r = 1, ..., k
    (position 0 is not used):
        upper[r] = (w, w, count):      d_r(C) <= w,       with count = #{s : dual_upper[s] <= n - w};
        lower[r] = (w + 1, w, count):  d_r(C) >= w + 1,   with count = #{s : dual_lower[s] <= n - w}.
    The first entry is the bound; the other two explain it.
    """
    k_dual = n - k
    # at_most_upper[x] = #{s : dual_upper[s] <= x}  and  at_most_lower[x] = #{s : dual_lower[s] <= x},
    # for 0 <= x <= n: we count the s for each value, and then add up.
    at_most_upper = [0] * (n + 1)
    at_most_lower = [0] * (n + 1)
    for s in range(1, k_dual + 1):
        at_most_upper[dual_upper[s]] += 1
        at_most_lower[dual_lower[s]] += 1
    for x in range(1, n + 1):
        at_most_upper[x] += at_most_upper[x - 1]
        at_most_lower[x] += at_most_lower[x - 1]

    # Upper bounds: for each r, the smallest w with  w - (n - k) + at_most_upper[n - w] >= r.
    upper = [None] * (k + 1)
    found = 0                               # upper[1], ..., upper[found] are known
    for w in range(n + 1):                  # w = 0, 1, ..., n: the first w that works is the best
        count = at_most_upper[n - w]
        at_least = w - k_dual + count       # N(w) >= at_least
        while found < min(at_least, k):     # every r <= at_least works with this w
            found += 1
            upper[found] = (w, w, count)

    # Lower bounds: for each r, the largest w with  w - (n - k) + at_most_lower[n - w] <= r - 1.
    lower = [None] * (k + 1)
    found = k + 1                           # lower[found], ..., lower[k] are known
    for w in range(n, -1, -1):              # w = n, n-1, ..., 0: the first w that works is the best
        count = at_most_lower[n - w]
        at_most = w - k_dual + count        # N(w) <= at_most
        while found > max(at_most + 1, 1):  # every r >= at_most + 1 works with this w
            found -= 1
            lower[found] = (w + 1, w, count)
    return lower, upper


# ---------------------------------------------------------------------------------------------
# Classical bounds, valid for every linear code
# ---------------------------------------------------------------------------------------------
#
# The two relations below hold for every linear code C of length n and dimension k over F_q, with
# weights 0 = d_0 < d_1 < ... < d_k <= n.  Each one is used in both directions, and together they
# contain the other classical bounds of [Wei91], [HKY92] and [HKLY95] (see the README).
#
#   [Wei91]   V. K. Wei, Generalized Hamming weights for linear codes, IEEE Trans. Inform. Theory
#             37(5) (1991), 1412-1418.
#   [HKY92]   T. Helleseth, T. Klove, O. Ytrehus, Generalized Hamming weights of linear codes,
#             IEEE Trans. Inform. Theory 38(3) (1992), 1133-1140.
#   [HKLY95]  T. Helleseth, T. Klove, V. I. Levenshtein, O. Ytrehus, Bounds on the minimum support
#             weights, IEEE Trans. Inform. Theory 41(2) (1995), 432-440.

def ceil_div(a, b):
    """The smallest integer that is at least a/b, for integers a and b > 0 (exact for numbers of any size)."""
    return -(-a // b)


def fundamental_lower(q, r, lower_previous):
    """The fundamental relation (the case s = r - 1 of [HKLY95, Thm. 1], and [HKY92, Thm. 1] for q = 2):
    for 2 <= r <= k,

        (q^r - q) d_r >= (q^r - 1) d_{r-1}.

    Given d_{r-1} >= lower_previous, it gives  d_r >= ceil((q^r - 1) lower_previous / (q^r - q)),  which is
    returned.  Since (q^r - 1)/(q^r - q) > 1, this is at least lower_previous + 1: the relation contains
    the strict increase d_{r-1} < d_r ([Wei91, Thm. 1]; [SJ24, Thm. 5])."""
    return ceil_div((q**r - 1) * lower_previous, q**r - q)


def fundamental_upper(q, r, upper_next):
    """The fundamental relation for r + 1, read the other way: for 1 <= r <= k - 1, given
    d_{r+1} <= upper_next, it gives  d_r <= floor((q^(r+1) - q) upper_next / (q^(r+1) - 1)),  which is
    returned.  It is at most upper_next - 1."""
    return (q**(r + 1) - q) * upper_next // (q**(r + 1) - 1)


def griesmer_sum(q, k, a):
    """sum_{i=0}^{k-1} ceil(a / q^i), for k >= 0 and a >= 0.  By the Griesmer bound, a linear code over F_q
    of dimension k and minimum distance at least a has at least this length."""
    total = 0
    power = 1                                # power = q^i
    for i in range(k):
        if power >= a:                       # then ceil(a / q^j) = min(a, 1) for every j >= i
            return total + (k - i) * min(a, 1)
        total += ceil_div(a, power)
        power *= q
    return total


def residual_length(q, k, r, a, b):
    """a + sum_{i=0}^{k-r-1} ceil((b - a) / q^i), for 0 <= a < b.

    The residual code bound ([HKLY95, proof of Thm. 4]) says that, for 0 <= r <= k - 1,

        n - d_r >= sum_{i=0}^{k-r-1} ceil((d_{r+1} - d_r) / q^i),

    that is, residual_length(q, k, r, d_r, d_{r+1}) <= n.  Proof: let D be a subcode of dimension r whose
    support has d_r elements.  Deleting these d_r coordinates from the codewords of C gives a code of
    length n - d_r and dimension k - r (the codewords of C that vanish outside the support of D are those
    of D, since one more would give d_{r+1} <= d_r), whose nonzero codewords have weight at least
    d_{r+1} - d_r.  Apply the Griesmer bound to it.  For r = 0 (d_0 = 0) this is the Griesmer bound.

    As a function of a (with b fixed) this does not increase, because the term i = 0 is b - a and the
    other terms do not increase.  As a function of b (with a fixed) it does not decrease."""
    return a + griesmer_sum(q, k - r, b - a)


def residual_upper(q, n, k, r, upper_r):
    """An upper bound for d_{r+1}, 0 <= r <= k - 1, from the residual code bound and d_r <= upper_r.

    Let b >= upper_r.  If d_{r+1} >= b + 1, then d_r <= upper_r < b + 1 <= d_{r+1}, and the monotonicity
    of residual_length gives  n >= residual_length(d_r, d_{r+1}) >= residual_length(upper_r, b + 1).
    So if  residual_length(upper_r, b + 1) > n,  then d_{r+1} <= b.  Returns (b, total) for the smallest
    such b, with total = residual_length(upper_r, b + 1).  (b = n always works, since total >= b + 1.)"""
    def too_long(b):
        return residual_length(q, k, r, upper_r, b + 1) > n
    low, high = upper_r, max(n, upper_r)     # too_long(high) holds; find the smallest b with too_long(b)
    while low < high:
        middle = (low + high) // 2
        if too_long(middle):
            high = middle
        else:
            low = middle + 1
    return low, residual_length(q, k, r, upper_r, low + 1)


def residual_lower(q, n, k, r, lower_next):
    """A lower bound for d_r, 1 <= r <= k - 1, from the residual code bound and d_{r+1} >= lower_next.

    Let 1 <= a <= lower_next.  If d_r <= a - 1, then d_r <= a - 1 < lower_next <= d_{r+1}, and the
    monotonicity of residual_length gives  n >= residual_length(d_r, d_{r+1}) >= residual_length(a - 1, lower_next).
    So if  residual_length(a - 1, lower_next) > n,  then d_r >= a.  Returns (a, total) for the largest
    such a, with total = residual_length(a - 1, lower_next), or (0, None) if there is none."""
    def too_long(a):
        return residual_length(q, k, r, a - 1, lower_next) > n
    if lower_next < 1 or not too_long(1):
        return 0, None
    low, high = 1, lower_next                # too_long(low) holds; find the largest a with too_long(a)
    while low < high:
        middle = (low + high + 1) // 2
        if too_long(middle):
            low = middle
        else:
            high = middle - 1
    return low, residual_length(q, k, r, low - 1, lower_next)
