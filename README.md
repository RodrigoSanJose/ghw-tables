# Tables of generalized Hamming weights

Bounds and exact values for the generalized Hamming weights of projective Reed–Muller codes,
with a justification for every value, in the spirit of [codetables.de](https://www.codetables.de).

> **Status: work in progress.** The tables will be available at
> https://rodrigosanjose.github.io/ghw-tables/, and every release will be archived on Zenodo with a DOI
> (see [Citation](#citation)).

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

## Where the bounds come from

Theorem numbers refer to the current version of [PRM] and to the published version of [SJ24].

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

* **Recursive bound** [SJ24, Thm 7]. It comes from the recursive construction of
  $\mathrm{PRM}_q(d,m)$ from $\mathrm{RM}_q(d-1,m)$ and $\mathrm{PRM}_q(d,m-1)$ [SJ24, Thm 4], and bounds
  $d_r(\mathrm{PRM}_q(d,m))$ from below by a minimum, over pairs $(\alpha,\gamma)$, of expressions
  involving two kinds of weights:
  * those of the affine codes $\mathrm{RM}_q(d,m)$ and $\mathrm{RM}_q(d-1,m)$, known by Heijnen and Pellikaan [HP98] (we use the form of [SJ24, Thm 6]);
  * those of the smaller codes $\mathrm{PRM}_q(d,m-1)$ and $\mathrm{PRM}_q(d-q+1,m-1)$.

  The tables use the best bounds available for these smaller codes, so any improvement for them
  propagates to the larger codes.
* **Computed values.** Values computed with the Sage package GHWs [GHWs], and values from the
  literature, listed in [`data/manual.csv`](data/manual.csv) with their source.

## How the tables are computed

Every source above is a *rule*: it looks at one code, proposes bounds, and records why. The generator:

1. starts from the trivial bounds $r \le d_r \le p_m$;
2. applies all the rules to all the codes, by increasing $m$;
3. repeats step 2 until a full pass improves nothing.

A rule can only raise a lower bound or lower an upper bound, and the result of every rule can only
improve when its inputs improve. Hence the final tables do not depend on the order in which the
rules are applied, and a new computed value is automatically used by the recursive bound for all
the larger codes.

Everything is recomputed from scratch from the formulas and `data/manual.csv`. The generator stops
if some lower bound is larger than the corresponding upper bound, which would reveal a wrong value
or a bug. An upper bound below $B_r(q,d,m)$ would be a counterexample to [PRM, Conj 6.9]; the generator
reports it as such.

## Adding a computed value

Add a line to [`data/manual.csv`](data/manual.csv), with the columns

```
q,d,m,r,lower,upper,source,note
3,4,3,7,16,16,GHWs,"Computed with the GHWs package, see [PRM, Section 6.3]."
```

* Leave `lower` (or `upper`) empty if the computation only gives an upper (or a lower) bound.
* `source` is a key of [`data/references.csv`](data/references.csv).
* `note` says how to reproduce the value.

Then run the generator, read its report, and commit the changes.

## Using the code

Only Python 3.9 or later is needed; there are no other dependencies. From the repository folder:

```
python3 src/generate.py                        # compute the tables (about a minute)
python3 -m unittest discover -s tests -v       # run the tests (a few seconds)
FULL_CHECK=1 python3 -m unittest discover -s tests -v
```

The tests reproduce the examples and the computational checks of [PRM]:

* the formula of Thm 1.1 for $d < q$, Sørensen's minimum distance, Cor 4.2, Prop 6.12, Lemma 6.10 and Cor 5.2;
* the examples of Section 6, and the remark verifying Conj 6.9 for $q = 3$, $m = 3$.

They also reproduce the examples of [SJ24, Section V] and every entry of [SJ24, Tables II–V]. With
`FULL_CHECK=1`, the checks of [PRM] run for every prime power $q \le 9$ and every $m \le 5$, which takes
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
| [`data/references.csv`](data/references.csv) | the references |
| [`tests/`](tests) | the tests |
| [`docs/`](docs) | the website; `docs/data/` is generated, never edit it by hand |
| [`CITATION.cff`](CITATION.cff) | how to cite the tables (used by GitHub and Zenodo) |
| [`LICENSE`](LICENSE), [`LICENSE-CC-BY-4.0.txt`](LICENSE-CC-BY-4.0.txt) | the licenses (see below) |

## Citation

If you use these tables, please consider citing them and the paper [PRM] where the bounds are proved.

> [!NOTE]
> The tables will be archived on Zenodo with the first release. The DOI below, `10.5281/zenodo.XXXXXXX`,
> is a placeholder until then.

### Citation for the tables
```
@Misc{ghwTables,
    AUTHOR = {San-Jos\'{e}, Rodrigo},
    TITLE = {Tables of generalized {H}amming weights of projective {R}eed--{M}uller codes},
    year = "2026",
    publisher = "Zenodo",
    doi = "10.5281/zenodo.XXXXXXX",
    howpublished = "Available online: \url{https://rodrigosanjose.github.io/ghw-tables/}"
}
```

### Citation for the paper
```
@Misc{sanjoseCommonZeros,
    AUTHOR = {San-Jos\'{e}, Rodrigo},
    TITLE = {Common zeros of homogeneous polynomials and the weight hierarchy of projective {R}eed--{M}uller codes},
    year = "2026",
    note = "Preprint"
}
```

## License

* The code (the folders `src/` and `tests/`, and the files `docs/ghw.js`, `docs/ghw.css` and `docs/index.html`)
  is released under the [MIT license](LICENSE).
* The tables (`docs/data/`), the data (`data/`) and the documentation (this README and the texts of the website)
  are released under the [Creative Commons Attribution 4.0 International license](LICENSE-CC-BY-4.0.txt) (CC BY 4.0).

The website uses the style of https://rodrigosanjose.github.io, which is based on
[Strata](https://html5up.net/strata) by HTML5 UP.

## References

* **[PRM]** R. San-José, *Common zeros of homogeneous polynomials and the weight hierarchy of
  projective Reed–Muller codes*, preprint (2026).
* **[SJ24]** R. San-José, *A recursive construction for projective Reed–Muller codes*,
  IEEE Trans. Inform. Theory 70(12) (2024), 8511–8523.
  [doi:10.1109/TIT.2024.3483998](https://doi.org/10.1109/TIT.2024.3483998).
* **[GHWs]** R. San-José, *An algorithm for computing generalized Hamming weights and the Sage package GHWs*,
  ACM Trans. Math. Softw. 51(4) (2025). [doi:10.1145/3773284](https://doi.org/10.1145/3773284),
  [github.com/RodrigoSanJose/GHWs](https://github.com/RodrigoSanJose/GHWs).
* **[BDG22]** P. Beelen, M. Datta, S. R. Ghorpade, *A combinatorial approach to the number of solutions of
  systems of homogeneous polynomial equations over finite fields*, Moscow Math. J. 22(4) (2022), 565–593.
  [doi:10.17323/1609-4514-2022-22-4-565-593](https://doi.org/10.17323/1609-4514-2022-22-4-565-593).
* **[HP98]** P. Heijnen, R. Pellikaan, *Generalized Hamming weights of q-ary Reed–Muller codes*,
  IEEE Trans. Inform. Theory 44(1) (1998), 181–196.
* **[Sør91]** A. B. Sørensen, *Projective Reed–Muller codes*, IEEE Trans. Inform. Theory 37(6) (1991), 1567–1576.
* **[Wei91]** V. K. Wei, *Generalized Hamming weights for linear codes*,
  IEEE Trans. Inform. Theory 37(5) (1991), 1412–1418.
