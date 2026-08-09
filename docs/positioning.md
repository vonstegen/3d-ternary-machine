# BT-IS: a 27-state geometric instruction system

> A working note accompanying the prototype implementation. This is the
> "what is the thesis and how is it different from prior art" document.
> Not a finished paper — a positioning memo that the actual paper can
> be cut down from.
>
> Includes corrections received via external critique (see
> `docs/CRITIQUE_RESPONSE.md`).

## 1. The claim

A machine architecture called the **3D-Ternary Machine** (BT-IS)
whose **primitive state is a balanced-ternary 3-vector** in the
27-element set `{-1, 0, +1}^3` (called *the cube*), and whose
**primitive operations include permutations of cube states**
induced by the cube's rotational and reflection symmetries, can
express useful computation more efficiently than a scalar
balanced-ternary RISC on at least one class of workloads.

The cube decomposes geometrically into 1 center, 6 axial, 12
face-diagonal, and 8 corner states. This decomposition is *not*
sacred — it's the `Σ C(3,k) · 2^k` orbit partition of nonzero
coordinates, which exists identically at every dimension. The
*number* 27 is special only as the smallest nontrivial case
where the symmetry group (octahedral, 24 rotations) is interesting.

The architecture has **two algebras on the cube**: a permutation
algebra (rotations, reflections, compositions, inverses) and an
arithmetic algebra (cube-add with carry through x, y, z). These
do not unify algebraically. The arithmetic algebra treats
coordinates as positional digits with place value; the
permutation algebra treats them as interchangeable spatial axes.
BT-IS ships both; the geometric claim is *about the permutation
algebra*, not about the arithmetic one.

## 2. Why this is not yet another ternary ISA

Conventional balanced-ternary ISAs (Setun, Setnex, REBEL) use trits as
the *alphabet* of the machine but encode instructions as numeric
opcodes — sequences of trits in a fixed-length instruction word.
BT-IS is structurally different:

1. **State is a 3-vector of trits, not a sequence of trits.** A BT-IS
   machine word is `q = (x, y, z) ∈ {-1, 0, +1}^3`. Setun words are
   strings of trits. The geometry of `q` is part of its semantics; the
   ordering of trits in a Setun word is not.

2. **Operations are permutations of cube states.** A rotation of the
   cube is a permutation of the 27-element set
   `{-1, 0, +1}^3`. Every instruction in BT-IS is a permutation of cube
   states. This means there are exactly 27! possible operations, but
   the cube's symmetry group has only 24 orientation-preserving and
   48 orientation-reversing elements — *the natural operations form
   a small, geometrically meaningful subset.*

3. **First-class group elements.** Rotor registers `R0..R7` hold
   permutations as values. They can be composed (`COMPOSE_R`),
   inverted (`INVERSE_R`), and applied to cube state (`APPLY_R`).
   This is in the lineage of Pendulum-style reversible machines and
   Toffoli-style conservative logic.

4. **Control flow is three-way, not two-way.** Balanced ternary gives
   a natural three-way comparison sign `(gt, eq, lt)` which is itself a
   cube. BT-IS's `CMP` instruction writes this sign into the flag
   register `F` and `BR_NEG / BR_ZERO / BR_POS` dispatch on it.

5. **Memory addresses are cube coordinates.** `STORE_C` writes `C` to
   `mem[C]`; `LOAD_C` reads `mem[C]` into `C`. The address *is* the
   cube state. Locality of reference is geometric locality: two
   addresses differing by Hamming distance 1 are face-adjacent cells.

6. **Intrinsic reversibility holds for the rotation/reflection
   subset.** Each `ROT_*` / `REFLECT_*` / `NEG` op is a permutation
   with an inverse in the group, so the rotation/reflection subset
   is intrinsically reversible. The full ISA (including
   `cube_add`, `STORE_C`, arithmetic) is *not* intrinsically
   reversible — `vm.undo_all()` is a Bennett-style journal-based
   history reversal that works for any machine and is not a
   distinguishing property of BT-IS.

## 3. Where this sits relative to prior art

### Closer-than-REBEL prior art: reversible / group-element machines

The architectural feature that *is* distinctive about BT-IS is not
"ternary" or "27-state" — it's the rotor registers (`R0..R7`) and
the first-class manipulation of group elements (`COMPOSE_R`,
`INVERSE_R`, `APPLY_R`). This lineage includes:

- **Toffoli / Fredkin / conservative logic**: reversible gates,
  permutation-based computation.
- **Pendulum (Frank, 2017)**: reversible computing with explicit
  group-element manipulation as first-class values. The rotor
  registers in BT-IS are Pendulum-style.
- **Group-equivariant computation (Cohen/Welling, E(3)-NNs)**: the
  cube's symmetry group `O_h` is the natural domain for
  group-averaged kernels. BT-IS's group operations are the
  primitive that an equivariant network would consume.

BT-IS should be understood as a *cube-lattice group machine*, not
as "another balanced-ternary ISA." The ternary alphabet is
incidental; the *group* is the substance.

Adjacent territory worth flagging:

- **Ternary content-addressable memory**: STORE/LOAD addressed
  by cube coordinates is a small associative structure.
- **GF(3) linear-algebra machines**: 3-trit values are GF(3)
  elements. Cube arithmetic is GF(3)^3 linear-ish algebra.

(REBEL remains a comparison point because it is the most recent
balanced-ternary machine, but it is *not* the closest prior art.)

### REBEL / Bos 2024

Steven Bos's 2024 PhD dissertation (*Beyond 0 and 1*, University of
South-Eastern Norway) develops REBEL, a balanced-ternary CPU and ISA.
REBEL's instructions are 27-trit words encoding conventional RISC-like
operations (load, store, add, branch, etc.) but represented in
balanced ternary. REBEL is the strongest *existing* prior art on
ternary machine architecture.

BT-IS is *not* a REBEL variant. The differences:

|                | REBEL               | BT-IS                 |
|----------------|---------------------|-----------------------|
| state          | 27-trit word        | 27-state 3-vector     |
| instruction    | numeric opcode      | permutation of states |
| control flow   | two-way (binary)    | three-way (ternary)   |
| addressing     | integer address     | cube coordinate       |
| arity          | RISC-like 2-op      | single-state update   |

REBEL encodes Boolean-style computation in balanced ternary. BT-IS
replaces Boolean semantics with cube-geometry semantics — for the
permutation subset. The arithmetic subset (cube-add) is a
3-trit scalar word add, which REBEL could equally well express.

### Setun (1958), Setnex (modern)

Balanced-ternary ISAs; sequences of trits in instruction words, not
3-vectors. Closest comparison point but not the closest prior art.

### Geometric algebra (GA)

Geometric algebra (Hestenes, Dorst) provides a mathematical language
for representing vectors, rotations, translations, reflections, and
projective operations as elements of a Clifford algebra. The continuous
relaxation at `/tmp/vrml_proto/python/` (Vec, Bivec, Trivec, Rotor)
implements the `Cl(3)` rotors. The prototype is mathematically
consistent with the BT-IS cube (rotors of 90° about axes correspond
to the cube's `ROT_*` instructions), but it is *not* the machine.

### Vector-symbolic architectures (VSA) / hyperdimensional computing

VSA represents symbols as high-dimensional real-valued vectors and
defines an algebra (binding, bundling, permutation) over them.

We previously claimed that "BT-IS is a VSA of dimension 27 with
balanced-ternary components." That framing is wrong. VSA's
useful properties (quasi-orthogonality, concentration of measure,
robust superposition) emerge at *high* dimension (typically
d=1000+). At d=3, BT-IS shares only the alphabet (ternary symbols);
the statistical properties that make VSA useful do not appear.
We retain the comparison only to note that BT-IS is *not* in
the VSA family.

### Cellular automata / multidimensional automata

Wolfram's cellular automata and the broader theory of multidimensional
automata define computation on regular grids. The 27-cube is a
`3 × 3 × 3` grid, so BT-IS can express cellular automata (a GoL step
over the cube is a permutation of cube states). But BT-IS is not
itself a CA — it is a *machine language* in which programs and data
share the same geometric space.

### GPUs / SIMD / tensor units

GPU programming models treat data as vectors of fixed-width numbers and
operations as SIMD kernels over those vectors. BT-IS treats data as a
3-vector of balanced trits and operations as 27-state permutations.
Both use vectors; BT-IS uses fewer, smaller, and more structured
vectors.

## 4. The central hypothesis

> **H.** There exists a non-trivial class of algorithms `A` for which
> a `BT-IS` implementation uses *strictly fewer* state-mutating
> instructions than a `SCALAR` (REBEL-style 27-trit word) implementation,
> and the reduction is attributable to *the symmetry group of the cube*
> (rotations, reflections, compositions) — not just to a difference
> in representation.

Note the revision: the original hypothesis said "geometric
structure of the cube." After critique, the testable claim is
narrower: *the symmetry group* — not the arithmetic algebra —
must do work that a word-width SCALAR baseline can't do as cheaply.

### Falsifiable predictions

P1. Three-way comparison (`CMP` + 3-way branch) replaces cascades of
    2-way branches in real code at non-trivial frequency.
P2. Cube-addressed memory (`STORE_C` / `LOAD_C`) collapses what would
    be multiple load/store + arithmetic ops in `SCALAR` into one
    geometric op, on geometric-locality workloads.
P3. **Intrinsic** reversibility of the rotation/reflection subset
    (each op is a group element with an inverse) — distinct from
    the journal-based reversibility of the full ISA.
P4. On workloads that exercise the *group structure itself*
    (e.g. polycube/voxel canonicalization under O_h, group-equivariant
    convolution), BT-IS instruction count is ≤ SCALAR with ≥10%
    reduction on ≥50% of workloads.
P5. On native hardware (FPGA / ASIC), BT-IS area ≤ 2× SCALAR for
    the same per-op cost.

### Success criteria

- **Useful (continue general):** ≥3 of P1–P5 confirmed, P4 ≥ 10%
  reduction on ≥3 workloads, P5 within 2× area.
- **Niche (focused):** the symmetry-group subset (P4) gives a real
  win on a small set of workloads.
- **Not worth pursuing (archive):** P4 fails on every workload
  we try, or P3 fails (no intrinsic reversibility — already shown).

## 5. What the prototype demonstrates

`btis/` (Rust crate) and `vrml_proto/python/` (continuous GA
reference) together implement:

- The 27-state cube primitive with `1 + 6 + 12 + 8` decomposition
  (`src/cube.rs`, `tests`).
- The full octahedral symmetry group (24 rotations) plus reflections
  and negation as 27-entry lookup tables (`src/symmetry.rs`).
- A BT-IS instruction set with rotation/reflection, arithmetic,
  comparison, three-way branching, memory, and halt (`src/isa.rs`).
- A symbolic assembler and a virtual machine that executes the ISA
  (`src/asm.rs`, `src/vm.rs`).
- A CLI driver: `cargo run -- programs/hello.btis` etc.
  (`src/main.rs`).

Test coverage: 34 unit tests, all passing. End-to-end programs
demonstrate that geometric operations compose and that the
trajectory through cube state space is the program's execution.

## 6. Measurements

Release-mode throughput on a single thread (`aarch64-unknown-linux-gnu`,
Rust 1.97, `opt-level = 3`, `lto = true`):

| implementation                    | throughput                          |
|-----------------------------------|-------------------------------------|
| `btis_pure_lut` (raw 27-entry LUT)| ~11 billion LUT lookups/sec         |
| `btis_bench` (BT-IS VM, in-process)| ~90 million instructions/sec        |
| `bench_rot.btis` via CLI          | ~9 kips (dominated by process spawn) |
| Python reference (scalar RISC)    | ~70 million instructions/sec        |

Both BT-IS and the scalar reference execute *one* cube rotation per
instruction. The instruction count for a workload is the same. The
~30% BT-IS advantage over Python reflects Rust vs interpreter
overhead, not architectural difference.

### Stage B (corrected) — instruction-count vs word-width SCALAR

The headline BT-IS advantage after correcting for a fair word-width
baseline (not a per-coord-strawman):

| workload       | BT-IS | SCALAR (word-width) | ratio |
|----------------|------:|--------------------:|------:|
| W1 rotations   | 10    | 14                  | 1.40× |
| W2 voxel_count | 72    | 61                  | 0.85× |
| W4 cubeadd_loop| 15    | 22                  | 1.47× |

The 1.5× ratio on W4 reflects the operand-location advantage (BT-IS
uses `C + mem[C]` where SCALAR needs pre-loaded registers), not a
3-wide-vs-1-wide arithmetic advantage. The corrected verdict
honestly is: marginal win on arithmetic-heavy workloads,
loss on register-shuffle-heavy workloads.

A *symmetry-group-exercising* workload (polycube canonicalization
under O_h, group-equivariant convolution) is the next benchmark
to test. See `docs/CRITIQUE_RESPONSE.md` for the full response.

## 7. Honest corrections

The project has been corrected in response to external critique.
The full response is in `docs/CRITIQUE_RESPONSE.md`. Summary:

- **Reversibility**: the full ISA is *not* intrinsically
  reversible; only the rotation/reflection subset is. The
  journal-based `vm.undo_all()` works for any machine. The
  earlier claim was overstated.
- **Prior art**: BT-IS is closer to Pendulum / reversible
  group-element machines than to REBEL. The ternary alphabet
  is incidental; the group is the substance.
- **VSA framing**: removed. d=3 is not "VSA in 3 dimensions";
  VSA's properties require high dimension.
- **Turing-completeness claim** (withdrawn at v0.3.1): the
  proof in `docs/turing_completeness.md` was unsound. The
  encoding required unbounded cube-keyed memory that the VM
  does not have (only 27 keys), and the DEC algorithm was
  incorrect. See the v0.3.1 rewrite of that file.
- **SCALAR baseline** (Stage B): the original was per-coord
  with explicit carries. Replaced with a word-width ALU
  (`WADD cd1, cd2` in one instruction), which is what REBEL
  actually does. The 4.8× headline collapses to 1.47×.

## 8. What this is *not*

It is **not** a commitment to a release schedule. Stages B and D
might fail and produce "niche" or "archive" outcomes; that's a
success for the project (we *learned something*), not a failure.

It is **not** advocacy. The hypothesis `H` is falsifiable, and the
verdict could be "no, this isn't useful". The roadmap respects that.

It is **not** a complete research program. A complete program
would also include: comparison to other recent ternary / vector /
geometric ISAs (Bos 2024, KAIST ART-9, Pendulum, Frank's reversible
machines, E(3)-equivariant NNs), a published paper, and external
review. Those are out of scope for this repo.

## 9. Open problems

- **The register-file weakness** (W2 loss). The fix proposed by
  critique is fused `LOAD_CR` / `STORE_CR` (memory ops with a rotor
  operand), not wider registers. Implement and re-measure.
- **A symmetry-group workload**. Polycube/voxel canonicalization
  under O_h, or O_h-equivariant convolution, would test the actual
  distinctive feature of the architecture (the rotor registers
  and group composition), not just cube arithmetic.
- **Native hardware synthesis**. Stage D's area estimates are
  estimates. Real yosys + nextpnr (or Vivado) synthesis is the
  next step.
- **Full 3D Game-of-Life step** in BT-IS. The scaffolding is in
  `programs/life3d_step.btis`; a full step is a Stage F follow-up.

## 10. Naming

*BT-IS* (Bi-Ternary / 3D-Ternary Instruction System) is a working name.
The ChatGPT-suggested "bi-ternary machine language" is apt but the
"bi" prefix becomes misleading if the architecture is generalized
beyond `n = 2` or `n = 3` (cf. the general n-ternary transformation
space in the upstream discussion). *3D-Ternary* is precise about what
the prototype actually implements.
