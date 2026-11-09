"""
The rules used to fill the table.

Each rule looks at one code PRM_q(d, m), proposes bounds for its weights together with the reason,
and returns the number of changes it made to the table.  A rule can only raise a lower bound or lower
an upper bound (see Table.improve_lower and Table.improve_upper), and the bound proposed by each rule
can only improve when the bounds it uses improve (the recursive bound uses the bounds of smaller codes,
Wei duality those of the dual code, and the classical bounds those of the other weights of the code).
Hence the order of the rules does not matter for the final table.  It only matters for the credit:
when two rules give the same bound, the one applied first keeps it.

The list RULES at the end of this file is the list of rules that generate.py uses.
"""

from formulas import (affine_hierarchy, attaining_set, binom, bounds_after_adding_a_vector, dim_PRM,
                      dual_degree, fundamental_lower, fundamental_upper, known_hierarchy, largest_n,
                      lifted_weights, macaulay, p, recursive_lower_bound, residual_lower, residual_upper,
                      sorensen_minimum_distance, wei_duality_bounds)


def exact_values(table, q, d, m):
    """Exact values: the complete hierarchy when it is known ([SJ26, Thm. 1.2] for d < q, [SJ26, Cor. 4.2]
    for (m-1)(q-1) < d < m(q-1), and the degrees d >= m(q-1)); the minimum distance (Sorensen);
    and the first weights given by [SJ26, Prop. 6.12]."""
    code = (q, d, m)
    changes = 0

    H, name = known_hierarchy(q, d, m)  # name: "SJ26 Thm. 1.1", "SJ26 Cor. 4.2", "whole space" or "dual is all-ones"
    if H is not None:
        for r in range(1, len(H)):
            reason = {"rule": name}
            if name == "SJ26 Thm. 1.1":
                reason["mu"] = macaulay(binom(m + d, d) - r, d)
            if name == "SJ26 Cor. 4.2":
                reason["dual_degree"] = m * (q - 1) - d
            changes += table.improve_lower(code, r, H[r], reason)
            changes += table.improve_upper(code, r, H[r], reason)

    d1 = sorensen_minimum_distance(q, d, m)
    changes += table.improve_lower(code, 1, d1, {"rule": "Sorensen"})
    changes += table.improve_upper(code, 1, d1, {"rule": "Sorensen"})

    for r, value in lifted_weights(q, d, m).items():
        reason = {"rule": "SJ26 Prop. 6.12"}
        changes += table.improve_lower(code, r, value, reason)
        changes += table.improve_upper(code, r, value, reason)
    return changes


def upper_bound(table, q, d, m):
    """The upper bound B_r(q, d, m) = p_m - n of [SJ26, Thm. 6.7], where n is the largest integer
    0 <= n <= p_m with h_d(n) <= k_d(m) - r.  The reason records n and which of the sets Z_n^-, Z_n^+
    is used."""
    code = (q, d, m)
    k = dim_PRM(q, d, m)
    N = largest_n(q, d, m)                 # N[v] = max{ n : h_d(n) <= v }
    changes = 0
    for r in range(1, k + 1):
        n = N[k - r]
        reason = {"rule": "SJ26 Thm. 6.7", "n": n, "set": attaining_set(q, d, n)}
        changes += table.improve_upper(code, r, p(q, m) - n, reason)
    return changes


def recursive_bound(table, q, d, m):
    """The lower bound of [SJ24, Thm. 7], using the current lower bounds for the codes PRM_q(d, m-1)
    and PRM_q(d-q+1, m-1).  Since the codes are treated by increasing m, these bounds are final when
    this rule reaches PRM_q(d, m), and a new value for a smaller code is automatically used here.

    The bound is computed for every r, also where the weight is already known: there it cannot
    improve anything, but generate.py then checks that it agrees with the known value.
    """
    # Thm. 7 needs 1 <= d <= m(q-1).  We use it for m >= 2: for m = 1 every weight is already known,
    # and the smaller codes PRM_q(., 0) are not in the tables.
    if m < 2 or d > m * (q - 1):
        return 0
    code = (q, d, m)
    PRM_d = table.lower_bounds(q, d, m - 1)                          # lower bounds for PRM_q(d, m-1)
    PRM_d_minus_q_plus_1 = table.lower_bounds(q, d - q + 1, m - 1)   # lower bounds for PRM_q(d-q+1, m-1)

    # The bound only depends on these two tuples.  This is the slowest rule, so if they are the same
    # as the last time that this rule was applied to this code, we do not compute it again (otherwise
    # the last pass of generate.py, which only confirms that nothing changes, would take twice as long).
    if table.recursive_inputs.get(code) == (PRM_d, PRM_d_minus_q_plus_1):
        return 0
    table.recursive_inputs[code] = (PRM_d, PRM_d_minus_q_plus_1)

    RM_d = affine_hierarchy(q, d, m)
    RM_d_minus_1 = affine_hierarchy(q, d - 1, m)
    changes = 0
    for r in range(2, dim_PRM(q, d, m) + 1):
        bound, alpha, gamma = recursive_lower_bound(q, d, m, r, PRM_d, PRM_d_minus_q_plus_1)
        reason = {"rule": "SJ24 Thm. 7", "alpha": alpha, "gamma": gamma,
                  # the four numbers in B_{alpha,gamma} at the pair attaining the minimum:
                  "RM_d": RM_d[r - gamma],                       # d_{r-gamma}(RM_q(d, m))
                  "RM_d_minus_1": RM_d_minus_1[r - alpha],       # d_{r-alpha}(RM_q(d-1, m))
                  "PRM_d": PRM_d[alpha],                         # bound for d_alpha(PRM_q(d, m-1))
                  "PRM_d_minus_q_plus_1": PRM_d_minus_q_plus_1[gamma]}   # bound for d_gamma(PRM_q(d-q+1, m-1))
        if bound == table.lower[code][r] and table.lower_reason[code][r]["rule"] == "SJ24 Thm. 7":
            # The same bound as before, but obtained from newer inputs: keep the explanation up to date.
            table.lower_reason[code][r] = reason
        else:
            changes += table.improve_lower(code, r, bound, reason)
    return changes


def computed_values(table, q, d, m):
    """Values computed outside this program (for instance with the GHWs package) or taken from the
    literature, read from data/manual.csv.  Each entry may give a lower bound, an upper bound, or both."""
    code = (q, d, m)
    changes = 0
    for entry in table.computed.get(code, []):   # the lines of data/manual.csv for this code (none if it has no line)
        reason = {"rule": "computed", "source": entry["source"], "note": entry["note"]}
        if entry["lower"] is not None:
            changes += table.improve_lower(code, entry["r"], entry["lower"], reason)
        if entry["upper"] is not None:
            changes += table.improve_upper(code, entry["r"], entry["upper"], reason)
    return changes


def wei_duality(table, q, d, m):
    """Wei duality ([SJ24, Thm. 9]): the current bounds for the weights of the dual code give bounds for
    this code, by the counting argument of wei_duality_bounds in formulas.py.  This is how [SJ24,
    Section V-C] improves the tables of the recursive bound (Example 6 and Tables VI-VIII there).

    The dual is PRM_q(e, m), with e = m(q-1) - d, if q-1 does not divide d, and PRM_q(e, m) plus the
    all-ones vector if q-1 divides d (see dual_degree).  In the second case, the bounds for PRM_q(e, m)
    first give bounds for the dual code, by bounds_after_adding_a_vector.  Since PRM_q(e, m) is also in
    the tables, the improvements go in both directions, and they also reach the recursive bound for
    the larger codes.
    """
    e = dual_degree(q, d, m)
    if e is None:
        return 0
    code = (q, d, m)
    n = p(q, m)
    k = dim_PRM(q, d, m)
    dual_lower, dual_upper = table.lower[q, e, m], table.upper[q, e, m]
    plus_ones = d % (q - 1) == 0                 # True if the dual is PRM_q(e, m) + <(1, ..., 1)>
    if plus_ones:
        dual_lower, dual_upper = bounds_after_adding_a_vector(n, dual_lower, dual_upper)
    lower, upper = wei_duality_bounds(n, k, dual_lower, dual_upper)
    changes = 0
    for r in range(1, k + 1):
        bound, w, count = lower[r]
        reason = {"rule": "Wei duality", "bound": "lower", "dual_degree": e, "plus_ones": plus_ones,
                  "w": w, "count": count}
        changes += table.improve_lower(code, r, bound, reason)
        bound, w, count = upper[r]
        reason = {"rule": "Wei duality", "bound": "upper", "dual_degree": e, "plus_ones": plus_ones,
                  "w": w, "count": count}
        changes += table.improve_upper(code, r, bound, reason)
    return changes


def fundamental_relation(table, q, d, m):
    """The fundamental relation (q^r - q) d_r >= (q^r - 1) d_{r-1} for every linear code ([HKLY95, Thm. 1],
    and [HKY92, Thm. 1] for q = 2), see fundamental_lower and fundamental_upper in formulas.py.  Lower
    bounds go upwards (d_r from d_{r-1}) and upper bounds downwards (d_r from d_{r+1}).  It contains the
    strict increase d_1 < d_2 < ... < d_k, so it also makes generate.py notice computed values that are
    impossible because they do not increase with r."""
    code = (q, d, m)
    k = dim_PRM(q, d, m)
    changes = 0
    for r in range(2, k + 1):                    # r = 2, ..., k: lower bounds, upwards
        previous = table.lower[code][r - 1]
        reason = {"rule": "fundamental relation", "from_r": r - 1, "from_bound": previous}
        changes += table.improve_lower(code, r, fundamental_lower(q, r, previous), reason)
    for r in range(k - 1, 0, -1):                # r = k-1, ..., 1: upper bounds, downwards
        following = table.upper[code][r + 1]
        reason = {"rule": "fundamental relation", "from_r": r + 1, "from_bound": following}
        changes += table.improve_upper(code, r, fundamental_upper(q, r, following), reason)
    return changes


def residual_code(table, q, d, m):
    """The residual code bound  n - d_r >= sum_{i=0}^{k-r-1} ceil((d_{r+1} - d_r) / q^i)  for every linear
    code ([HKLY95, proof of Thm. 4]), see residual_length in formulas.py.  Upper bounds go upwards
    (d_{r+1} from d_r, starting with d_0 = 0, which is the Griesmer bound) and lower bounds downwards
    (d_r from d_{r+1}).  The reason records the number that exceeds n, for the explanation."""
    code = (q, d, m)
    n = p(q, m)
    k = dim_PRM(q, d, m)
    changes = 0
    for r in range(0, k):                        # r = 0, ..., k-1: upper bounds for d_{r+1}, upwards
        previous = table.upper[code][r]          # for r = 0 this is d_0 = 0
        bound, total = residual_upper(q, n, k, r, previous)
        reason = {"rule": "residual code", "from_r": r, "from_bound": previous, "total": total}
        changes += table.improve_upper(code, r + 1, bound, reason)
    for r in range(k - 1, 0, -1):                # r = k-1, ..., 1: lower bounds for d_r, downwards
        following = table.lower[code][r + 1]
        bound, total = residual_lower(q, n, k, r, following)
        if total is not None:
            reason = {"rule": "residual code", "from_r": r + 1, "from_bound": following, "total": total}
            changes += table.improve_lower(code, r, bound, reason)
    return changes


# The rules used by generate.py, in this order.
RULES = [exact_values, upper_bound, recursive_bound, computed_values, wei_duality, fundamental_relation,
         residual_code]
