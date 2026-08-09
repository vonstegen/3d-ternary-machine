# Stage B results (corrected)

> Expressiveness comparison: BT-IS vs a word-width SCALAR
> balanced-ternary RISC baseline. State-mutating instruction counts
> on representative workloads.

> **Note:** this is the *corrected* version. The original Stage B
> used a trit-granular SCALAR (per-coord ops with explicit carries)
> which produced an inflated 4.8× headline. A fair word-width
> baseline shows the actual ratio is ~1.5×. The original numbers
> are preserved in git history (commit `a2c38d2`).

## Method

Same as before — implement each workload twice, count mutating
instructions — but with a corrected baseline:

- The SCALAR baseline uses a *word-width* ALU: `WADD cd1, cd2`
  is one cube-add instruction (mirroring REBEL's 27-trit word
  model). The original trit-granular baseline decomposed this
  into `CADDX + CADDY + CADDZ + CARRY_X + CARRY_Y + CARRY_Z`
  (six ops), which was an unfair handicap.

Three workloads:

| ID | name              | what it stresses                |
|----|-------------------|---------------------------------|
| W1 | rotations         | pure 27-state LUT ops           |
| W2 | voxel_count       | cube memory + cube-add          |
| W4 | cubeadd_loop      | pure cube-add                   |

## Corrected results

| workload       | BT-IS | SCALAR (word-width) | ratio |
|----------------|------:|--------------------:|------:|
| W1 rotations   | 10    | 14                  | 1.40× |
| W2 voxel_count | 72    | 61                  | 0.85× |
| W4 cubeadd_loop| 15    | 22                  | 1.47× |

(`ratio` = SCALAR / BT-IS. Higher = BT-IS more efficient.)

## Interpretation

### W4 — cubeadd_loop: BT-IS 1.47× (not 4.8×)

This is the corrected headline. With a fair baseline, BT-IS's
`cube_add` advantage is **1.5×**, not 4.8×. The previous 4.8×
figure came from a baseline that decomposed a word-add into
six per-coord ops — a strawman.

The 1.5× advantage reflects:
- BT-IS cube-add: 1 op.
- SCALAR WADD: 1 op (the fair baseline).
- BT-IS's advantage comes from the *operand location*: BT-IS
  uses `C + mem[C]` (the cube IS the operand and the address
  simultaneously), while SCALAR's WADD requires the operands
  pre-loaded into cube registers. The setup cost (CGET × 3 +
  MEM_LOAD) is what tips the balance.

### W1 — rotations: BT-IS 1.40×

Same conclusion as before: small win. Both architectures do
8 rotations; BT-IS uses 8 `rot_*` instructions, SCALAR uses
8 `APPLY_PERM` instructions. The gap is setup overhead.

### W2 — voxel_count: BT-IS 0.85× (loss)

Unchanged. The current 4-cube-register file is the bottleneck;
the `cube_add` advantage cannot compensate for the operand
shuffling required.

## Conclusion of Stage B (corrected)

**The central hypothesis H is not strongly supported.**

- BT-IS's `cube_add` gives a ~1.5× instruction-count win over a
  fair word-width SCALAR. This is real but modest.
- BT-IS loses on workloads dominated by register-to-memory
  shuffling (W2: 0.85×).
- The architecture has *no* general-purpose advantage at the
  current ISA.

The original verdict ("niche") should be revised to:
**the architecture has a marginal advantage on cube-add-heavy
workloads, conditional on register-file improvements.** Without
those improvements, the architecture may not be worth pursuing.

## Action items

1. **Implement the fused `LOAD_CR` / `STORE_CR` ops** (LOAD_C
   with a rotor operand, applying R during the memory op).
   This directly attacks the W2 shuffle cost.
2. **Re-run W2** with the new ops.
3. **Find a workload that tests the symmetry group itself**, not
   just cube arithmetic. Candidates from the critique:
   polycube/voxel canonicalization, O_h-equivariant convolution.
4. **Re-run W4 with these new ops** to see if the 1.5× win
   extends to a 2-3× win on a workload that *uses* the group
   structure.

## How to reproduce

```bash
cargo build
python3 benchmarks/stage_b_word.py
```

The word-width baseline is in `benchmarks/scalar_vm_word.py`.
The per-workload programs are `programs/w*.btis` (BT-IS) and
`benchmarks/w*_word_scalar.py` (SCALAR).
