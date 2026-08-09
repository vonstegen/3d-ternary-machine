# RESULTS (v0.3.1)

> Consolidated results from Stages A through W5 as of the
> v0.3.1 tag. The numbers in this document are the
> **re-measured** instruction counts after the v0.2.0-niche
> and v0.3.0-negative tags were found to be comparing
> different programs on BT-IS and SCALAR. The current
> drivers (`benchmarks/stage_b_word.py` and
> `benchmarks/stage_b_w5.py`) assert output equality
> before reporting any ratio and exit non-zero on
> mismatch.

## Headline

| workload | BT-IS | SCALAR (fair) | ratio (SCALAR / BT-IS) |
|---|---:|---:|---:|
| W1 rotations | 9 | 14 | 1.56× |
| W2 voxel_count (3 alive face neighbors) | 34 | 52 | 1.53× |
| W4 cubeadd_loop (10× of `C := C + C`) | 32 | 22 | 0.69× (loss) |
| W5 48 $O_h$ inner loop | 281 | 384 | 1.37× |

`ratio` is SCALAR / BT-IS. Higher = BT-IS more efficient.

**BT-IS wins on three of four measured workloads** (W1,
W2, W5). **BT-IS loses on one** (W4, pure cube-add
recurrence). The v0.2.0-niche 4.8× W4 headline and the
v0.3.0-negative 0.67× W5 loss were both artifacts of
mismatched programs; the v0.3.1 numbers above are the
honest measurements.

## What each workload actually measures

### W1 — rotations (BT-IS 1.56× faster)

7 geometric ops (`rot_z_90, rot_x_90, rot_y_180,
rot_z_270, rot_x_180, reflect_x, neg`) on the input cube
`(1, 0, 0)`. Both programs produce `(0, 0, -1)`.

BT-IS uses `load_axis X` + 7 named ops + `outc` + `halt`
= 9 mutating steps. SCALAR uses 3 `LOAD_IMM` + 3 `CGET`
to build `(1, 0, 0)`, 7 `APPLY_PERM`, `OUT_C`, `HALT` =
14 mutating steps. The 1.56× win is SCALAR's per-program
setup cost (3 + 3 = 6 ops to build the input cube),
not the rotation primitive itself (1 op on both
architectures).

### W2 — voxel_count (BT-IS 1.53× faster)

3 alive face neighbors of `(0, 0, 0)`: `+X`, `-X`, `+Y`.
The pattern is stored in `mem` with `mem[addr] = addr`.
For each alive neighbor, the running accumulator `C` is
updated via `cube_add`. Both programs produce `(0, 1, 0)`.

BT-IS uses 34 mutating steps; SCALAR uses 52. The win is
the operand-location cost: BT-IS's `cube_add` reads
`C := C + mem[C]` (the cube is both address and value),
while SCALAR's `WADD` requires a separate `MEM_LOAD_C`
per iteration. BT-IS saves 1 op per neighbor.

The previous v0.2.0-niche 0.85× loss was on a different
W2 program (the SCALAR had a register-index bug that
made `C1` constant `(-1, -1, -1)`, and the BT-IS counted
only 4 of 8 neighbors with a different sequence). The
v0.3.1 numbers are on the corrected programs.

### W4 — cubeadd_loop (BT-IS 0.69× slower)

10 iterations of `C := C + C` starting from `(1, 1, 1)`.
Both programs produce `(1, 0, 0)`.

BT-IS uses 32 mutating steps (3 setup + 2 per iteration
× 10 + `outc` + `halt`). SCALAR uses 22 (6 setup + 1 per
iteration × 10 + `OUT_C` + `HALT`). SCALAR's `WADD C0,
C0` is 1 op; BT-IS's `cube_add` is `C := C + mem[C]`,
which requires a `store_d 0` + `cube_add` + `mov_cd 0`
refresh sequence to compute `C := C + C`. The setup
overhead per iteration costs BT-IS 1 op.

The v0.2.0-niche 1.47× win was on a different W4 program
(BT-IS did `C := C + mem[C]`, which became a no-op after
iter 0 because the address changed and `mem[C]` was
empty). The v0.3.1 0.69× loss is the honest measurement
when both sides compute the same recurrence.

The cube-add primitive is **not** a load-bearing win
when both architectures compute `C := C + C` directly.

### W5 — 48 $O_h$ inner loop (BT-IS 1.37× faster)

For each of the 48 elements of the cube's full
octahedral symmetry group $O_h$, apply it to `(1, 0, 0)`
and emit the result. The output orbit is the 6 axial
states $\{\pm X, \pm Y, \pm Z\}$, each appearing 8 times
(48 / 6 = 8). Both programs produce the same 48-output
multiset.

BT-IS uses 281 mutating steps; SCALAR uses 384. The win
is the rotor-register setup cost. BT-IS loads a
permutation into R0 in 0-3 named `rot_*_r` /
`reflect_*_r` / `neg_r` instructions, then `apply_r 0`
(1 op) applies it to `C`. SCALAR has no cube-copy
primitive, so it must rebuild the input cube from
scratch each iteration using 3 `LOAD_IMM` + 3 `CGET` = 6
ops. Per-apply: 1 op on both. The 1.37× win is
SCALAR's per-iteration setup overhead.

The v0.3.0-negative 0.67× loss was on a different W5
program (a single 7-term composition, not the 48-symmetry
inner loop). The v0.3.1 1.37× win is the honest
measurement on the actual canonicalization experiment.

**W5 is the inner loop of voxel canonicalization, not
full canonicalization.** Full canonicalization (apply 48
group elements to all 27 cells of a 3×3×3 pattern) is
27× the inner loop on both architectures. Since both
`apply_r` and `APPLY_PERM` are 1 op per application, the
per-cell ratio is 1:1 and the 27× outer factor doesn't
change the win. The "48× canonicalization flagship" claim
in the v0.2.0 ROADMAP was for a not-yet-implemented
`apply_r_to_mem` opcode that operates on a 27-cell
pattern, not a single cube.

## Architecture properties

The following properties are confirmed by the v0.3.1
implementation:

- **Cube primitive**: 27 states, decomposition 1 + 6 + 12 + 8.
- **Turing-completeness**: **claim withdrawn** at v0.3.1.
  The proof in `docs/turing_completeness.md` requires
  unbounded cube-keyed memory; the VM has at most 27
  keys. Re-deriving the proof requires an unbounded
  address register and a corrected DEC algorithm. Out of
  scope for v0.3.1.
- **Intrinsic reversibility** of the rotation /
  reflection subset (12 named ops, each is a group
  element with an inverse in $O_h$).
- **Journal reversibility** of the full ISA via
  `vm.undo_all()`. Bennett-style history tape; works for
  any register VM; not an architectural property of
  BT-IS.
- **Three-way branching**: present in both BT-IS and
  SCALAR. Not a discriminator at the instruction-count
  level.
- **Synthesizability**: projected, not measured. The
  Verilog model in `hardware/btis_core.v` is incomplete
  (12 of 13 rotation tables uninitialized, 6+ opcodes
  TODO no-ops). The "~3000 LUTs + 9 BRAMs" figure is a
  design estimate, not a synthesis result.

## Implementation status

- Rust crate: **34 unit tests passing**.
- 16 `.btis` example programs (rotation trajectories,
  Fibonacci, voxel patterns, W1/W2/W4 Stage B workloads,
  W5 canonicalization).
- Python prototype + cross-verification harness
  (`benchmarks/verify.py`, `benchmarks/cross_check.py`).
- W5 cross-checked: BT-IS output multiset matches SCALAR
  output multiset (each of 6 axial states × 8 = 48
  outputs).
- Stage D hardware: behavioral Verilog, no synthesis.

## What's NOT confirmed at v0.3.1

- That BT-IS has an architectural advantage on
  *general-purpose* workloads. The four measured
  workloads are geometric; SCALAR with similar
  primitives matches or beats BT-IS on the cube-add
  primitive.
- That the rotor registers give a general compositional
  advantage. The W5 win is setup-cost only; on a
  per-`apply` basis, BT-IS and SCALAR pay the same 1 op.
- That 3D Game-of-Life, balanced-ternary neural
  networks, or other domain workloads favor BT-IS.
  None have been implemented at v0.3.1.
- That native hardware synthesis is feasible. The
  Verilog model is incomplete; area / latency / power
  numbers are projections.
- That the architecture is Turing-complete. The proof
  is withdrawn.

## Decision criteria at v0.3.1

The v0.2.0 ROADMAP defined:

- **Useful** (continue general): ≥10% on ≥3 workloads.
  v0.3.1 has 3 workloads with >50% wins (W1 1.56×, W2
  1.53×, W5 1.37×) and 1 workload with a 0.69× loss
  (W4). 3/4 ≥10% is met. **Useful: ambiguous.** The
  wins are real but the W4 loss is also real, and
  none of the wins is on a domain-relevant application.
- **Niche**: a single workload with a real win. W2
  (voxel-count) is the closest candidate at 1.53×, but
  the 3-alive-neighbor test is a toy workload, not a
  domain benchmark. **Niche: not established.**
- **Not worth pursuing** (archive): all measured
  workloads lose. W1, W2, W5 are wins. **Not worth
  pursuing: not established.**

The honest position is **competitive on some
workloads, slower on one, with no clear niche
established.** This is documented in `VERDICT.md` as
the v0.3.1 verdict.

## Recommendations

1. **Do not invest in more ISA extensions to chase the
   48× canonicalization claim.** The current
   architecture's `apply_r` is 1 op per cube; the
   per-cell ratio is 1:1 with SCALAR. To get a real
   48× win on full canonicalization, a new
   `apply_r_to_mem` opcode is needed — and that's a
   new architecture, not an extension of the existing
   one.
2. **Do not invest in 3D Game-of-Life step
   implementation** until the W4 register-shuffle
   cost is understood better. The 1.53× W2 win was on
   a 3-alive-neighbor toy; the original v0.2.0
   expectation of "3D GoL would be a 4-100× win" was
   retracted in `docs/STAGE_E_RESULTS.md`.
3. **Archive the project as a reference
   implementation.** The math, the tests, and the
   benchmark methodology are a real contribution; the
   thesis the project started with is not supported by
   the v0.3.1 measurements.
4. **Or, alternative: reframe as a teaching
   artifact.** The code, tests, and documentation are
   well-suited for a course on novel machine
   architectures or balanced-ternary computing.

## What's next

The v0.3.1 verdict replaces both the v0.2.0-niche
"niche" label and the v0.3.0-negative "not worth
pursuing" framing. Neither is supported by the data.

Path forward (a) archive the project as a clean
reference; (b) reframe as a teaching artifact; (c) look
for a workload where BT-IS shows a ≥2× win. Path (c) is
the open question. Candidates from the v0.2.0 ROADMAP
(polycube / voxel canonicalization, $O_h$-equivariant
convolution) have not been tried at v0.3.1 because
`apply_r_to_mem` doesn't exist in the current ISA.

## Honest reading

The architecture was a reasonable hypothesis; the
hypothesis has been tested; the test result is "BT-IS is
competitive with a fair SCALAR baseline on three of four
measured geometric workloads, and slower on the fourth."
That's a valid research outcome. It is not a positive
result, but it is not a negative result either.

The codebase is real, working, well-tested, and
well-documented. It is a clean implementation of a
balanced-ternary cube machine with reversible execution
on a subset of the ISA. That is a contribution, just not
the one originally proposed.
