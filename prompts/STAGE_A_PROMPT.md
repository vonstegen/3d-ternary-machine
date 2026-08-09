# Stage A handoff (v0.3.1)

> **Context.** Branch `v0.3.1-fixes` is merged, tag `v0.3.1` is
> on `main` at `3ab67f3`. The TC proof is withdrawn, the assembler
> validates operands/indices, `undo_all` is complete, the Tracer
> is precise. All 51 unit tests pass; all four benchmarks (W1
> 1.56×, W2 1.53×, W4 0.69×, W5 1.37×) pass on output-equality.
>
> **What's left (7 items, all Stage A programs).**

## 1. Implement `gcd.btis` with the Euclidean algorithm in cube arithmetic.

## 2. Cross-check `gcd` against a Python reference.

## 3. Implement `life3d_step.btis` with a full 3×3×3 Bays' step.

## 4. Cross-check `life3d_step` against a Python reference.

## 5. Implement `sort3x3x3.btis` as a real sort (not a hard-coded triple).

## 6. Cross-check `sort3x3x3` against a Python reference.

## 7. Update `ROADMAP.md` Stage A exit criteria to checked boxes where
        the programs now exist.

---

## Key constraints

1. **ISA limits.** v0.3.1 has `CUBE_ADD` (full 27-state with carry,
   top carry dropped) and `CMP` (sign of `C.x - arg`). It does
   **not** have `CUBE_SUB` or `CUBE_CMP`. For `gcd.btis` and
   `sort3x3x3.btis`, this means the operand values are effectively
   limited to the `.x` coordinate (range `{0, 1, 2}`) or to small
   cube values where the algorithm terminates. Document the
   limitation explicitly in the program header.

2. **`life3d_step` is the hardest.** 27 cells, 6/18/26-neighbor
   variants, Bays' classification. Start by writing the Python
   reference first (the oracle), then the BT-IS program that the
   oracle will be checked against. The current stub in
   `programs/life3d_step.btis:39-60` is just `outc` of one cell.

3. **Python cross-checks.** `benchmarks/cross_check.py` is the
   existing harness. It only handles fibonacci.btis today. For
   gcd, life3d_step, and sort3x3x3, add new functions to that
   file (or write a separate script per program) that:
   - Run the BT-IS program and parse its `OUTV` / `OUTI` output.
   - Run the equivalent Python reference.
   - Assert they match.
   - Exit non-zero on mismatch (consistent with the v0.3.1 driver
     convention).

4. **Don't extend the ISA.** If a workload can't be done with the
   existing opcodes, either:
   - Restrict the input domain and document it, or
   - Mark the workload as "out of scope for v0.3.1" and retitle
     the program file.
   Adding `CUBE_SUB` / `CUBE_CMP` would be a real ISA change with
   downstream effects on the existing benchmarks. The `v0.3.1`
   release should not silently grow the ISA.

5. **Update `ROADMAP.md` last.** Mark the checkboxes (`[x]`) only
   after the program and its cross-check both exist and pass.

## Recommended order

1. **Sort first** — smallest, most testable. Lexicographic sort on
   the `.x` coordinate of 27 cells is ~50 lines of BT-IS, even
   with no CUBE_CMP. Use a simple sort network (odd-even
   transposition).
2. **GCD next** — already half-done from the previous session. The
   current `programs/gcd.btis` stub needs a complete rewrite; aim
   for inputs `{0, 1, 2}` with the Euclidean by repeated
   subtraction.
3. **Life3dStep last** — most complex. Write the Python oracle
   first, then the BT-IS program that emits the same pattern.

## Test convention

All three programs should:
- Emit their result via `OUTV` (cube) or `OUTI` (trit)
  consistently.
- Be invokable from bash: `cargo run -- programs/X.btis`.
- Be cross-checked by a Python script in `benchmarks/`.

## Tools that will help

- The existing 51 unit tests in `src/`. Don't break them; add new
  tests in the same modules (`src/cube.rs`, `src/asm.rs`,
  `src/vm.rs`).
- The `benchmarks/stage_b_word.py` and `benchmarks/stage_b_w5.py`
  drivers — same pattern of "run BT-IS, run Python, assert
  output match" should apply to Stage A programs.
- The `python/vrml/cube.py` module — has the Python mirror of the
  27-state cube, useful for Python oracles.

## Done-when checklist

- [ ] `programs/sort3x3x3.btis` runs and emits the sorted 27 cubes
  in lex order; a Python oracle verifies.
- [ ] `programs/gcd.btis` runs for inputs (a, b) in {0, 1, 2} and
  emits the correct gcd; a Python oracle verifies.
- [ ] `programs/life3d_step.btis` runs one Bays' step on a
  specified input pattern and emits the new pattern; a Python
  oracle verifies.
- [ ] `ROADMAP.md:78-87` Stage A exit criteria are all checked
  (`[x]`) where applicable.
- [ ] All 51+ unit tests still pass; the bench drivers still pass.
- [ ] `git log` shows clean commits on `main`.
