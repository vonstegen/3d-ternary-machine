# Stage B results

> Expressiveness comparison: BT-IS vs a SCALAR balanced-ternary
> RISC baseline. Measures state-mutating instruction counts on
> representative workloads.

## Method

For each workload we implement the same algorithm twice:

1. **BT-IS** — a `.btis` program assembled and run by the BT-IS CLI.
2. **SCALAR** — a Python emulator (`benchmarks/scalar_vm.py`) that
   interprets an explicit SCALAR program. SCALAR is the "no
   geometric primitives" baseline: it has 8 trit registers `R0..R7`,
   8 cube registers `C0..C7`, and per-coord scalar operations
   (`CADDX/Y/Z`, `CARRY_X/Y/Z`, `TCMP`, `TADD`, etc.). Geometric
   operations that BT-IS does in 1 op (e.g. `cube_add`) require
   SCALAR to do 6 ops (3 CADD + 3 CARRY).

The metric is *state-mutating instruction count*. Branch instructions
that don't mutate state are not counted.

We ran three workloads:

| ID | name              | what it stresses                |
|----|-------------------|---------------------------------|
| W1 | rotations         | pure 27-state LUT ops           |
| W2 | voxel_count       | cube memory + cube-add          |
| W4 | cubeadd_loop      | pure cube-add                   |

(W3 — three-way merge — was designed but found to be a
non-discriminator: both architectures have native 3-way compare and
3-way branch, so a lex compare costs the same on each. Skipped.)

## Results

| workload       | BT-IS | SCALAR | ratio |
|----------------|------:|-------:|------:|
| W1 rotations   | 10    | 13     | 1.30× |
| W2 voxel_count | 72    | 61     | 0.85× |
| W4 cubeadd_loop| 15    | 72     | 4.80× |

(`ratio` = SCALAR / BT-IS. Higher = BT-IS more efficient.)

## Interpretation

### W1 — rotations: BT-IS 1.30× faster

The win is small. Both architectures do 8 rotations; BT-IS uses
8 `rot_*` instructions, SCALAR uses 8 `APPLY_PERM` instructions.
The 3 BT-IS extras (loading the initial axis cube) plus the
SCALAR setup overhead explain the gap. This workload is *not* a
discriminator for the geometric-vs-scalar question.

### W2 — voxel_count: BT-IS 0.85× (slower)

This is the surprising negative result. The BT-IS implementation
uses 4 cube-adds via `cube_add`, but the surrounding setup
(moving cubes between `C` and `D0`/`D1`, storing back to memory)
requires many `MOV_CD` / `MOV_DC` / `STORE_D` ops. SCALAR
operates directly on trit registers without the cube↔trit
shuffling cost.

The architecture *does* have a cube-add primitive, but the
*register file* is not wide enough: only 4 cube registers means
binary operations like `a + b` need the operand at `mem[C]`
and the other operand at `C` simultaneously, requiring the
register-to-memory shuffle.

This finding is itself useful: it identifies a specific ISA
weakness — insufficient cube registers — and motivates the
"register file expansion" extension in `docs/RESULTS.md` Stage A.

### W4 — cubeadd_loop: BT-IS 4.80× faster

The pure geometric win. Each cube-add is 1 BT-IS instruction
versus 6 SCALAR instructions (`CADDX`, `CADDY`, `CADDZ`,
`CARRY_X`, `CARRY_Y`, `CARRY_Z`). Across 10 iterations, BT-IS
does 10 `cube_add`s + setup (15 total); SCALAR does 60 add/sub
+ 12 setup (72 total). The 4.8× ratio matches the theoretical 6×
ratio minus setup overhead.

## Conclusion of Stage B

**The central hypothesis H is partially supported.**

- BT-IS dominates on workloads that *consist of cube-adds* (W4:
  4.8× speedup). This is the geometric payoff: the cube-add
  primitive absorbs six per-coordinate SCALAR ops into one op.
- BT-IS loses on workloads that *require shuttling cubes between
  registers and memory* (W2: 0.85× slowdown). The current
  register file is too narrow.
- On workloads that don't exercise geometric primitives (W1),
  BT-IS and SCALAR are roughly tied.

The hypothesis as stated ("BT-IS uses strictly fewer state-mutating
instructions than SCALAR, attributable to geometric structure")
holds *when* the workload is dominated by cube-arithmetic, and
fails *when* it is dominated by register-to-memory traffic.

For Stage F (decision), this is mixed evidence. The geometric
advantage is real but conditional. Recommendation: **niche** —
useful for cube-arithmetic-heavy workloads (3D Game-of-Life step,
voxel neighborhood iteration, ternary neural-net primitives),
but not a general-purpose improvement.

## How to reproduce

```bash
cargo build
python3 benchmarks/stage_b.py
```

The workload programs are in `programs/w*.btis` and
`benchmarks/w*.py`.
