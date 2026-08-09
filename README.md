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
| `programs/`   | `.btis` source programs (rotation, countdown, voxel patterns)     |
| `docs/`       | Language reference (ISA.md) and thesis-style positioning memo     |
| `benchmarks/` | Throughput comparison vs scalar balanced-ternary reference        |

## Quick start

```bash
cargo test                              # 31 unit tests
cargo run -- programs/countdown.btis   # BT-IS CLI demo
cargo run --bin btis_bench --release 1000000   # ~90 M instructions/sec
```

| `benchmarks/` | Throughput comparison vs scalar balanced-ternary reference        |

## Roadmap

A staged plan to determine whether this architecture is *useful*,
with falsifiable predictions and explicit exit criteria for each
stage. See [`ROADMAP.md`](./ROADMAP.md) for the full plan.

 ## Quick start
## What the project demonstrates

- A 27-state cube with the right symmetry structure: 1 + 6 + 12 + 8 = 27,
  every permutation is a bijection, and the octahedral group `O` acts
  with the right orbit sizes (axial orbit = 6, corner orbit = 8).
- A small ISA whose operations are *rotations and reflections of the
  cube* (`ROT_X/Y/Z_90/180/270`, `REFLECT_*`, `NEG`) plus arithmetic,
  comparison, three-way branching, and cube-addressed memory.
- A virtual machine that executes the ISA and records every step's
  inverse, so a program is *automatically reversible* by `vm.undo_all()`.
- 31 unit tests passing. End-to-end CLI working. Cross-implementation
  agreement between Rust and Python verified on all 27 cube states and
  all 13 built-in permutations.

## Status

This is a research prototype, not a production system. It is intended
to demonstrate that the geometric computational ontology described in
`docs/positioning.md` can be made operational, and to provide a basis
for further investigation — including native hardware (FPGA), more
elaborate programs (3D Game-of-Life, balanced-ternary neural networks),
and benchmarks against real workloads.

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
- `docs/positioning.md` — comparison vs REBEL / Setnex / GA / VSA,
  including measurements
- `python/README.md` — continuous-GA prototype notes (pre-cube)
- `programs/` — annotated `.btis` example programs
