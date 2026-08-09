# Cross-reference prompt: BT-IS code & implementation

> A variant of THESIS_SUMMARY_PROMPT.md for code-oriented AIs.
> Focus: implementation quality, ISA design tradeoffs, code-level
> correctness. Use this if you want the responding model to focus on
> the code rather than the theory.
>
> Version: matches repo state at tag `v0.2.0-niche`.

---

You are being asked to review the **implementation** of a novel
machine architecture called the 3D-Ternary Machine (BT-IS). The
theory is in the parent prompt; this one focuses on the code.

Please respond with: **code-quality critique, ISA design review,
specific bug reports, and refactor suggestions**.

---

## 1. Repo at a glance

```
github.com/vonstegen/3d-ternary-machine @ v0.2.0-niche
├── src/
│   ├── cube.rs              # 27-state primitive
│   ├── symmetry.rs          # 27-entry LUTs (LazyLock<Perm>)
│   ├── isa.rs               # opcode constants
│   ├── asm.rs               # symbolic assembler
│   ├── vm.rs                # register-file VM with undo log
│   ├── trace.rs             # per-step snapshot
│   ├── main.rs              # CLI driver
│   ├── lib.rs               # module re-exports
│   └── bin/dump_tables.rs   # JSON dump for cross-check
├── examples/reversibility_demo.rs
├── hardware/btis_core.v     # behavioral Verilog
├── programs/*.btis          # 9 example programs
├── benchmarks/*.py          # SCALAR emulator + cross-check + stage_b/c
└── docs/                    # ISA.md, turing_completeness.md, etc.
```

Rust 1.97, edition 2021. **34 unit tests passing.**

## 2. Specific things to review

### A. ISA design

- The ISA started at v0.1.0 with only `C`, `F`, and rotor
  registers `R0..R7`. Stage A forced an extension: 4 cube data
  registers `D0..D3` plus `MOV_CD`, `MOV_DC`, `STORE_D`,
  `LOAD_D`. **Was the right design reached, or is there a cleaner
  ISA that would have avoided this Stage A extension?**
- `cube_add` semantics: `C := C + mem[C]` (the *value* at the
  address that C holds). This is geometric — the address *is*
  the operand — but it forces the operand to be at a specific
  memory location. **Is there a more flexible formulation?**
- `CYCLE_X/Y/Z` step a coordinate through {-1, 0, +1} cyclically.
  Combined with `cube_add`, these give BT-IS full balanced-ternary
  arithmetic. **Should these be unified into a single `STEP` op
  with an axis selector?**

### B. Code quality in `src/vm.rs`

- The undo log uses an enum (`Undo`) with five variants. The
  `apply_undo` method has a `match` over these. **Is the enum
  design right, or would a trait-based approach be cleaner?**
- The `exec` method is a single large `match` on the opcode,
  ~200 lines. **Should the dispatch table be a function pointer
  array instead? Would that improve readability? Performance?**
- The `C` register is overloaded — it's both the implicit
  operand for many ops and the explicit argument for the
  three-way `CMP`. **Is this dual role a usability hazard?**

### C. Correctness

- Check `balanced_trit` in `src/vm.rs`. The truth table is:

  ```
  sum  -> (digit, carry)
   3   -> (0, 1)
   2   -> (-1, 1)
   1   -> (1, 0)
   0   -> (0, 0)
  -1   -> (-1, 0)
  -2   -> (1, -1)
  -3   -> (0, -1)
  ```

  **Is the table correct for ALL inputs in {-3..=3}?** Spot-check
  the boundary cases.

- Check `cube_add` in `src/vm.rs`. It sums `a + b` per-coordinate
  with carry. **Does the carry chain propagate correctly when
  multiple coordinates overflow simultaneously?**

- The Stage A Turing-completeness proof in
  `docs/turing_completeness.md` claims a reduction from
  Minsky's 2-counter machine. The encoding: a counter is a
  chain of cubes in memory, one cube per trit. INC walks
  forward, DEC walks backward. **Trace through a counter
  increment from 8 to 9 in the cube representation and verify
  the carry chain.**

### D. The assembler

- `src/asm.rs` uses a hand-written tokenizer. **Is there a
  standard Rust crate that would do better, and what would the
  tradeoff be?**
- The mnemonic table is ~30 entries hardcoded in a `match`.
  **Would a table-driven design scale better when the ISA grows?**

### E. The Verilog

- `hardware/btis_core.v` has placeholder `TODO` for several ops
  (IADD, ISUB, CMP, BR_*, JMP). **Which of these is hardest to
  implement in hardware, and why?**

### F. Specific files to look at

In rough priority order:

1. `src/vm.rs::cube_add` — the geometric primitive
2. `src/vm.rs::exec` — the dispatch table
3. `src/vm.rs::undo_all` — the reversibility mechanism
4. `src/symmetry.rs::Perm` — the 27-entry permutation type
5. `src/asm.rs::assemble` — the assembler
6. `programs/fibonacci.btis` — the only fully cross-checked program
7. `examples/reversibility_demo.rs` — confirms `vm.undo_all()`

---

## 3. What we want from you

- **Bug reports**: any code path that produces wrong output for
  specific inputs. Be specific (file, line, input, expected vs
  actual).
- **Refactor suggestions**: where the code is harder to read
  than it needs to be, or where Rust idioms are violated.
- **ISA improvements**: if you see a way to fix the W2 voxel-
  count loss (Stage B) with a clean ISA change, propose it.
- **Specific test cases**: if a corner case isn't covered by
  the existing 34 unit tests, suggest a test.

---

## 4. What we don't want

- General "this is good" feedback without specifics.
- Suggestions to switch languages or rebuild from scratch — we
  want code-level critique of what's there.
- Praise for the abstraction. We want stress tests.

---

## 5. Repo pointers

- Repo: https://github.com/vonstegen/3d-ternary-machine
- Tag: `v0.2.0-niche`
- Tests: `cargo test` (34 passing)
- Benchmarks: `python3 benchmarks/stage_b.py` for instruction-
  count comparison vs SCALAR baseline
- Cross-check: `python3 benchmarks/cross_check.py` runs the BT-IS
  Fibonacci and compares to the Python reference
