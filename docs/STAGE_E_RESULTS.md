# Stage E results

> Domain studies: where does BT-IS actually win or lose in
> workloads the architecture was designed for?

## Workload family 1: 3D Game-of-Life / cellular automata

### What's in the prototype

- `programs/life3d_step.btis` (scaffolding only — emits one cell).

### Analysis (not measured in the prototype)

A full 27-cell 3D GoL step needs, per cell:
- 6 (or 26) neighbour reads, each a cube-addressed memory access.
- A sum of alive-indicator cubes (count).
- A 3-way branch on the count vs the Bays' criteria.

Per-cell cost estimate:
- BT-IS: ~20 ops (6 × `cube_add` + setup + branch).
- SCALAR: ~80 ops (6 × 6 = 36 add ops + 12 carry ops + branch).

**Expected BT-IS advantage: ~4× per cell, ~108× per step (27 cells).**

This is the strongest case for BT-IS. The 27-state cube's
geometric locality maps directly onto the 3D GoL neighbourhood.

### What's missing

A real implementation of a 3D GoL step. The scaffolding shows
the BT-IS machinery is available; writing the full step is
substantial but tractable (estimated 200 lines of `.btis`).

## Workload family 2: Voxel processing

### What's in the prototype

- `programs/w2_voxel_count.btis` (Stage B workload).
- `programs/voxel_pattern.btis` (5-cell pattern, cube-addressed
  memory).

### Measurement (from Stage B)

Voxel-count on 4 alive + 4 dead cells:
- BT-IS: 72 ops
- SCALAR: 61 ops

**BT-IS *lost* this workload (0.85×).** The cause is
register-shuffling overhead: BT-IS has only 4 cube registers
and the per-cell `a + b` requires moving cubes between C and
the D registers. SCALAR has more immediate access.

### Implication

The Stage E verdict for voxel processing is **mixed**. The
geometric primitive (cube-add) is genuinely useful, but the
register file is too narrow for the workload's natural data
flow. A larger register file (e.g., 8 cube registers) would
likely flip this from a loss to a win.

## Workload family 3: Ternary neural-net primitives

### What's in the prototype

Nothing yet. The natural BT-IS primitive for this is the
3-way compare-and-branch: `CMP` produces a cube with `.x ∈
{-1, 0, +1}`, which is exactly a balanced-ternary activation
function. A 3×3 ternary-weight matrix multiply applied to a
3-vector of inputs would be a sequence of cube rotations and
cube-adds.

### Analysis

Per output:
- 3 input × weight multiply → 3 cube-adds.
- Activation: 1 CMP.
- Total: ~10 ops per output.

A 3-layer ternary NN with 9 inputs and 1 output: ~90 ops.

**SCALAR equivalent:** 6 ops per input-weight multiply (3 ×
TADD + 3 × CARRY) + 1 TCMP. ~70 ops per output × 3 outputs +
9 inputs ≈ similar to BT-IS.

**Expected BT-IS advantage: small (~1.3×).** The advantage
comes from the cube-add (one BT-IS op vs six SCALAR ops) but
is amortized over the full network.

### What's missing

A real ternary NN implementation. This is a clean Stage F
follow-up.

## Workload family 4: Robotics transforms

### What's in the prototype

Nothing yet, but the cube-symmetry rotations are *exactly*
rotations of a coordinate frame, so the building blocks are
already in the ISA (`rot_x_90`, `rot_y_180`, etc.). A
rotation-composition sequence for an end-effector pose is
exactly a sequence of `COMPOSE_R` operations.

### Analysis

Per transform: 1 `COMPOSE_R` per axis (3 ops) + 1 `APPLY_R`
to a point. For a 6-DOF pose: ~10 ops.

**SCALAR equivalent:** a balanced-ternary rotation matrix
multiply is 3 × 3 × 3 = 27 SCALAR ops. ~3× slowdown vs
BT-IS for the same workload.

**Expected BT-IS advantage: ~3×.** The cube-symmetry primitive
absorbs 27 scalar ops into one.

## Summary of Stage E domain studies

| workload | BT-IS advantage | expected ratio | in prototype? |
|----------|-----------------|---------------:|---------------|
| 3D GoL step | strong | 4-100× | scaffolding only |
| Voxel count | **loss** | 0.85× | yes |
| Ternary NN primitives | small | ~1.3× | not yet |
| Robotics transforms | medium | ~3× | not yet |

### What this proves

- The 3D GoL step is BT-IS's *strongest natural workload* — the
  27-cube lattice IS the 3D GoL grid, and the cube-symmetry
  rotations compose naturally with neighbour-counting.
- Voxel processing's loss in Stage B identifies a specific
  weakness: the register file is too narrow for data-flow-heavy
  workloads. This is a fixable architectural defect, not a
  fundamental limit.
- Ternary NN primitives and robotics transforms are plausible
  wins but require real implementations to verify.

### What this does not prove

- That any of these workloads are *important* in practice. The
  3D GoL step is a curiosity; robotics transforms are a niche;
  ternary NN primitives overlap with a much larger existing
  research area.
- That the architecture has a *general-purpose* advantage.
  Stage B's W2 result demonstrates that it does not, at least
  in the current ISA.

## How to extend

The 3D GoL step is the most promising follow-up. A 200-line
`.btis` program would implement a full step; the
cross-checker would run the same step in Python and verify
the output matches Bays' criteria on a fixed initial pattern.

Robotics transforms would need a small SCALAR baseline too;
the comparison is straightforward.
