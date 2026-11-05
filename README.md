# Tables of generalized Hamming weights

Bounds and exact values for the generalized Hamming weights of projective Reed–Muller codes,
with a justification for every value, in the spirit of [codetables.de](https://www.codetables.de).

> **Status: work in progress.** Implemented and tested so far: the exact formulas and the upper
> bound ([`src/formulas.py`](src/formulas.py)). The lower bounds, the generator of the tables and
> the website are being written. The tables will be available at
> https://rodrigosanjose.github.io/ghw-tables/, and every release will be archived on Zenodo with a DOI.

## The codes

Let $q$ be a prime power and $m, d \ge 1$. The projective Reed–Muller code $\mathrm{PRM}_q(d,m)$
is obtained by evaluating the homogeneous polynomials of degree $d$ in $\mathbb{F}_q[X_0,\dots,X_m]$
at fixed representatives of the points of $\mathbb{P}^m(\mathbb{F}_q)$. Its length is
$p_m = 1 + q + \dots + q^m$ and we denote its dimension by $k_d(m)$.

The $r$-th generalized Hamming weight $d_r(C)$ of a linear code $C$ is the smallest support of an
$r$-dimensional subcode of $C$, and $d_1(C) < d_2(C) < \dots < d_k(C)$ is its weight hierarchy.
For each code in the range below, the tables give, for every $1 \le r \le k_d(m)$, an interval

```math
\text{lower} \;\le\; d_r(\mathrm{PRM}_q(d,m)) \;\le\; \text{upper},
```

which is a single number when the value is known. Each end of the interval comes with the result
(or computation) it follows from.

## Parameters covered

All degrees $1 \le d \le m(q-1)+1$ (for $d > m(q-1)$ the code is the whole space) and all $r$, for:

| $q$ | $m$ | largest length $p_m$ |
|---|---|---|
| 2 | 1, …, 9 | 1023 |
| 3 | 1, …, 6 | 1093 |
| 4 | 1, …, 4 | 341 |
| 5 | 1, …, 4 | 781 |
| 7 | 1, 2, 3 | 400 |
| 8 | 1, 2, 3 | 585 |
| 9 | 1, 2, 3 | 820 |

The range is set in [`src/parameters.py`](src/parameters.py) and will be extended.

## Where the bounds come from

Theorem numbers refer to the current version of [PRM]. Those of [SJ24] refer to arXiv:2312.05072v2.

### Exact values

| Range | Value | Source |
|---|---|---|
| $d < q$ | complete hierarchy | [PRM, Thm 1.1], conjectured by Beelen, Datta and Ghorpade [BDG22] |
| $(m-1)(q-1) < d < m(q-1)$ | complete hierarchy | [PRM, Cor 4.2]: Wei duality [Wei91] and Sørensen's description of the dual [Sør91] |
| $d = m(q-1)$ | $d_r = r + 1$ | the dual code is spanned by the all-ones vector [Sør91] |
| $d > m(q-1)$ | $d_r = r$ | the code is the whole space |
| $r = 1$ | minimum distance | [Sør91] |
| $d = 1 + t(q-1)$, or $d = 2 + t(q-1)$ with $q \ge 3$ | the first $m - t + 1$ weights | [PRM, Prop 6.12] |

For $d < q$, writing $(\mu_1, \dots, \mu_d)$ for the Macaulay tuple of $\binom{m+d}{d} - r$ in degree $d$,

```math
d_r(\mathrm{PRM}_q(d,m)) = p_m - p_{\mu_d} - \sum_{i=1}^{d-1} \lfloor q^{\mu_i} \rfloor .
```

In particular, the complete weight hierarchy is known for $m \le 2$.

### Upper bound, valid in every degree

By [PRM, Thm 6.7], for $1 \le r \le k_d(m)$,

```math
d_r(\mathrm{PRM}_q(d,m)) \;\le\; B_r(q,d,m) = p_m - \max\{\, 0 \le n \le p_m : h_d(n) \le k_d(m) - r \,\}.
```

Here $h_d(n)$ is the smaller of the Hilbert functions in degree $d$ of two explicit sets
$Z_n^-, Z_n^+ \subseteq \mathbb{P}^m(\mathbb{F}_q)$ with $n$ points, built by filling affine spaces and their
points at infinity. It is computed with the recursion of [PRM, Prop 6.6]. The bound comes from the
subcode of polynomials vanishing on the corresponding set. Equality holds for $d < q$, and
[PRM, Conj 6.9] states that it always holds.

### Lower bounds

* **Recursive bound** [SJ24, Thm 5.5]. It bounds $d_r(\mathrm{PRM}_q(d,m))$ from below in terms of the
  weights of the affine codes $\mathrm{RM}_q(d,m)$ and $\mathrm{RM}_q(d-1,m)$, known by Heijnen and Pellikaan [HP98],
  and lower bounds for $\mathrm{PRM}_q(d,m-1)$ and $\mathrm{PRM}_q(d-q+1,m-1)$. The tables use the best bounds
  available for these smaller codes, so any improvement for them propagates.
* **Consecutive weights.** If $D$ is a subcode attaining $d_{r+1}$, each coordinate of its support
  lies in the support of all but one of the hyperplanes of $D$. Counting gives
  ```math
  d_{r+1} \;\ge\; \left\lceil d_r \,\frac{q^{r+1}-1}{q^{r+1}-q} \right\rceil ,
  ```
  which raises lower bounds from $r$ to $r+1$; read backwards, it lowers upper bounds from $r+1$ to $r$.
* **Computations.** Values computed with the Sage package GHWs [GHWs], and values from the
  literature, each with its source and a way to reproduce it.

## How the tables are computed

Every bound above is a *rule*: it reads the current table and may raise a lower bound or lower an
upper bound, recording why. The generator starts from the trivial bounds
$r \le d_r \le p_m - k_d(m) + r$, applies all the rules, and repeats until a full pass improves
nothing. Every rule is monotone (better inputs never give worse outputs), so the final table does
not depend on the order in which the rules are applied. In particular, a new computed value is
automatically used by the recursive bound for all larger codes.

Everything is recomputed from scratch from the formulas and the file of computed values, and the
generator checks that every lower bound is at most the corresponding upper bound. A computed value
below $B_r(q,d,m)$ would be a counterexample to [PRM, Conj 6.9], and would be reported as such.

## Using the code

Only Python 3.9 or later is needed; there are no other dependencies. From the repository folder:

```
python3 -m unittest discover -s tests -v
```

runs the tests in a few seconds. They reproduce the examples and the computational checks of [PRM]:

* the formula of Thm 1.1 for $d < q$;
* Sørensen's minimum distance;
* Cor 4.2, Prop 6.12 and Lemma 6.10;
* the examples of Section 6.

The command

```
FULL_CHECK=1 python3 -m unittest discover -s tests -v
```

does the same for every prime power $q \le 9$ and $m \le 5$, as in [PRM], and takes about a minute.

The functions can also be used from Sage. Start Sage in the repository folder and run:

```
sage: load("src/formulas.py")
sage: B(3, 4, 3, 7)              # B_7(3, 4, 3)
16
sage: upper_bound_hierarchy(3, 3, 2)   # (B_1, ..., B_10) for PRM_3(3, 2)
(3, 4, 6, 7, 8, 9, 10, 11, 12, 13)
```

Every function implements one formula, named as in the papers, and its documentation gives the
precise reference. All computations use exact integers.

## References

* **[PRM]** R. San-José, *Common zeros of homogeneous polynomials and the weight hierarchy of
  projective Reed–Muller codes*, preprint (2026).
* **[SJ24]** R. San-José, *A recursive construction for projective Reed–Muller codes*,
  IEEE Trans. Inform. Theory 70(12) (2024), 8511–8523.
  [doi:10.1109/TIT.2024.3483998](https://doi.org/10.1109/tit.2024.3483998),
  [arXiv:2312.05072](https://arxiv.org/abs/2312.05072).
* **[GHWs]** R. San-José, *An algorithm for computing generalized Hamming weights and the Sage package GHWs*,
  ACM Trans. Math. Softw. 51(4) (2025). [doi:10.1145/3773284](https://doi.org/10.1145/3773284),
  [github.com/RodrigoSanJose/GHWs](https://github.com/RodrigoSanJose/GHWs).
* **[BDG22]** P. Beelen, M. Datta, S. R. Ghorpade, *A combinatorial approach to the number of solutions of
  systems of homogeneous polynomial equations over finite fields*, Moscow Math. J. 22(4) (2022), 565–593.
  [doi:10.17323/1609-4514-2022-22-4-565-593](https://doi.org/10.17323/1609-4514-2022-22-4-565-593),
  [arXiv:1807.01683](https://arxiv.org/abs/1807.01683).
* **[HP98]** P. Heijnen, R. Pellikaan, *Generalized Hamming weights of q-ary Reed–Muller codes*,
  IEEE Trans. Inform. Theory 44(1) (1998), 181–196.
* **[Sør91]** A. B. Sørensen, *Projective Reed–Muller codes*, IEEE Trans. Inform. Theory 37(6) (1991), 1567–1576.
* **[Wei91]** V. K. Wei, *Generalized Hamming weights for linear codes*,
  IEEE Trans. Inform. Theory 37(5) (1991), 1412–1418.
