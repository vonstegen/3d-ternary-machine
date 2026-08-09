# Verdict

> Final synthesis of Stages A through E into a decision about
> whether the 3D-Ternary Machine architecture is useful, niche,
> or not worth pursuing.

## Summary of evidence

| Stage | result |
|-------|--------|
| **A: Correctness / universality** | Fibonacci F(0..9) mod 27 cross-checked against Python reference. Turing-completeness proved by reduction to Minsky's 2-counter machine. |
| **B: Instruction-count vs SCALAR** | W4 cube-add loop: **BT-IS 4.8× faster**. W1 rotations: 1.3× faster. W2 voxel-count: **0.85× (loss)**. |
| **C: Reversibility + 3-way branches** | Reversibility automatic, per-step undo constant-time. 3-way branching qualitative only; SCALAR has the same TCMP + BR shape. |
| **D: Native hardware** | Behavioral Verilog model synthesizable; estimated ~3000 LUTs + 9 BRAMs on a low-cost FPGA. SCALAR smaller in area. P5 likely true (~1.5× area ratio), not measured. |
| **E: Domain studies** | 3D GoL step: strong BT-IS advantage expected (~4-100×), not implemented. Voxel processing: loss identified (register-file issue). Ternary NN: small expected win. Robotics transforms: medium expected win. |

## Decision

The architecture is **niche**, not general-purpose useful.

### What works

- **Cube-arithmetic-heavy workloads** see a real instruction-
  count win (Stage B W4: 4.8×). This is the geometric payoff
  the architecture was designed for.
- **3-way branching and reversibility** are real architectural
  properties, even if not measurable as instruction-count wins
  vs the SCALAR baseline (Stage C).
- **The architecture is synthesizable** on a low-cost FPGA at
  modest area (Stage D estimates).

### What doesn't work

- **The register file is too narrow** for workloads dominated by
  register-to-memory shuffling. Stage B W2 (voxel count) lost
  15% to SCALAR for this reason. A larger register file
  (8+ cube registers) might fix this, but it would also widen
  the ISA.
- **General-purpose advantage** is not established. The current
  evidence is workload-specific.
- **3D GoL / robotics / NN workloads** are not implemented. The
  expected wins are plausible but unverified.

### What the niche looks like

If the verdict is "useful for X, niche for Y", the natural
niche is **cube-arithmetic-dominated spatial computing**:

- 3D cellular automata on the cube grid (the natural fit).
- Voxel neighbourhood iteration (if the register-file issue
  is fixed).
- 3D robotics pose composition (the cube-symmetry rotations
  are exactly the tool needed).
- Ternary neural-network primitives (the 3-way activation is
  native).

For these workloads, BT-IS is plausibly the cleanest available
machine. For others, it's at best parity.

## What we did *not* claim

- We did not claim the architecture is *useful for general-
  purpose computing*. Stage B W2 shows it's not.
- We did not claim native hardware is production-ready. The
  Stage D estimates are estimates.
- We did not claim the architecture is more *efficient* in
  cycles or joules. We measured instruction count, which is
  one proxy.

## What we did claim

- The architecture is *real*: it has a Rust VM, an assembler,
  CLI, 31+34 unit tests passing, a Python cross-verification
  harness, and a Verilog core model.
- The architecture is *universal*: it can express any
  computable function (Turing-completeness by reduction).
- The architecture is *geometrically motivated*: instructions
  are permutations of cube states, and the cube's structure
  (1 + 6 + 12 + 8 = 27 states, 1 + 6 + 12 = 19 symmetry orbits)
  is the source of instruction semantics.
- The architecture has *real reversibility*: every program is
  undoable, automatically, by VM construction.
- The geometric primitives *can* absorb scalar operations:
  one BT-IS `cube_add` does what six SCALAR ops do.

## Honest verdict

**Niche.** The architecture has genuine geometric advantages on
workloads that exercise cube arithmetic heavily (Stage B W4
shows a 4.8× instruction-count reduction). These workloads
exist and are interesting, but they are not the general case.

For general-purpose use, BT-IS as currently specified loses to
SCALAR on workloads dominated by register-to-memory traffic
(Stage B W2 shows a 0.85× ratio).

We recommend:

1. **Continue development** but narrow scope to the cube-
   arithmetic niche (3D GoL, voxel iteration, robotics,
   ternary NN).
2. **Fix the register-file issue** before claiming the voxel
   workload as a win. The fix is straightforward: add cube
   registers D4..D7 and verify the W2 result flips.
3. **Real FPGA synthesis** in Stage D's planned follow-up to
  convert estimates into measurements.
4. **Re-decide at v0.3.0** after the register-file expansion and
   FPGA synthesis are done.

We explicitly do *not* recommend archiving the project: the
niche is real, the architecture is well-grounded mathematically,
and the implementation is solid. The right next step is
*focusing* on the niche, not abandoning the work.
