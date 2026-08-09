# Changelog

All notable changes to the 3D-Ternary Machine project will be documented
in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

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
- **Programs.** 7 example `.btis` programs demonstrating rotation
  trajectories, balanced-ternary countdown, cube-addressed voxel
  patterns, and orbit exploration.

### Tests

- 31 unit tests covering cube encoding, symmetry bijectivity, orbit
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
  is via memory).
