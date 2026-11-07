# Tables of generalized Hamming weights

Bounds and exact values for the generalized Hamming weights of projective Reed–Muller codes,
with a justification for every value, in the spirit of [codetables.de](https://www.codetables.de).

**The tables are available at [https://rodrigosanjose.github.io/ghw-tables/](https://rodrigosanjose.github.io/ghw-tables/)**, and every release is archived on Zenodo, [doi:10.5281/zenodo.24020768](https://doi.org/10.5281/zenodo.24020768) (see [Citation](#citation)).

## The codes

Let $q$ be a prime power and $m, d \ge 1$. The projective Reed–Muller code $\mathrm{PRM}_q(d,m)$
is obtained by evaluating the homogeneous polynomials of degree $d$ in $\mathbb{F}_q[X_0,\dots,X_m]$
at fixed representatives of the points of $\mathbb{P}^m(\mathbb{F}_q)$. Its length is
$p_m = 1 + q + \dots + q^m$ and we denote its dimension by $k_d(m)$.

The $r$-th generalized Hamming weight $d_r(C)$ of a linear code $C$ is the smallest support of an
$r$-dimensional subcode of $C$, and $d_1(C) < d_2(C) < \dots < d_k(C)$ is its weight hierarchy.
For each code in the range below, the tables give, for every $1 \le r \le k_d(m)$, an interval

$$
\text{lower} \;\le\; d_r(\mathrm{PRM}_q(d,m)) \;\le\; \text{upper},
$$

which is a single number when the value is known. Each end of the interval comes with the result
(or computation) it follows from.

## Parameters covered

All degrees $1 \le d \le m(q-1)+1$ (for $d > m(q-1)$ the code is the whole space) and all $r$, for:

| $q$ | $m$ | largest length $p_m$ |
|---|---|---|
| 2 | 1, …, 8 | 511 |
| 3 | 1, …, 6 | 1093 |
| 4 | 1, …, 4 | 341 |
| 5 | 1, …, 4 | 781 |
| 7 | 1, 2, 3 | 400 |
| 8 | 1, 2, 3 | 585 |
| 9 | 1, 2, 3 | 820 |

For $q = 2$ every weight is known exactly. In that case $\mathrm{PRM}_2(d,m)$ is
$\mathrm{RM}_2(d,m+1)$ shortened at the origin.

## Where the bounds come from

Theorem numbers refer to [SJ26] ([arXiv:2611.08203v1](https://arxiv.org/abs/2611.08203v1)) and to the
published version of [SJ24].

### Exact values

| Range | Value | Source |
|---|---|---|
| $d < q$ | complete hierarchy | [SJ26, Thm. 1.1], conjectured by Beelen, Datta and Ghorpade [BDG22] |
| $(m-1)(q-1) < d < m(q-1)$ | complete hierarchy | [SJ26, Cor. 4.2]: Wei duality [Wei91] and Sørensen's description of the dual [Sør91] |
| $d = m(q-1)$ | $d_r = r + 1$ | the dual code is spanned by the all-ones vector [Sør91] |
| $d > m(q-1)$ | $d_r = r$ | the code is the whole space |
| $r = 1$ | minimum distance | [Sør91] |
| $d = 1 + t(q-1)$, or $d = 2 + t(q-1)$ with $q \ge 3$ | the first $m - t + 1$ weights | [SJ26, Prop. 6.12] |

For $d < q$, writing $(\mu_1, \dots, \mu_d)$ for the Macaulay tuple of $\binom{m+d}{d} - r$ in degree $d$,

$$
d_r(\mathrm{PRM}_q(d,m)) = p_m - p_{\mu_d} - \sum_{i=1}^{d-1} \lfloor q^{\mu_i} \rfloor .
$$

In particular, the complete weight hierarchy is known for $m \le 2$.

### Upper bound, valid in every degree

By [SJ26, Thm. 6.7], for $1 \le r \le k_d(m)$,

$$
d_r(\mathrm{PRM}_q(d,m)) \;\le\; B_r(q,d,m) = p_m - \max\{\, 0 \le n \le p_m : h_d(n) \le k_d(m) - r \,\}.
$$

Here $h_d(n)$ is the smaller of the Hilbert functions in degree $d$ of two explicit sets
$Z_n^-, Z_n^+ \subseteq \mathbb{P}^m(\mathbb{F}_q)$ with $n$ points, built by filling affine spaces and their
points at infinity. It is computed with the recursion of [SJ26, Prop. 6.6]. The bound comes from the
subcode of polynomials vanishing on the corresponding set. Equality holds for $d < q$, and
[SJ26, Conj. 6.9] states that it always holds.

### Lower bounds

* **Recursive bound** [SJ24, Thm. 7]. It comes from the recursive construction of
  $\mathrm{PRM}_q(d,m)$ from $\mathrm{RM}_q(d-1,m)$ and $\mathrm{PRM}_q(d,m-1)$ [SJ24, Thm. 4], and bounds
  $d_r(\mathrm{PRM}_q(d,m))$ from below by a minimum, over pairs $(\alpha,\gamma)$, of expressions
  involving two kinds of weights:
  * those of the affine codes $\mathrm{RM}_q(d,m)$ and $\mathrm{RM}_q(d-1,m)$, known by Heijnen and Pellikaan [HP98] (we use the form of [SJ24, Thm. 6]);
  * those of the smaller codes $\mathrm{PRM}_q(d,m-1)$ and $\mathrm{PRM}_q(d-q+1,m-1)$.

  The tables use the best bounds available for these smaller codes, so any improvement for them
  propagates to the larger codes.
* **Duality** [Wei91; SJ24, Thm. 9], as in [SJ24, Section V-C]. Let $1 \le d \le m(q-1)-1$ and
  $e = m(q-1)-d$. The dual of $\mathrm{PRM}_q(d,m)$ is $\mathrm{PRM}_q(e,m)$ if $q-1$ does not divide $d$, and
  $\mathrm{PRM}_q(e,m) + \langle (1,\dots,1) \rangle$ if it does [Sør91]. In the second case, a subspace of the
  dual of dimension $s$ meets $\mathrm{PRM}_q(e,m)$ in dimension at least $s-1$, so

  $$
  d_{s-1}(\mathrm{PRM}_q(e,m)) \le d_s(\mathrm{PRM}_q(d,m)^\perp) \le d_s(\mathrm{PRM}_q(e,m)).
  $$

  Either way, the bounds for $\mathrm{PRM}_q(e,m)$, which is also in the tables, give bounds for the
  weights of the dual. Let $N(w)$ be the number of weights of a code $C$ of length $n$ and dimension $k$
  that are at most $w$. Wei duality gives

  $$
  N(w) = w - (n - k) + \#\{\, s : d_s(C^\perp) \le n - w \,\},
  $$

  so the bounds for the weights of the dual give lower and upper bounds for $N(w)$, and hence for the
  weights of $C$. This applies to all the bounds above, in both directions, and the improved bounds
  are also used by the recursive bound for the larger codes. ([SJ24, Section V-C] uses the first case;
  the second one is new here.)
* **Classical bounds**, valid for every linear code of length $n$ (here $n = p_m$) and dimension $k$
  over $\mathbb{F}_q$, each one used in both directions:
  * the case $s = r - 1$ of [HKLY95, Thm. 1] ([HKY92, Thm. 1] for $q = 2$),

    $$
    (q^r - q)\, d_r \ge (q^r - 1)\, d_{r-1}, \qquad 2 \le r \le k,
    $$

    which gives lower bounds for $d_r$ from those of $d_{r-1}$, and upper bounds for $d_{r-1}$ from
    those of $d_r$;
  * the bound (from the proof of [HKLY95, Thm. 4])

    $$
    n - d_r \ge \sum_{i=0}^{k-r-1} \left\lceil \frac{d_{r+1} - d_r}{q^i} \right\rceil, \qquad 0 \le r \le k-1.
    $$

  These two contain the other bounds of [Wei91], [HKY92] and [HKLY95] that can be evaluated from
  bounds for the weights, so these are not applied separately:
  * the strict increase $d_{r-1} < d_r$ [Wei91, Thm. 1; SJ24, Thm. 5], since $(q^r - 1)/(q^r - q) > 1$;
  * the other cases of [HKLY95, Thm. 1], [HKLY95, Cor. 1], and the Griesmer-type lower bound
    $d_r \ge \sum_{i=0}^{r-1} \lceil d_1/q^i \rceil$ ([Wei91, Thm. 4 and Lemma 1], there for $q = 2$), which
    follow by iterating the bound of [HKLY95, Thm. 1] upwards;
  * the generalized Singleton bound $d_r \le n - k + r$ [Wei91, Cor. 1], the Plotkin-type bound
    [HKLY95, Thm. 2] and the generalized Griesmer bound [HKLY95, Thm. 4] ([HKY92, Thm. 5] for $q = 2$),
    which follow by iterating the bound of [HKLY95, Thm. 1] downwards from $d_k \le n$;
  * [HKY92, Thm. 9], whose proof works over every field, and whose form over $\mathbb{F}_q$ is the bound
    from the proof of [HKLY95, Thm. 4] with the ceilings omitted.

* **Computed values.** Values computed with the Sage package GHWs [SJ25], and values from the
  literature, listed in [`data/manual.csv`](data/manual.csv) with their source.

## How the tables are computed

Every source above is a *rule*: it looks at one code, proposes bounds, and records why. The generator:

1. starts from the trivial bounds $r \le d_r \le p_m$;
2. applies all the rules to all the codes, by increasing $m$;
3. repeats step 2 until a full pass changes nothing.

A rule can only raise a lower bound or lower an upper bound, and the result of every rule can only
improve when its inputs improve. Hence the final tables do not depend on the order in which the
rules are applied, and a new computed value is automatically used by the recursive bound for all
the larger codes, and by duality and the classical bounds.

Everything is recomputed from scratch from the formulas and `data/manual.csv`. The generator stops
if some lower bound is larger than the corresponding upper bound, which would reveal a wrong value
or a bug; since the bound of [HKLY95, Thm. 1] implies the strict monotonicity of the weights, this
includes computed values that do not increase with $r$. The recursive bound is also computed where
the weight is already known, so it checks the exact values too.
An upper bound below $B_r(q,d,m)$ would be a counterexample to [SJ26, Conj. 6.9]; the generator reports it
as such.

## Adding a computed value

Add a line to [`data/manual.csv`](data/manual.csv), with the columns

```
q,d,m,r,lower,upper,source,note
3,4,3,7,16,16,SJ25,"Also given in [SJ26, Section 6.3]."
```

* Leave `lower` (or `upper`) empty if the computation only gives an upper (or a lower) bound.
* `source` is a key of [`data/references.csv`](data/references.csv).
* `note` says how to reproduce the value. Write it between double quotes if it contains a comma.

Then run the generator, read its report, and commit the changes. If a line is not valid, the
generator stops and says which line it is.

### Computing values with GHWs

[`sage/compute.py`](sage/compute.py) computes weights with the GHWs package [SJ25] and prints the lines
to add to `data/manual.csv`. It is the only file that needs SageMath, and nothing else depends on it.
With SageMath and GHWs installed, from the repository folder:

```
sage -python sage/compute.py 4 4 3        # the weights of PRM_4(4,3) that are not known in the tables
sage -python sage/compute.py 4 4 3 7      # only d_7(PRM_4(4,3))
sage -python sage/compute.py 3 4 3 all    # all the weights of PRM_3(4,3), to compare them with the tables
```

When $d_r$ is not known, the tables give $a \le d_r \le b$ with $a < b$ and $b \le B_r(q,d,m)$, and
[SJ26, Conj. 6.9] says that $d_r = B_r(q,d,m)$. So the script first asks `GHW_bound` whether $d_r \ge b$,
which is usually much faster than computing $d_r$. If the answer is yes, then $d_r = b$, and the line
for `data/manual.csv` only gives the lower bound $b$ (the upper bound is already in the tables). If the
answer is no, the script computes $d_r$ with `GHW`, and reports a counterexample to the conjecture.

## Using the code

Only Python 3.9 or later is needed; there are no other dependencies (SageMath is only needed to
compute new values, see above). From the repository folder:

```
python3 src/generate.py                        # compute the tables (about a minute and a half)
python3 -m unittest discover -s tests -v       # run the tests (a few seconds)
FULL_CHECK=1 python3 -m unittest discover -s tests -v
```

The tests reproduce the examples and the computational checks of [SJ26]:

* the formula of Thm. 1.1 for $d < q$, Sørensen's minimum distance, Cor. 4.2, Prop. 6.12, Lemma 6.10 and Cor. 5.2;
* the examples of Section 6, and the remark verifying Conj. 6.9 for $q = 3$, $m = 3$.

They also reproduce Examples 2–5 of [SJ24], and the value of [SJ24, Thm. 7] at every entry of
[SJ24, Tables II–V]: the exact value, or the lower end $a$ of the entries $a$–$b$. They reproduce
[SJ24, Example 6] too: duality and monotonicity turn the row $d = 3$ of [SJ24, Table III] into the exact
values of [SJ24, Table VI]. They also check by brute force, on random binary codes, the inequalities
used for duality when $q-1$ divides $d$. With
`FULL_CHECK=1`, the checks of [SJ26] run for every prime power $q \le 9$ and every $m \le 5$, which takes
about a minute.

The functions can also be used from Sage. Start Sage in the repository folder and run:

```
sage: load("src/formulas.py")
sage: B(3, 4, 3, 7)                    # B_7(3, 4, 3)
16
sage: upper_bound_hierarchy(3, 3, 2)   # (0, B_1, ..., B_10) for PRM_3(3, 2)
(0, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13)
```

A weight hierarchy is always stored as $(0, d_1, \dots, d_k)$, so that position $r$ holds $d_r$.

## Files

| File | Contents |
|---|---|
| [`src/formulas.py`](src/formulas.py) | every formula, one function each, with the reference |
| [`src/rules.py`](src/rules.py) | the rules that fill the tables |
| [`src/table.py`](src/table.py) | the table of bounds and their reasons |
| [`src/generate.py`](src/generate.py) | computes the tables, checks them, writes `docs/data/` |
| [`src/parameters.py`](src/parameters.py) | the codes in the tables |
| [`data/manual.csv`](data/manual.csv) | computed values and values from the literature |
| [`sage/compute.py`](sage/compute.py) | computes weights with GHWs, for `data/manual.csv` (needs SageMath) |
| [`data/references.csv`](data/references.csv) | the references |
| [`tests/`](tests) | the tests |
| [`docs/`](docs) | the website; `docs/data/` is generated, never edit it by hand |
| [`CITATION.cff`](CITATION.cff) | how to cite the tables (used by GitHub and Zenodo) |
| [`LICENSE`](LICENSE), [`LICENSE-CC-BY-4.0.txt`](LICENSE-CC-BY-4.0.txt) | the licenses (see below) |

## Citation

If you use these tables, please consider citing them and the papers [SJ24,SJ26] where the main bounds are proved.

The tables are archived on Zenodo with the DOI
[10.5281/zenodo.24020768](https://doi.org/10.5281/zenodo.24020768), which always points to the latest version.

### Citation for the tables
```
@misc{sanjoseGHWTables,
  author       = {San-Jos{\'e}, Rodrigo},
  title        = {Tables of generalized {H}amming weights of
                  projective {Reed--Muller} codes},
  year         = {2026},
  howpublished = {Zenodo},
  note         = {Interactive tables:
                  \url{https://rodrigosanjose.github.io/ghw-tables/}.
                  Permanent DOI:
                  \url{https://doi.org/10.5281/zenodo.24020768}}
}
```

## License

* The code (the folders `src/` and `tests/`, and the files `docs/ghw.js`, `docs/ghw.css` and `docs/index.html`)
  is released under the [MIT license](LICENSE).
* The tables (`docs/data/`), the data (`data/`) and the documentation (this README and the texts of the website)
  are released under the [Creative Commons Attribution 4.0 International license](LICENSE-CC-BY-4.0.txt) (CC BY 4.0).

## References

* **[BDG22]** P. Beelen, M. Datta, S. R. Ghorpade, *A combinatorial approach to the number of solutions of
  systems of homogeneous polynomial equations over finite fields*, Moscow Math. J. 22(4) (2022), 565–593.
  [doi:10.17323/1609-4514-2022-22-4-565-593](https://doi.org/10.17323/1609-4514-2022-22-4-565-593).
* **[HP98]** P. Heijnen, R. Pellikaan, *Generalized Hamming weights of q-ary Reed–Muller codes*,
  IEEE Trans. Inform. Theory 44(1) (1998), 181–196. [doi:10.1109/18.651015](https://doi.org/10.1109/18.651015).
* **[HKLY95]** T. Helleseth, T. Kløve, V. I. Levenshtein, Ø. Ytrehus, *Bounds on the minimum support weights*,
  IEEE Trans. Inform. Theory 41(2) (1995), 432–440. [doi:10.1109/18.370144](https://doi.org/10.1109/18.370144).
* **[HKY92]** T. Helleseth, T. Kløve, Ø. Ytrehus, *Generalized Hamming weights of linear codes*,
  IEEE Trans. Inform. Theory 38(3) (1992), 1133–1140. [doi:10.1109/18.135655](https://doi.org/10.1109/18.135655).
* **[SJ24]** R. San-José, *A recursive construction for projective Reed–Muller codes*,
  IEEE Trans. Inform. Theory 70(12) (2024), 8511–8523.
  [doi:10.1109/TIT.2024.3483998](https://doi.org/10.1109/TIT.2024.3483998).
* **[SJ25]** R. San-José, *An algorithm for computing generalized Hamming weights and the Sage package GHWs*,
  ACM Trans. Math. Softw. 51(4) (2025). [doi:10.1145/3773284](https://doi.org/10.1145/3773284),
  [github.com/RodrigoSanJose/GHWs](https://github.com/RodrigoSanJose/GHWs).
* **[SJ26]** R. San-José, *Common zeros of homogeneous polynomials and the weight hierarchy of
  projective Reed–Muller codes*, arXiv:2611.08203 (2026).
  [doi:10.48550/arXiv.2611.08203](https://doi.org/10.48550/arXiv.2611.08203).
* **[Sør91]** A. B. Sørensen, *Projective Reed–Muller codes*, IEEE Trans. Inform. Theory 37(6) (1991), 1567–1576.
  [doi:10.1109/18.104317](https://doi.org/10.1109/18.104317).
* **[Wei91]** V. K. Wei, *Generalized Hamming weights for linear codes*,
  IEEE Trans. Inform. Theory 37(5) (1991), 1412–1418. [doi:10.1109/18.133259](https://doi.org/10.1109/18.133259).
