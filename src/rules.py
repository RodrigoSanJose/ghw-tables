"""
The rules used to fill the table.

Each rule looks at one code PRM_q(d, m), proposes bounds for its weights together with the reason,
and returns how many bounds it improved.  A rule can only raise a lower bound or lower an upper
bound (see Table.improve_lower and Table.improve_upper), so the order of the rules does not matter
for the final table.  It only matters for the credit: when two rules give the same bound, the one
applied first keeps it.

The list RULES at the end of this file is the list of rules that generate.py uses.
"""

from formulas import (affine_hierarchy, attaining_set, dim_PRM, known_hierarchy, largest_point_sets,
                      lifted_weights, macaulay, binom, p, recursive_lower_bound,
                      sorensen_minimum_distance)


def exact_values(table, q, d, m):
    """Exact values: the complete hierarchy when it is known ([PRM, Thm 1.1] for d < q, [PRM, Cor. 4.2]
    for (m-1)(q-1) < d < m(q-1), and the large degrees d >= m(q-1)); the minimum distance
    (Sorensen); and the first weights given by [PRM, Prop. 6.12]."""
    code = (q, d, m)
    changes = 0

    H, result = known_hierarchy(q, d, m)
    if H is not None:
        for r in range(1, len(H)):
            if result == "PRM Thm 1.1":
                reason = {"rule": result, "mu": macaulay(binom(m + d, d) - r, d)}
            elif result == "PRM Cor 4.2":
                reason = {"rule": result, "dual_degree": m * (q - 1) - d}
            elif d > m * (q - 1):
                reason = {"rule": "whole space"}
            else:
                reason = {"rule": "dual is all-ones"}       # d = m(q-1)
            changes += table.improve_lower(code, r, H[r], reason)
            changes += table.improve_upper(code, r, H[r], reason)

    d1 = sorensen_minimum_distance(q, d, m)
    changes += table.improve_lower(code, 1, d1, {"rule": "Sorensen"})
    changes += table.improve_upper(code, 1, d1, {"rule": "Sorensen"})

    for r, value in lifted_weights(q, d, m).items():
        reason = {"rule": "PRM Prop 6.12"}
        changes += table.improve_lower(code, r, value, reason)
        changes += table.improve_upper(code, r, value, reason)
    return changes


def upper_bound(table, q, d, m):
    """The upper bound B_r(q, d, m) = p_m - n of [PRM, Thm 6.7], where n is the largest integer with
    h_d(n) <= k_d(m) - r.  The reason records n and which of the sets Z_n^-, Z_n^+ is used."""
    code = (q, d, m)
    k = dim_PRM(q, d, m)
    N = largest_point_sets(q, d, m)        # N[v] = max{ n : h_d(n) <= v }
    changes = 0
    for r in range(1, k + 1):
        n = N[k - r]
        reason = {"rule": "PRM Thm 6.7", "n": n, "set": attaining_set(q, d, n)}
        changes += table.improve_upper(code, r, p(q, m) - n, reason)
    return changes


def recursive_bound(table, q, d, m):
    """The lower bound of [SJ24, Thm 7], using the current lower bounds for the codes PRM_q(d, m-1)
    and PRM_q(d-q+1, m-1).  Since the codes are treated by increasing m, these bounds are final when
    this rule reaches PRM_q(d, m), and a new value for a smaller code is automatically used here."""
    if m < 2 or d > m * (q - 1):          # Thm 7 needs m >= 2 and 1 <= d <= m(q-1)
        return 0
    code = (q, d, m)
    same_degree = table.lower_bounds(q, d, m - 1)
    lower_degree = table.lower_bounds(q, d - q + 1, m - 1)

    # The bound only depends on these two tuples.  If they are the same as the last time that this
    # rule was applied to this code, it cannot give anything new, so we save the work.
    if table.recursive_inputs.get(code) == (same_degree, lower_degree):
        return 0
    table.recursive_inputs[code] = (same_degree, lower_degree)

    RM_d = affine_hierarchy(q, d, m)
    RM_d_minus_1 = affine_hierarchy(q, d - 1, m)
    changes = 0
    for r in range(2, dim_PRM(q, d, m) + 1):
        if table.is_exact(code, r):
            continue                      # nothing left to improve
        bound, alpha, gamma = recursive_lower_bound(q, d, m, r, same_degree, lower_degree)
        reason = {"rule": "SJ24 Thm 7", "alpha": alpha, "gamma": gamma,
                  # the four numbers in B_{alpha,gamma} at the pair attaining the minimum:
                  "RM_d": RM_d[r - gamma],                    # d_{r-gamma}(RM_q(d, m))
                  "RM_d_minus_1": RM_d_minus_1[r - alpha],    # d_{r-alpha}(RM_q(d-1, m))
                  "same_degree": same_degree[alpha],          # bound for d_alpha(PRM_q(d, m-1))
                  "lower_degree": lower_degree[gamma]}        # bound for d_gamma(PRM_q(d-q+1, m-1))
        changes += table.improve_lower(code, r, bound, reason)
    return changes


def computed_values(table, q, d, m):
    """Values computed outside this program (for instance with the GHWs package) or taken from the
    literature, read from data/manual.csv.  Each entry may give a lower bound, an upper bound, or both."""
    code = (q, d, m)
    changes = 0
    for entry in table.computed.get(code, []):
        reason = {"rule": "computed", "source": entry["source"], "note": entry["note"]}
        if entry["lower"] is not None:
            changes += table.improve_lower(code, entry["r"], entry["lower"], reason)
        if entry["upper"] is not None:
            changes += table.improve_upper(code, entry["r"], entry["upper"], reason)
    return changes


# The rules used by generate.py, in this order.
RULES = [exact_values, upper_bound, recursive_bound, computed_values]
