# RESULTS

> Consolidated results from Stages A through F of the BT-IS roadmap,
> plus corrections received via external critique. See
> `VERDICT.md` for the final decision and `STAGE_*_RESULTS.md`
> for per-stage detail.

## Headline (corrected)

After critique:

> The 3D-Ternary Machine has a **marginal advantage on
> cube-arithmetic-heavy workloads (~1.5× instruction-count over a
> fair word-width SCALAR)** and a **loss on workloads dominated by
> register-to-memory shuffling (0.85×)**. The original 4.8×
> headline was a baseline artifact (trit-granular SCALAR with
> explicit carries vs word-width SCALAR).

The architecture's *distinctive* feature is the rotor registers
and group-element composition (Pendulum-style), not the cube
arithmetic. The right next benchmark exercises the group
structure, not just the cube arithmetic.

## Instruction-count comparison vs word-width SCALAR

| workload       | BT-IS | SCALAR | ratio |
|----------------|------:|-------:|------:|
| W1 rotations   | 10    | 14     | 1.40× |
| W2 voxel_count | 72    | 61     | 0.85× |
| W4 cubeadd_loop| 15    | 22     | 1.47× |

(`ratio` = SCALAR / BT-IS. Higher = BT-IS more efficient.)

### Comparison with the original (incorrect) Stage B numbers

| workload | original SCALAR | corrected SCALAR | original ratio | corrected ratio |
|----------|----------------:|-----------------:|---------------:|----------------:|
| W1 | 13 | 14 | 1.30× | 1.40× |
| W2 | 61 | 61 | 0.85× | 0.85× |
| W4 | 72 | 22 | **4.80×** | **1.47×** |

The W4 ratio collapse (4.80× → 1.47×) was the most important
finding from the critique. The original baseline decomposed
a cube-add into six per-coord ops; the corrected baseline treats
a cube as a 27-trit word, matching REBEL's actual architecture.
The 1.47× ratio reflects operand-location (BT-IS cube *is* the
address) and the slight overhead savings on tight arithmetic loops,
not a "3-wide-vs-1-wide arithmetic advantage."

## Architecture properties confirmed

- **Cube primitive**: 27 states, decomposition 1 + 6 + 12 + 8.
- **Turing completeness**: proved by reduction to Minsky's
  2-counter machine; reduction is polynomial in program size.
- **Intrinsic reversibility** of the rotation/reflection subset.
  Full-ISA reversibility is journal-based (Bennett-style) and
  works for any machine — not a distinguishing feature.
- **Three-way branching**: native in BT-IS; also native in
  SCALAR's TCMP+BR shape. Not a discriminator.
- **Synthesizability**: behavioral Verilog model; estimated
  ~3000 LUTs + 9 BRAMs. SCALAR ~2000 LUTs. Area ratio ~1.5×.
  Estimates only.

## Implementation status

- Rust crate: 34 unit tests passing.
- Python prototype + cross-verification harness: working.
- 7 `.btis` example programs including Fibonacci (cross-checked)
  and W1/W2/W4 Stage B benchmarks.
- Behavioral Verilog core: compiles, area estimates documented.

## Decision criteria revisited

Per the roadmap's success criteria:

- **Useful** (continue general): requires P4 ≥10% reduction on
  ≥3 workloads, P5 within 2× area. After correction: P4 holds
  marginally on W4 (1.47×). Other workloads are ties or losses.
  P5 estimated at ~1.5× area. **Useful: not yet.**
- **Niche** (focused): the symmetry-group subset (P4) gives a
  real win on a small set of workloads. **Niche: still
  plausible, pending a group-exercising workload measurement.**
- **Not worth pursuing** (archive): P4 fails on every workload
  we try, or P3 fails. **P3 holds for the subset; P4 holds
  marginally on W4.** Not-worth-pursuing: refuted.

The verdict remains **niche**, with the caveat that the
niche has not yet been *positively demonstrated* on a workload
that exercises the symmetry group rather than just cube arithmetic.

## Recommendations

1. **Add fused `LOAD_CR` / `STORE_CR`** (memory ops with a rotor
   operand). This directly attacks the W2 shuffle cost without
   widening the register file.
2. **Implement a polycube/voxel-canonicalization workload**.
   This tests the symmetry-group claim — the distinctive feature
   of BT-IS — rather than just cube arithmetic.
3. **Real FPGA synthesis** with yosys + nextpnr.
4. **Re-decide at v0.3.0** after the above.

## What's next

The roadmap stops at Stage F. Stage G (publication) is outside
the scope of this repo. After v0.3.0, the right next step is a
paper describing the architecture, the cube-arithmetic advantage,
the niche, and the limitations — aimed at a venue like the
Journal of Symbolic Computation or a workshop on novel
architectures.
