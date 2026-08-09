# Status of Claude's 6-step plan

> Audit of where each of Claude's 6 recommendations stands in the
> repo. Tagged `v0.2.1-corrected` was committed in the prior
> critique-response pass.

## Step 1 — Fix the baseline before anything else

**Status: DONE** (in `v0.2.1-corrected`).

The word-width SCALAR baseline
(`benchmarks/scalar_vm_word.py`, `WADD cd1, cd2`) replaced the
trit-granular strawman. Re-running Stage B with the fair baseline
shows the W4 ratio collapsed from **4.80× to 1.47×**.

| workload | BT-IS | SCALAR (word-width) | ratio |
|----------|------:|-------------------:|------:|
| W1 rotations | 10 | 14 | 1.40× |
| W2 voxel_count | 72 | 61 | 0.85× |
| W4 cubeadd_loop | 15 | 22 | **1.47×** |

The corrected numbers are in `docs/STAGE_B_RESULTS.md` and
`docs/RESULTS.md`.

## Step 2 — Reframe the claim around the group, not the cube

**Status: PARTIALLY DONE.**

The positioning doc now states the claim is about the *symmetry
group* — the rotor registers and group-element composition — not
about cube arithmetic. From `docs/positioning.md` §4:

> The architecture has **two algebras on the cube**: a permutation
> algebra (rotations, reflections, compositions, inverses) and an
> arithmetic algebra (cube-add with carry through x, y, z). These
> do not unify algebraically. The arithmetic algebra treats
> coordinates as positional digits with place value; the
> permutation algebra treats them as interchangeable spatial
> axes. BT-IS ships both; the geometric claim is *about the
> permutation algebra*, not about the arithmetic one.

But the claim has not yet been *benchmarked* — Step 3 is what
makes this reframe real rather than aspirational.

## Step 3 — Make canonicalization the flagship benchmark

**Status: NOT STARTED.** This is the load-bearing experiment.

The next benchmark must be one where the *symmetry group is the
inner loop*: voxel-pattern canonicalization under O_h. Apply all
48 group elements to a 3×3×3 pattern, pick the smallest
configuration under some canonical ordering.

Expected ratio: ~48× — every SCALAR cube-add for the cube-arithmetic
operations in the canonical ordering pays the same cost, while
BT-IS's `APPLY_R` does one rotation per op.

This is the work for v0.3.0.

## Step 4 — Fix the two false claims now

**Status: DONE.**

- **Reversibility**: restricted to the rotation/reflection subset
  in `docs/positioning.md` §2 #6 and `docs/STAGE_C_RESULTS.md`.
- **VSA comparison**: removed; rewritten as a *disclaimer* in
  `docs/positioning.md` §3.
- **Stage E projected ratios**: the table in
  `docs/STAGE_E_RESULTS.md` still has entries like "expected
  4-100×" and "expected ~3×" for unimplemented workloads. These
  are exactly the "projected ratios read as wishful" that Claude
  flagged. **They need to be cut or implemented.** Tracked in
  todos.

## Step 5 — Real synthesis

**Status: BLOCKED on tools.** No yosys / nextpnr available on this
machine. Requires installation:

```bash
# Debian/Ubuntu
sudo apt-get install yosys
# iCE40 toolchain
pip install nextpnr-ecp5   # or build from source for iCE40
# or for Lattice ECP5
sudo apt-get install nextpnr-ecp5
```

This is a one-weekend-of-work step. The estimate in Stage D
(~3000 LUTs) needs to become a measurement.

## Step 6 — Publish

**Status: BLOCKED on Step 3.**

The honest scope is a workshop paper (ARCS, CF, or reversible/
unconventional computing venue), not mainline ISCA. The verdict
shifts from "niche" to "rigorous negative-plus-niche result
with one clean win" if Step 3 confirms a real canonicalization
win.

## What this means for the v0.3.0 release

- **Required**: Step 3 (canonicalization benchmark, implemented
  in BT-IS and SCALAR, instruction counts compared).
- **Required**: Step 4 finishing (cut Stage E projected ratios).
- **Optional but valuable**: Step 5 (real synthesis).

If Step 3 shows a real win (~48× on canonicalization, or any
double-digit factor on a group-exercising workload), the paper
becomes viable.

If Step 3 shows no win, the verdict becomes "not worth pursuing
general-purpose; the geometric primitives are real but no
workload in our reach tests them." That's also a publishable
finding.

Either outcome is honest. The right move is to *do* Step 3 and
find out.
