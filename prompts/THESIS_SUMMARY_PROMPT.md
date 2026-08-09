# Cross-reference prompt: 3D-Ternary Machine (BT-IS)

> A self-contained prompt for cross-referencing the BT-IS thesis with
> another AI platform. Drop this into a fresh chat and ask for
> critique, comparison, or extension.
>
> Version: matches repo state at tag `v0.2.0-niche`.

---

You are being asked to evaluate a research thesis about a novel
machine architecture. Please read the prompt carefully, then respond
with **critique, prior-art comparison, and concrete suggestions**.

---

## 1. The claim

A machine architecture called the **3D-Ternary Machine** (BT-IS)
whose **primitive state is a balanced-ternary 3-vector** in the
27-element set `{-1, 0, +1}^3` (called *the cube*), and whose
**primitive operations are permutations of cube states** induced by
the cube's rotational and reflection symmetries, can express useful
computation more efficiently than a scalar balanced-ternary RISC on
at least one class of workloads.

The decomposition of the cube is geometrically meaningful:
- **1 center** (0,0,0) — natural identity / halt
- **6 axial** states — primitive one-axis operations
- **12 face-diagonal** states — paired two-axis operations
- **8 corner** states — three-way combined operations

This decomposition is *not* decoration — it is the source of the
instruction semantics.

## 2. The model of computation

A BT-IS *program* is a sequence of permutations applied to a
single cube state `C`. Execution is a **trajectory through the
27-cube**. The cube's full symmetry group (the octahedral group
plus reflections, 48 elements total) is what makes the operations
non-trivial.

Key ISA features:

- `ROT_X/Y/Z_{90,180,270}` — nine axis-aligned rotations, each one
  27-entry LUT lookup (O(1))
- `REFLECT_X/Y/Z`, `NEG` — three reflections plus inversion
- `COMPOSE_R`, `INVERSE_R`, `APPLY_R` — eight rotor registers `R0..R7`
  holding composable permutations
- `CUBE_ADD` — full 27-state addition with carry through (x, y, z)
- `CMP` + `BR_NEG/BR_ZERO/BR_POS` — three-way comparison and branching
- `STORE_C` / `LOAD_C` — memory addressed by *cube coordinates*
- `vm.undo_all()` — every step is recorded; the program can be
  reversed in O(n) with one call

A register file of 4 cube data registers `D0..D3` plus the `C`
cube plus the `F` flag cube gives 6 simultaneous cube slots,
which the architecture needed for binary operations (added in
Stage A after we found that v0.1.0's single `C` register was
too narrow).

## 3. What we measured (Stages A–F of the roadmap)

This is a **research prototype**, not a production system. The
research followed a 6-stage falsifiable plan (ROADMAP.md in the
repo). The verdict after Stage F is **"niche"**.

### Stage B — instruction-count vs SCALAR baseline

We built a SCALAR reference emulator (REBEL-style balanced-ternary
RISC, no geometric primitives) and ran three workloads on both:

| workload       | BT-IS | SCALAR | ratio |
|----------------|------:|-------:|------:|
| W1 rotations   | 10    | 13     | 1.30× |
| W2 voxel_count | 72    | 61     | 0.85× |
| W4 cubeadd_loop| 15    | 72     | 4.80× |

`ratio` = SCALAR / BT-IS; higher means BT-IS more efficient.

**BT-IS dominates on cube-arithmetic-heavy workloads (4.8×)**
because `cube_add` absorbs six per-coordinate SCALAR ops into one
op. **BT-IS loses on workloads dominated by register-to-memory
shuffling (0.85×)** because the current 4 cube registers are
insufficient.

### Stage A — Turing completeness

Proved by reduction to Minsky's 2-counter machine. The
construction: a counter is encoded as a chain of cubes in
memory, one per balanced-ternary digit. INC/DEC walk the chain
with carry/borrow via `CYCLE_X`. The dispatch on zero vs nonzero
uses BT-IS's native 3-way branch. The reduction is polynomial.

### Stage C — reversibility

`examples/reversibility_demo.rs` runs a 6-instruction program,
then `vm.undo_all()` restores the initial `C`, clears `mem`, and
restores the register file. Confirmed:
```
initial C:   Cube((0, 0, 0))
after run C: Cube((-1, 0, 0))
after undo C: Cube((0, 0, 0))
undone 6 steps; mem_restored: true
RESTORED: true
```

Reversibility is **automatic** — every BT-IS program is reversible
by construction.

### Stage D — hardware feasibility

Behavioral Verilog model in `hardware/btis_core.v`. Area
*estimates* (not measurements): ~3000 LUTs + 9 BRAMs, fitting
comfortably on a low-cost iCE40-HX8K. SCALAR baseline ~2000
LUTs (no BRAM). Estimated BT-IS / SCALAR area ratio ~1.5×.
Real synthesis (yosys + nextpnr) is a Stage F follow-up.

### Stage E — domain studies (analysis only)

| workload | expected BT-IS ratio | implemented? |
|----------|----------------------:|---------------|
| 3D GoL step | 4–100× | scaffolding only |
| Voxel count | 0.85× (loss) | yes |
| Ternary NN primitives | ~1.3× | not yet |
| Robotics transforms | ~3× | not yet |

The 3D Game-of-Life step is the strongest natural case — the
27-cube *is* the 3D GoL lattice — but we have not implemented
a full step in BT-IS.

## 4. The honest verdict

**Niche.** The geometric primitive (`cube_add`) is a real win
on cube-arithmetic-heavy workloads (Stage B W4: 4.8×), but the
architecture does **not** show a general-purpose advantage over
SCALAR (Stage B W2: 0.85×). The reversibility and 3-way-branching
properties are real but qualitative, not measurable as
instruction-count wins (the SCALAR baseline has the same
TCMP + BR shape).

Recommendations from the project's VERDICT.md:

1. **Add D4..D7 cube registers** — likely flips the W2 voxel-
   count loss to a win.
2. **Implement a full 3D GoL step** in BT-IS — the flagship
   workload.
3. **Real FPGA synthesis** (yosys + nextpnr) to convert Stage D
   estimates into measurements.
4. **Re-decide at v0.3.0** after the above.

We explicitly did **not** archive the project: the niche is real,
the architecture is mathematically sound, and the implementation
is solid. The right next step is *focusing* on the niche, not
abandoning the work.

## 5. Prior art we considered

- **REBEL / Bos 2024**: balanced-ternary CPU; instructions are
  27-trit words. REBEL encodes Boolean-style computation in
  balanced ternary. BT-IS replaces Boolean semantics with cube-
  geometry semantics.
- **Setun (1958), Setnex (modern)**: balanced-ternary ISAs;
  sequences of trits, not 3-vectors.
- **Geometric algebra (Hestenes, Dorst)**: continuous. BT-IS uses
  the *discrete* octahedral group O as its rotation set.
- **Vector-symbolic architectures / hyperdimensional computing**:
  high-dim real-valued vectors. BT-IS is the balanced-ternary
  special case at dimension 3.
- **Cellular automata / multidimensional automata**: BT-IS can
  express 3D CA, but is not itself a CA — it's a machine that
  can *run* one.

## 6. The specific question for you

We'd like you to:

1. **Critique the central claim.** Is the geometric primitive
   genuinely interesting, or is it just an encoding trick? What's
   the strongest argument *against* this being worth pursuing?

2. **Compare to prior art.** Which existing architecture is
   BT-IS closest to? Did we misclassify any prior work in §5?

3. **Suggest workloads we missed.** Beyond 3D GoL, voxel
   processing, ternary NN, and robotics transforms — what
   workload should we benchmark next that would *truly* test
   the geometric-primitive claim?

4. **Suggest an ISA improvement.** The 4-cube-register file is
   a known weakness (W2 loss). What's the cleanest ISA extension
   that fixes this without bloating the architecture?

5. **Flag any factual errors.** We've made several non-trivial
   claims (Minsky reduction, octahedral-group orbit sizes,
   geometric-decomposition interpretation). Check our math.

---

## 7. Repository pointers (in case you want to read code)

- Repo: https://github.com/vonstegen/3d-ternary-machine
- Tag: `v0.2.0-niche`
- Math model + 31 unit tests: `src/cube.rs`, `src/symmetry.rs`
- ISA: `src/isa.rs`, `docs/ISA.md`
- VM with reversibility: `src/vm.rs`
- Fibonacci (cross-checked): `programs/fibonacci.btis`,
  `benchmarks/cross_check.py`
- Turing completeness proof: `docs/turing_completeness.md`
- Stage B measurements: `docs/STAGE_B_RESULTS.md`
- Stage C reversibility demo: `examples/reversibility_demo.rs`
- Verilog hardware model: `hardware/btis_core.v`
- Verdict: `VERDICT.md`

---

## 8. What we don't want

We do **not** want generic encouragement. We do **not** want a
"yes this is great" review without specific challenges. We want
sharp critique, especially of:

- The decomposition interpretation (1+6+12+8 = 27). Is the
  *number* 27 actually load-bearing for the architecture, or is
  it an artifact of dimension choice?
- The Minsky reduction in `docs/turing_completeness.md`. Is the
  chain-of-cubes counter encoding valid? Does the carry/borrow
  propagate correctly through `CYCLE_X`?
- The instruction-count comparison methodology. Did Stage B's
  SCALAR baseline get a fair implementation, or is it artificially
  inefficient?
