# Stage C results

> Reversibility and three-way branching quantification.

## Reversibility

The BT-IS VM records an `Undo` entry for every state-mutating step
in `vm.undo_log`. Calling `vm.undo_all()` pops them in reverse
order, recovering `(C, F, R, D, mem)` to the pre-run state.

We demonstrate this on a W4-like program (3 cube-adds):

```
initial C:   Cube((0, 0, 0))
after run C: Cube((-1, 0, 0))
after undo C: Cube((0, 0, 0))
undone 6 steps; mem_restored: true
RESTORED: true
```

All 6 instructions are undone; `mem` is empty (the `STORE_C` was
undone); `C` is back to its initial value.

### Properties demonstrated

1. **Per-step undo is constant-time.** Each `Undo` entry is a
   small enum variant; pushing and popping them is O(1).
2. **Reversibility is automatic**, not a programmer opt-in.
   Every BT-IS program is reversible by construction — including
   programs that use `CALL`/`RET` (whose stack manipulation is
   recorded in `Undo::RestoreStackLen`).
3. **The undo log grows linearly** with instruction count. For
   long-running programs this is O(n) memory. The VM does not
   currently support commit/rollback regions; this is a
   potential Stage F follow-up.

### What this proves

- BT-IS is *unconditionally reversible*. Every program execution
  has a well-defined inverse trajectory through the 27-cube.
- Reversibility is essentially free in implementation terms:
  each `exec()` arm pushes one `Undo`, and the VM does not need
  separate bookkeeping for "checkpoint vs run" modes.

### What this does not prove

- That reversibility is *useful* in practice. Most software is
  not reversible; reversible execution is a curiosity except in
  specific niches (speculative execution, debugging, formal
  verification, undoable editing).
- That a non-trivial *interesting* program demonstrates reversibility
  usefully. The Stage C todo asked for "e.g. undoable GoL"; that
  program has not been written (and is itself a Stage A follow-up).

## Three-way branching

We count branch-related ops across the existing programs:

```
program                       BR_NEG  BR_ZERO  BR_POS   JMP  CALL   RET
  programs/countdown.btis            0        3       0     2     0     0
  programs/fibonacci.btis            0        0       0     0     9     9
  programs/w4_cubeadd.btis           0        0       0     0     0     0
  programs/voxel_pattern.btis        0        0       0     0     0     0
  programs/w3_merge.btis             0        0       1     0     0     0
```

### What the numbers say

- `countdown.btis` uses 3 BR_ZERO + 2 JMP. It loops while a counter
  is non-zero, dispatching on a single 3-way branch each iteration.
- `fibonacci.btis` uses 9 CALL + 9 RET. The fib_step subroutine
  is called 9 times, returning each time. (Subroutine call/return
  is not strictly a "branch" but is dispatch logic.)
- `w3_merge.btis` uses 1 BR_POS. A single 3-way branch dispatches
  to one of three paths after a CMP.

### Comparison with SCALAR

In the SCALAR baseline (REBEL-style), the same code uses:

- TCMP followed by three separate `BR_GT / BR_EQ / BR_LT`. That's
  the same instruction count as BT-IS (one TCMP + one branch).
- For *lexicographic* comparison (compare .x, then .y, then .z
  if tied), SCALAR needs 3 TCMP + up to 3 branch dispatches.

So three-way branching is *not* a discriminator between BT-IS and
SCALAR at the ISA level — both architectures have native 3-way
comparison. The architectural claim "three-way branching is
natural" is true for both, and *neither* has the cascade-of-two-way
branches that a Boolean ISA would need (a Boolean ISA would
require `if-else if-else` chains for the same logic).

### Where BT-IS does benefit from three-way semantics

The architectural benefit of three-way branches is in the
*semantics* of the ISA:

- `F` is itself a cube, with `.x` carrying the sign `{-1, 0, +1}`.
- The three branches are encoded as cube directions, not
  Boolean conditions.
- The flag is a *first-class value* — it can be inspected,
  transformed (rotated, reflected), or stored, in the same way
  as any other cube.

This is a qualitative property of BT-IS rather than a measurable
quantitative win over SCALAR.

## Conclusion of Stage C

**Reversibility:** demonstrated and verified. Per-step undo is
constant-time; full program undo is O(n) in instruction count.
**P3** (constant-time per-step undo, native reversibility) is
**confirmed**.

**Three-way branching:** present in both BT-IS and SCALAR, so
the SCALAR baseline does not let us measure an instruction-count
advantage. The qualitative advantage — that the flag is itself
a cube — is a design property of BT-IS, not a measurable win.
**P1** (three-way branches replace 2-way cascades) is
**confirmed qualitatively**; **not measurable** as an
instruction-count win over the SCALAR baseline.

## How to reproduce

```bash
cargo build --example reversibility_demo
python3 benchmarks/stage_c.py
```

The reversibility demo lives in
`examples/reversibility_demo.rs`; the three-way branch counts
are computed by parsing `--trace` output.
