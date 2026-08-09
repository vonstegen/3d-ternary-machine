# Stage E: domain studies (revised)

> Honest version. Removes the projected ratios that were not
> measured. The previous version of this document had a table of
> "expected ratios" that included numbers like "4-100×" for an
> unimplemented workload; Claude flagged these as wishful. This
> version keeps only what is measured or measured-relevant.

## Workload family 1: 3D Game-of-Life / cellular automata

**What's in the prototype:** `programs/life3d_step.btis` (scaffolding
only — emits one cell).

**Measured result:** none.

**Status:** not implemented. The Stage W5 negative result
suggests that even if implemented, BT-IS would *not* win on this
workload by more than a constant factor, because both BT-IS and
SCALAR can do cube-add and cube-memory access. The 27-state
cube lattice is convenient but the *cube-add primitive* is the
same in both architectures (W4: 1.47× ratio with fair SCALAR).

## Workload family 2: Voxel processing

**What's in the prototype:** `programs/w2_voxel_count.btis` and
`programs/voxel_pattern.btis`.

**Measured result (from Stage B):** BT-IS = 72 ops, SCALAR
(word-width) = 61 ops. **Ratio 0.85× (loss).** BT-IS loses on
this workload because of register-shuffle overhead; only 4 cube
data registers are insufficient.

**Status:** loss identified. The proposed fix (fused `LOAD_CR` /
`STORE_CR` with rotor operand) has not been implemented.

## Workload family 3: Ternary neural-net primitives

**What's in the prototype:** none.

**Measured result:** none. **No projected ratio.** The previous
"~1.3× expected" claim was removed; we don't have data.

## Workload family 4: Robotics transforms

**What's in the prototype:** none.

**Measured result:** none. The Stage W5 result (BT-IS ≈ SCALAR
on composition workloads) suggests that even when implemented,
BT-IS would be at most ~1× on robotics transforms — *not* the
"~3×" previously projected.

The "3× slowdown" estimate for SCALAR assumed a 3 × 3 × 3 = 27
op rotation-matrix multiply, which is unfair to SCALAR. A fair
SCALAR with a word-width rotation-matrix primitive matches
BT-IS op-for-op.

## Summary

| workload | measured? | result |
|----------|-----------|--------|
| 3D GoL step | no | not implemented |
| Voxel count | yes | 0.85× (loss) |
| Ternary NN | no | not implemented, no projection |
| Robotics transforms | no | not implemented, no projection |

## What was removed

The previous Stage E table included projected ratios:

| workload | claimed (removed) |
|----------|------------------:|
| 3D GoL step | "4-100×" |
| Ternary NN | "~1.3×" |
| Robotics | "~3×" |

These were removed because:

1. They were not measured.
2. The Stage B W4 result (1.47× with fair baseline) suggests
   the cube-add advantage is smaller than these projections
   assumed.
3. The Stage W5 result (BT-IS ≈ SCALAR with equivalent
   primitives) suggests that no architectural advantage exists
   beyond what the primitive set provides.

Projected ratios read as wishful. They are removed.

## What this proves

- BT-IS loses on voxel processing (W2: 0.85×) — a real,
  measured result.
- BT-IS ties on composition workloads (W5: 1.5× with fair
  SCALAR) — a real, measured result.
- BT-IS wins marginally on cube-add (W4: 1.47× with fair
  SCALAR) — a real, measured result.
- The 3D GoL step and ternary NN workloads remain unimplemented.
  Their architectural advantage (if any) is unproven.

## What this does not prove

- That the architecture is *useful* for any specific workload.
  Stage B + Stage W5 show it is approximately equivalent to a
  fair SCALAR baseline.
- That there exists *any* workload where BT-IS has an
  architectural advantage beyond what a fair SCALAR can match.

## Verdict implication

Combined with Stage B and Stage W5:

- W4 cube-add: 1.47× (modest)
- W5 composition: 1.50× (BT-IS slower)
- W2 voxel-count: 0.85× (loss)

The architecture has **no measured workload where it decisively
beats a fair SCALAR baseline.** This is the strongest evidence
that "the geometric primitive is an architectural advantage" is
false, and the verdict should shift from "niche" toward "no
demonstrated advantage."
