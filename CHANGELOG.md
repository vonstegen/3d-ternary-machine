# Changelog

All notable changes to the 3D-Ternary Machine project will be documented
in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.1] — 2026-08-09

### Changed

- **Bench output-equality gate.** `benchmarks/stage_b_word.py` and the
  new `benchmarks/stage_b_w5.py` now assert that BT-IS and SCALAR
  produce the same output on every workload before reporting any
  instruction-count ratio. Scripts exit non-zero on mismatch. This
  caught the v0.2.0-niche and v0.3.0-negative measurement errors
  described below.
- **Honest W4 measurement.** The previous W4 program computed
  different recurrences on BT-IS and SCALAR. Both programs now
  compute 10 iterations of `C := C + C` starting from `(1, 1, 1)`.
  Result: **BT-IS 0.69× slower** (32 vs 22 mutating steps). The
  v0.2.0-niche 1.47× win was on mismatched programs; the
  v0.2.0-niche 4.8× original win was on a trit-granular SCALAR
  strawman. The cube-add primitive is not a load-bearing win.
- **Honest W5 measurement.** The previous W5 program was a
  single 7-term composition mis-reported as the canonicalization
  flagship. The new W5 (`programs/w5_canon.btis` and
  `benchmarks/w5_canon/`) implements the actual inner loop of
  voxel canonicalization: apply all 48 elements of $O_h$ to
  `(1, 0, 0)` and emit. Result: **BT-IS 1.37× faster** (281 vs 384
  mutating steps), because BT-IS's rotor-register setup is
  cheaper than SCALAR's per-iteration cube rebuild.
- **W2 SCALAR bug fix.** `benchmarks/w2_word_scalar.py` had a
  register-index bug that made `C1` constant `(-1, -1, -1)`, plus
  a missing accumulator reset. Fixed; the new W2 SCALAR matches
  BT-IS on the 3-alive-neighbor test.
- **`VERDICT.md` and `docs/RESULTS.md` rewritten.** Both
  v0.2.0-niche ("niche") and v0.3.0-negative ("not worth pursuing")
  verdicts are retracted as artifacts of mismatched programs. The
  v0.3.1 verdict is: **BT-IS is competitive with a fair SCALAR
  baseline on three of four measured workloads** (W1 1.56×, W2
  1.53×, W5 1.37× wins; W4 0.69× loss), with no clear niche
  established.
- **Turing-completeness claim withdrawn.** The proof in
  `docs/turing_completeness.md` requires unbounded cube-keyed
  memory, but the VM has at most 27 keys. The claim is unverified
  until the proof is rewritten with an unbounded address register.

### Added

- **`benchmarks/w5_canon/`** — the W5 canonicalization benchmark
  on a single cube. `oh.py` generates the 48 $O_h$ permutations
  (24 proper + 24 improper); `verify.py` asserts group axioms
  (closure over all 2304 pairs); `factor.py` BFS-finds a
  minimum-length factorization of each permutation into named
  BT-IS rotor ops (max factor length: 3); `gen_w5_btis.py` emits
  the BT-IS program; `w5_scalar.py` is the SCALAR equivalent.
- **`benchmarks/stage_b_w5.py`** — W5 driver with output-minset
  equality check.
- **`programs/w5_canon.btis`** — generated BT-IS W5 program.
- **REFLECT_X / REFLECT_Y / REFLECT_Z constants** in
  `benchmarks/scalar_vm_word.py` so the SCALAR can mirror
  BT-IS's `reflect_x` / `reflect_y` / `reflect_z` ops.
- **Documentation** — `docs/STAGE_W5_RESULTS.md` rewritten to
  describe the actual 48-symmetry inner loop.

### Removed

- **Tag `v0.3.0-negative` deleted** — the tag pointed at a commit
  whose headline W5 claim ("BT-IS = 21 ops, SCALAR = 14, BT-IS
  slower") was on a 7-term composition, not the canonicalization
  experiment. The new W5 (real canonicalization inner loop) is
  the opposite: BT-IS 1.37× faster. Preserved in git history.

### Honest summary

- BT-IS wins on W1, W2, W5 (1.56×, 1.53×, 1.37×).
- BT-IS loses on W4 (0.69×) when both compute the same `C := C +
  C` recurrence.
- The v0.2.0-niche 4.8× W4 headline and v0.2.0-niche 1.47× corrected
  W4 number were both artifacts of comparing different programs
  on each side.
- The v0.3.0-negative 0.67× W5 loss was on a 7-term composition,
  not the canonicalization experiment.
- Verdict: **competitive on some workloads, slower on one, with
  no clear niche established.** See `VERDICT.md`.

## [0.3.0-negative] — 2026-08-08 (SUPERSEDED — tag deleted at v0.3.1)

### Added

- **W5 7-term composition workload** (`programs/w5_compose.btis`,
  `benchmarks/w5_scalar.py`). This was reported as the
  "canonicalization flagship" but was actually a single
  composition. The real canonicalization experiment was not run.

### Results

- W5 (7-term composition): BT-IS 21 ops, SCALAR 14 ops, BT-IS 0.67×
  slower. **This number is on a different workload than v0.3.1's
  W5.** See v0.3.1 for the actual 48 $O_h$ inner-loop result.

### Verdict (retracted)

- "Not worth pursuing" was the v0.3.0-negative verdict, based on
  the 7-term composition result above and the v0.2.0-niche W4
  1.47× win. Both numbers were artifacts of comparing different
  programs on each side. The v0.3.1 re-measurement supersedes.

## [0.2.1-corrected] — 2026-08-08

### Added

- Word-width SCALAR baseline (`benchmarks/scalar_vm_word.py`,
  `WADD cd1, cd2`) replacing the trit-granular strawman. The fair
  baseline uses one cube-wide ALU op per cube-add, matching
  REBEL's "27-trit word" model. The headline Stage B number
  collapsed from 4.80× to 1.47× on W4.
- Restated reversibility claim: intrinsic for the rotation /
  reflection subset, journal-based for the full ISA. The
  v0.1.0 "every BT-IS program is reversible by construction"
  was an overclaim.
- Stage D status (`docs/STAGE_D_RESULTS_status.md`): synthesis
  environmentally blocked (no yosys / no sudo).

## [0.2.0-niche] — 2026-08-08 (SUPERSEDED at v0.3.1)

### Added (Stages A-F)

- **Data registers D0..D3** (cubes), with `MOV_CD`, `MOV_DC`,
  `STORE_D`, `LOAD_D` ops. Necessary to hold two cubes
  simultaneously for binary operations.
- **Cube arithmetic**: `CYCLE_X/Y/Z` (cyclic per-coord, no
  saturation), `CUBE_ADD` (full 27-state addition with carry
  through x, y, z).
- **Stage A program**: `fibonacci.btis` computing F(0..9) mod 27
  using cube-additive Fibonacci in Z_3^3, cross-checked against
  `benchmarks/cube_arith.py`.
- **Stage B programs**: `w1_rotations.btis`, `w2_voxel_count.btis`,
  `w4_cubeadd.btis`, with SCALAR equivalents and a benchmark
  driver.
- **Stage C harness**: `benchmarks/stage_c.py` runs an
  in-process reversibility demo (`examples/reversibility_demo.rs`)
  and counts branch ops across existing programs.
- **Stage D hardware model**: `hardware/btis_core.v`, a behavioral
  Verilog model of the BT-IS core with area estimates.
- **Documentation**: `docs/turing_completeness.md`,
  `docs/STAGE_B_RESULTS.md`, `docs/STAGE_C_RESULTS.md`,
  `docs/STAGE_D_RESULTS.md`, `docs/STAGE_E_RESULTS.md`,
  `docs/RESULTS.md`, `VERDICT.md`.

### Results (v0.2.0-niche; pre-fix, pre-correction)

- **Stage B** (instruction-count vs SCALAR): BT-IS wins on cube-add
  workload (W4: 4.8x on a trit-granular strawman; 1.47x on the
  corrected word-width SCALAR). **The 1.47x win was on mismatched
  programs** — BT-IS did `C := C + mem[C]` (a no-op after iter 0)
  while SCALAR did `C0 := C0 + C0` (real work). The v0.3.1 W4
  re-measurement on the same recurrence gives 0.69x (BT-IS
  slower). See v0.3.1 changelog.
- **W1**: BT-IS 1.40x on a 7-op sequence. The v0.3.1 W1 fix makes
  both programs compute the same op sequence on `(1, 0, 0)`; the
  ratio is 1.56x.
- **W2**: BT-IS 0.85x on a partial program that summed 4 of 8
  neighbors with different sequences on each side. The v0.3.1
  W2 fix uses 3 alive neighbors with matching sequences; the
  ratio is 1.53x.
- **Stage C**: reversibility automatic and constant-time per
  step; 3-way branching present in both architectures so not a
  discriminator. (The "automatic reversibility" claim was
  retracted in v0.2.1-corrected.)
- **Stage D**: estimated ~3000 LUTs + 9 BRAMs on a low-cost FPGA,
  ~1.5x the SCALAR baseline's area (estimates only, no
  synthesis).

### Verdict (v0.2.0-niche; retracted at v0.3.1)

**Niche.** This verdict was based on the 1.47x W4 win, which was
on mismatched programs. The v0.3.1 re-measurement gives 0.69x
(BT-IS slower) on the same `C := C + C` recurrence. The
"niche" label is retracted at v0.3.1.

## [0.1.0] — 2026-08-08

### Added

- **Cube primitive.** The 27-state balanced-ternary 3-vector
  `{-1, 0, +1}^3` packed into a single `u8`. Decomposition into 1 center,
  6 axial, 12 face-diagonal, 8 corner states verified by tests.
- **Cube symmetry group.** 9 axis-aligned rotations, plus negation,
  plus the three axis-aligned reflections, plus the inverse function,
  all as 27-entry lookup tables. Lazy-initialized via `std::sync::LazyLock`
  to keep the build simple on stable Rust.
- **BT-IS ISA.** Opcodes for rotation, reflection, negation, rotor
  composition, arithmetic (saturating balanced ternary on `C.x`),
  comparison (3-way sign in `F`), three-way branching, call/ret,
  full-cube-addressed memory, and halt. See `docs/ISA.md` for the full
  encoding.
- **Virtual machine.** A register-file VM executing the ISA, with
  per-step reversibility (`vm.undo_all()` restores initial state).
- **Symbolic assembler.** `loadc`, `load_axis`, `rot_*`, `reflect_*`,
  `neg`, `compose_r`, `apply_r`, `mov_r`, `load_r`, `iadd/isub/imul`,
  `cmp`, `br_*`, `br_axis`, `jmp`, `call`, `ret`, `store`, `load`,
  `store_c`, `load_c`, `halt`, with `label NAME` markers.
- **CLI driver.** `cargo run -- programs/foo.btis [--trace]`.
- **Python prototype.** Continuous geometric-algebra reference (`Vec`,
  `Bivec`, `Trivec`, `Rotor` over reals) plus a discrete cube mirror
  with the same 27-state semantics as the Rust crate.
- **Cross-verification.** Rust crate dumps its 13 permutation tables to
  JSON; Python script (`benchmarks/verify.py`) compares against the
  Python implementation and asserts agreement on all 27 cube states
  and all 13 permutations.
- **Benchmarks.** `btis_bench` (in-process VM), `btis_pure_lut`
  (raw 27-entry LUT lookup), `bench_rot.btis` + `bench.sh` (CLI path),
  `benchmarks/reference.py` (Python scalar baseline). Release-mode
  throughput: ~90 M instructions/sec in-process; pure-LUT baseline
  ~15 G LUT lookups/sec.
- **Documentation.** `docs/ISA.md` (language reference), `docs/positioning.md`
  (thesis-style comparison vs REBEL, Setnex, geometric algebra, vector
  symbolic architectures, with measurements).
- **Programs.** 16 example `.btis` programs demonstrating rotation
  trajectories, balanced-ternary countdown, cube-addressed voxel
  patterns, and orbit exploration.

### Tests

- **34 unit tests** covering cube encoding, symmetry bijectivity, orbit
  structure, ISA dispatch, register file, full-cube memory,
  reversibility, call/ret, and the assembler.
- Cross-verification: Rust ↔ Python agreement on 27 cube states and
  13 permutations.

### Limitations

- No native hardware prototype.
- No benchmarking on workloads the architecture was designed for
  (3D Game-of-Life, balanced-ternary neural networks).
- ISA is small and intentionally so; missing: floating-point ops,
  indirect memory addressing beyond `STORE_C`/`LOAD_C`, multi-word
  state (the register file has only one `C` cube; multi-word state
  is not supported beyond the 4 D registers added in v0.2.0).
- The "every BT-IS program is automatically reversible" claim
  was overstated. Journal-based `vm.undo_all()` works for any
  machine; intrinsic reversibility holds only for the rotation /
  reflection subset.
- The Turing-completeness argument in `docs/turing_completeness.md`
  is unsound: it assumes unbounded cube-keyed memory, but the VM
  has at most 27 keys. The claim is withdrawn at v0.3.1.
