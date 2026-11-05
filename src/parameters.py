"""The codes PRM_q(d, m) included in the tables."""

# For each field size q, the largest m included (lengths p_m up to about 1100).
MAX_M = {2: 9, 3: 6, 4: 4, 5: 4, 7: 3, 8: 3, 9: 3}


def codes(max_m=MAX_M):
    """All (q, d, m) with 1 <= m <= max_m[q] and 1 <= d <= m(q-1) + 1.

    For d > m(q-1) the code is the whole space, so larger degrees give nothing new.
    """
    for q, top in max_m.items():
        for m in range(1, top + 1):
            for d in range(1, m * (q - 1) + 2):
                yield q, d, m
