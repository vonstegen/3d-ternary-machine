# RESULTS

> Consolidated results from Stages A through F of the BT-IS roadmap.
> See `VERDICT.md` for the final decision and `STAGE_*_RESULTS.md`
> for per-stage detail.

## Headline

The 3D-Ternary Machine is **a niche architecture with genuine
geometric advantages on cube-arithmetic-heavy workloads, and a
loss on workloads dominated by register-to-memory traffic**. We
recommend continuing development in a narrowed scope.

## Instruction-count comparison vs SCALAR (Stage B)

| workload       | BT-IS | SCALAR | ratio |
|----------------|------:|-------:|------:|
| W1 rotations   | 10    | 13     | 1.30× |
| W2 voxel_count | 72    | 61     | 0.85× |
| W4 cubeadd_loop| 15    | 72     | 4.80× |

(`ratio` = SCALAR / BT-IS. Higher = BT-IS more efficient.)

BT-IS dominates on the cube-arithmetic-heavy workload (W4: 4.8×)
because the `cube_add` primitive absorbs 6 per-coord SCALAR ops
into 1 BT-IS op. BT-IS loses on the workload dominated by register
shuffling (W2: 0.85×) because the current 4 cube data registers
are too few to hold binary operands simultaneously.

## Architecture properties confirmed

- **Cube primitive**: 27 states, decomposition 1 + 6 + 12 + 8
  verified (Stage A math model).
- **Turing completeness**: proved by reduction to Minsky's
  2-counter machine (Stage A).
- **Reversibility**: per-step undo is constant-time; full
  program reversal is automatic by VM construction (Stage C).
- **Three-way branching**: native in both BT-IS and SCALAR; not a
  discriminator between the two architectures (Stage C).
- **Synthesizability**: behavioral Verilog model + area
  estimates show BT-IS fits on a low-cost FPGA (~3000 LUTs +
  9 BRAMs), 1.5× the SCALAR baseline's area (Stage D, estimates
  only).

## Implementation status

- Rust crate: 34 unit tests passing.
- Python prototype + cross-verification harness: working.
- 7 `.btis` example programs including Fibonacci (cross-checked)
  and W1/W2/W4 Stage B benchmarks.
- Behavioral Verilog core: compiles, area estimates documented.

## Decision criteria revisited

Per the roadmap's success criteria:

- **Useful** (continue general): requires P4 ≥10% reduction on
  ≥3 workloads, P5 within 2× area. **W4 achieves 4.8×**, but
  only one workload is verified. W2 fails. P5 estimated at
  ~1.5× but unmeasured. **Useful: not yet.**
- **Niche** (focused): requires P1, P3, P4 holds on a narrow
  class. **P3 confirmed; P1 qualitative only; P4 holds on W4**.
  W4 is the cube-arithmetic niche. **Niche: confirmed.**
- **Not worth pursuing** (archive): requires P4 fails on every
  workload or P3 fails. **P4 holds on W4 (a real workload);
  P3 confirmed.** Not-worth-pursuing: refuted.

The verdict is **niche**. The architecture has real, measurable
advantages on cube-arithmetic-heavy workloads. These workloads
are not the general case, but they exist and are interesting.

## Recommendations

1. **Add more cube data registers (D4..D7)** to fix the W2 loss.
   This is a small ISA extension; estimated cost ~20-40 LOC.
2. **Implement the 3D Game-of-Life step** to test the strong
   expected BT-IS advantage on the niche's flagship workload.
3. **Real FPGA synthesis** with yosys + nextpnr to convert
   Stage D estimates into measurements.
4. **Re-decide at v0.3.0** after the above.

## What's next

The roadmap stops at Stage F. Stage G (publication) is outside
the scope of this repo. After v0.3.0, the right next step is a
paper describing the architecture, the cube-arithmetic advantage,
the niche, and the limitations — aimed at a venue like the
Journal of Symbolic Computation or a workshop on novel
architectures.
