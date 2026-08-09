# Stage W5 results (revised)

> The W5 workload tests whether BT-IS's first-class rotor
> registers (`load_r`, `rot_*_r`, `reflect_*_r`, `neg_r`,
> `apply_r`) give an instruction-count advantage on a workload
> that exercises the cube's symmetry group structure.

## What was actually run

The original W5 (`programs/w5_compose.btis`) was a single
7-term composition, not the canonicalization flagship
described in `docs/PLAN_6_STEPS_STATUS.md:45-58`. The
PLAN-recommended workload was:

> Apply all 48 elements of $O_h$ to a 3×3×3 pattern; pick
> the lex-minimum configuration.

That workload was never implemented. The previous W5
results claimed a 1.50× loss for BT-IS on a 7-term composition;
this is *not* the canonicalization experiment.

This commit implements the inner loop of canonicalization
on a single cube (the cell-application step):

> For each of the 48 $O_h$ permutations, apply it to
> $(1, 0, 0)$ and emit the result. The orbit of $(1, 0, 0)$
> under $O_h$ is the 6 axial states $\{\pm X, \pm Y, \pm Z\}$,
> each appearing 8 times (48 / 6 = 8).

The full canonicalization algorithm (apply 48 group elements
to all 27 cells of a 3×3×3 pattern) is 27× this inner loop
on both architectures. Since both BT-IS `apply_r` and
SCALAR `APPLY_PERM` are 1 op per application, the per-cell
ratio is 1:1 and the 27× outer factor doesn't change it. The
discriminating question for the inner loop is *setup cost*:
how many ops does each architecture pay to load a permutation
into a register?

## The 48 $O_h$ permutations

Generated in `benchmarks/w5_canon/oh.py`. The 24 proper
rotations are built from the standard octahedral group tables:

- Identity
- 9 axis 90°/180°/270° rotations (3 axes × 3 angles)
- 6 face-diagonal 180° rotations
- 8 body-diagonal 120°/240° rotations (4 axes × 2 angles)

The 24 improper rotations are each proper rotation composed
with inversion.

The 8 body-diagonal rotations are derived by conjugating
the 120° rotation around (1,1,1) with the axis-aligned
reflections that map (1,1,1) to the target body-diagonal
axis. This is necessary because a 120° rotation around
(-1,1,1) cannot be expressed as a simple cycle in
(x, y, z) coordinates; it is the (1,1,1) cycle composed
with REFLECT_X.

`benchmarks/w5_canon/verify.py` asserts the 48 permutations:

- Each is a bijection on {0, ..., 26}.
- Their inverses are in the set.
- They are closed under composition over all 48² = 2304 pairs.
- Negation maps the proper 24 to the improper 24.

## Factoring permutations into BT-IS rotor ops

Each BT-IS `rot_*_r`, `reflect_*_r`, `neg_r` instruction
post-composes its named permutation onto a rotor register.
So to load a target permutation `p` into R0 starting from
identity, we need a sequence of generators
`g_1, g_2, ..., g_k` such that
`g_k ∘ ... ∘ g_2 ∘ g_1 = p`. The sequence length `k` is
the setup cost.

`benchmarks/w5_canon/factor.py` does a BFS over the 13
generators (9 axis rotations + 3 reflections + 1 negation)
and finds the minimum sequence for each of the 48 $O_h$
elements. Maximum sequence length: **3 instructions**.

For example:

| Permutation | Factor | Length |
|---|---|---|
| `I` (identity) | (none) | 0 |
| `Rx90` | `rot_x_90_r` | 1 |
| `Rxy180` (face-diagonal 180° around (1,1,0)) | `rot_x_180_r, rot_z_90_r` | 2 |
| `R111_120` (body-diagonal 120° around (1,1,1)) | `rot_x_90_r, rot_z_90_r` | 2 |
| `iR111_120` (improper body-diagonal) | `rot_x_90_r, rot_z_90_r, neg_r` | 3 |

## Results

| implementation | mutating steps |
|---|---:|
| BT-IS (rotor registers: 4 fixed ops per perm + 89 total factored setup) | 281 |
| SCALAR (APPLY_PERM: 8 ops per perm, rebuild input cube each time) | 384 |

**Ratio SCALAR / BT-IS: 1.37×. BT-IS is faster by 103 steps (26.8%).**

Both programs produce the same 48-output multiset: each of
the 6 axial states $\{\pm X, \pm Y, \pm Z\}$ appears 8 times.

## Interpretation

**BT-IS does win on the canonicalization inner loop.** The
win comes from setup cost, not from the per-apply primitive
itself (which is 1 op on both architectures).

- **BT-IS** loads a permutation into R0 in 0–3 named
  `rot_*_r` / `reflect_*_r` / `neg_r` instructions, then
  `apply_r 0` (1 op) applies it to C. Setup: 0–3 ops
  depending on the permutation. Apply: 1 op. Total:
  1–4 ops per permutation, plus `load_axis X` (1 op) and
  `outc` (1 op) = 3–6 ops per perm. Across 48 perms: 192
  + 89 = 281.

- **SCALAR** has no cube-copy primitive, so it must rebuild
  the input cube `(1, 0, 0)` from scratch each iteration
  using 3 `LOAD_IMM` + 3 `CGET` = 6 ops. Plus `APPLY_PERM`
  (1 op) and `OUT_C` (1 op) = 8 ops per perm. Across 48
  perms: 384.

The architectural claim "rotor registers reduce setup cost
for group-element operations" is supported on this workload.

## What this does not prove

- **The original 48× canonicalization claim.** That
  projected ratio assumed BT-IS could apply a group element
  to an entire 27-cell pattern in 1 op, which would require
  an `apply_r_to_mem` opcode that does not exist in the
  current ISA. The current ISA's `apply_r` is one
  permutation applied to one cube. The 27× outer loop
  cancels out: both architectures pay 27 ops per perm
  to apply it to a 27-cell pattern.
- **A general advantage across other group-structured
  workloads.** W5 is the inner loop of canonicalization;
  the per-perm cost of 1 op is shared. The 1.37× win is
  purely the setup cost. Workloads where the 27× outer
  factor dominates (e.g., a full canonicalization on a
  large 3D pattern) would not show this advantage.
- **Verdict reversal.** The Stage B / W5 results are now
  mixed: W1, W2, W5 show BT-IS faster; W4 shows BT-IS
  slower. The honest verdict is "BT-IS is competitive on
  some workloads, not others, on a fair comparison."
  See `VERDICT.md` for the consolidated decision.

## Files

- `benchmarks/w5_canon/oh.py` — generate 48 $O_h$ permutations
- `benchmarks/w5_canon/verify.py` — group axioms
- `benchmarks/w5_canon/factor.py` — BFS factorization
- `benchmarks/w5_canon/factor_sequences.json` — min factor per perm
- `benchmarks/w5_canon/gen_w5_btis.py` — emit BT-IS program
- `benchmarks/w5_canon/w5_scalar.py` — SCALAR equivalent
- `programs/w5_canon.btis` — generated BT-IS program
- `benchmarks/stage_b_w5.py` — driver with output-equality gate

## How to reproduce

```bash
# Generate the 48 O_h permutations.
python3 benchmarks/w5_canon/oh.py

# Verify group axioms.
python3 benchmarks/w5_canon/verify.py

# BFS-factor each permutation into named BT-IS rotor ops.
python3 benchmarks/w5_canon/factor.py

# Emit the BT-IS program.
python3 benchmarks/w5_canon/gen_w5_btis.py

# Run the comparison driver.
python3 benchmarks/stage_b_w5.py
```

The driver asserts BT-IS and SCALAR produce the same
48-output multiset (each of 6 axial states × 8) and
reports instruction counts. Exits non-zero on mismatch.
