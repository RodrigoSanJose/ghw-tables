"""The codes PRM_q(d, m) included in the tables."""

# For each field size q, the largest m included (lengths p_m up to 4369).
MAX_M = {2: 8, 3: 6, 4: 5, 5: 4, 7: 4, 8: 3, 9: 3, 11: 3, 13: 3, 16: 3}


def codes(max_m=MAX_M):
    """The list of all (q, d, m) with 1 <= m <= max_m[q] and 1 <= d <= m(q-1) + 1.

    For d > m(q-1) the code is the whole space, so larger degrees give nothing new.
    """
    result = []
    for q, largest_m in max_m.items():
        for m in range(1, largest_m + 1):
            for d in range(1, m * (q - 1) + 2):
                result.append((q, d, m))
    return result
