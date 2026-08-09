# 3D-Ternary Machine

> A working prototype of a **Bi-Ternary / 3D-Ternary Instruction System**:
> a machine architecture whose primitive state is a balanced-ternary
> 3-vector in `{-1, 0, +1}^3`, and whose primitive operations are
> permutations of the 27-element cube induced by its geometric
> symmetries.

The fundamental machine primitive is the **cube** — the 27 points of
`{-1, 0, +1}^3`. It decomposes geometrically into 1 center, 6 axial,
12 face-diagonal, and 8 corner states. This decomposition is the
source of instruction semantics, not decoration.

A *program* in this architecture is a trajectory through the 27-cube:
each instruction is a permutation applied to the cube state `C`, and
execution is the sequence of cubes visited.

This repository holds:

| Path          | Contents                                                          |
|---------------|-------------------------------------------------------------------|
| `src/`        | Rust implementation: cube, symmetry group, ISA, VM, assembler, CLI |
| `python/`     | Python prototype: continuous-GA relaxation + discrete cube mirror |
| `programs/`   | `.btis` source programs (rotation, countdown, voxel patterns, W1-W5) |
| `docs/`       | Language reference, results, thesis-style positioning memo         |
| `benchmarks/` | Throughput comparison vs scalar balanced-ternary reference        |
| `hardware/`   | Behavioral Verilog model (Stage D — sketch, not synthesized)      |

## Quick start

```bash
cargo test                                       # 34 unit tests
cargo run -- programs/countdown.btis            # BT-IS CLI demo
cargo run --bin btis_bench --release 1000000    # ~90 M instructions/sec

python3 benchmarks/stage_b_word.py              # W1/W2/W4 comparison
python3 benchmarks/stage_b_w5.py                 # W5 48-O_h comparison
```

## What the project demonstrates

- A 27-state cube with the right symmetry structure: 1 + 6 + 12 + 8 = 27,
  every permutation is a bijection, and the octahedral group $O$ acts
  with the right orbit sizes (axial orbit = 6, corner orbit = 8).
- A small ISA whose operations are *rotations and reflections of the
  cube* (`ROT_X/Y/Z_90/180/270`, `REFLECT_*`, `NEG`) plus arithmetic,
  comparison, three-way branching, and cube-addressed memory.
- A virtual machine that executes the ISA with a per-step undo log
  (`vm.undo_all()`). The rotation / reflection subset is intrinsically
  reversible; the full ISA is journal-reversible.
- **34 unit tests passing.** End-to-end CLI working. Cross-implementation
  agreement between Rust and Python verified on all 27 cube states and
  all 13 built-in permutations.

## v0.3.1 benchmark results (honest)

The current measurement drivers (`benchmarks/stage_b_word.py`,
`benchmarks/stage_b_w5.py`) assert that BT-IS and SCALAR produce the
same output on each workload before reporting any instruction-count
ratio. The script exits non-zero on mismatch.

| workload | BT-IS | SCALAR | ratio (SCALAR / BT-IS) |
|---|---:|---:|---:|
| W1 rotations | 9 | 14 | 1.56× |
| W2 voxel_count (3 alive face neighbors) | 34 | 52 | 1.53× |
| W4 cubeadd_loop (10× of `C := C + C`) | 32 | 22 | 0.69× (loss) |
| W5 48 $O_h$ inner loop | 281 | 384 | 1.37× |

**BT-IS wins on three of four measured workloads** (W1, W2, W5).
**BT-IS loses on one** (W4, the pure cube-add recurrence). The
v0.2.0-niche 4.8× W4 headline and the v0.3.0-negative 0.67× W5 loss
were both artifacts of mismatched programs; the v0.3.1 numbers above
are the honest measurements. See `docs/RESULTS.md` and `VERDICT.md`
for the full analysis.

## Status

This is a research prototype, not a production system. At v0.3.1:

- **Code**: 34 unit tests passing, end-to-end CLI, Python
  cross-verification harness.
- **Benchmarks**: W1, W2, W4, W5 measurements re-run on a fair
  baseline with output-equality gates.
- **Hardware**: `hardware/btis_core.v` is a behavioral Verilog
  sketch. Real synthesis (yosys + nextpnr) has not been run and is
  environmentally blocked.
- **Turing-completeness**: claim withdrawn. The proof in
  `docs/turing_completeness.md` requires unbounded cube-keyed
  memory that the VM does not have. Re-deriving the proof is
  out of scope for v0.3.1.
- **Verdict**: **competitive on some workloads, slower on one, with
  no clear niche established.** The architecture is a clean
  reference implementation of a balanced-ternary cube machine; the
  thesis the project started with ("BT-IS is a useful machine
  architecture with a geometric primitive") is not supported by the
  v0.3.1 measurements. See `VERDICT.md`.

## Naming

- "BT-IS" — Bi-Ternary / 3D-Ternary Instruction System
- "3D-Ternary Machine" — descriptive project name (this repo)
- "VRML" — Vector-Rotational Machine Language (the original ChatGPT
  proposal name; abandoned because of the existing VRML acronym for
  Virtual Reality Modeling Language)

## License

Dual-licensed under MIT or Apache 2.0, at your option.

## See also

- `docs/ISA.md` — language reference and instruction encoding
- `docs/positioning.md` — comparison vs REBEL / Setnex / GA / VSA
- `docs/RESULTS.md` — full v0.3.1 measurement write-up
- `VERDICT.md` — v0.3.1 verdict
- `programs/` — annotated `.btis` example programs
- `python/vrml/` — Python cube module (continuous GA + discrete mirror)
