# BT-IS: a 27-state geometric instruction system

> A working note accompanying the prototype implementation. This is the
> "what is the thesis and how is it different from prior art" document.
> Not a finished paper — a positioning memo that the actual paper can
> be cut down from.

## 1. The claim

BT-IS (Bi-Ternary / 3D-Ternary Instruction System) is a machine
architecture in which the **primitive computational state** is a
*balanced-ternary vector* in `{-1, 0, +1}^3`, and the **primitive
computational operations** are *permutations of that 27-element set*
induced by the cube's rotational and reflection symmetries.

The cube's 27 states decompose geometrically into 1 center, 6 axial,
12 face-diagonal, and 8 corner states. This decomposition is *not*
notation — it is the source of instruction semantics:

- the center is the natural identity / halt / neutral element,
- the six axial states are primitive one-axis operations,
- the twelve face-diagonal states are coupled two-axis operations,
- the eight corner states are three-way combined operations.

The arithmetic, control-flow, and memory primitives of the machine are
derived from this 27-element geometric universe, not assigned as
arbitrary opcodes.

## 2. Why this is not yet another ternary ISA

Conventional balanced-ternary ISAs (Setun, Setnex, REBEL) use trits as
the *alphabet* of the machine but encode instructions as numeric
opcodes — sequences of trits in a fixed-length instruction word.
BT-IS is structurally different:

1. **State is a 3-vector of trits, not a sequence of trits.** A BT-IS
   machine word is `q = (x, y, z) ∈ {-1, 0, +1}^3`. Setun words are
   strings of trits. The geometry of `q` is part of its semantics; the
   ordering of trits in a Setun word is not.

2. **Operations are permutations of cube states, not numeric opcodes.**
   A rotation of the cube is a permutation of the 27-element set
   `{-1,0,+1}^3`. Every instruction in BT-IS is a permutation of cube
   states. This means there are exactly 27! possible operations, but
   the cube's symmetry group has only 24 orientation-preserving and
   48 orientation-reversing elements — *the natural operations form a
   small, geometrically meaningful subset.*

3. **Control flow is three-way, not two-way.** Balanced ternary gives
   a natural three-way comparison sign `(gt, eq, lt)` which is itself a
   cube. BT-IS's `CMP` instruction writes this sign into the flag
   register `F` and `BR_NEG / BR_ZERO / BR_POS` dispatch on it. There
   is no need for a separate "less than / equal / greater than"
   cascade of two-way branches.

4. **Memory addresses are cube coordinates.** `STORE n` writes `C` to
   `mem[Cube(n,n,n)]`. Memory is addressed by points in the cube, so
   locality of reference is geometric locality: two addresses differing
   by Hamming distance 1 are face-adjacent cells.

5. **Programs are trajectories through the 27-cube.** A BT-IS program
   is a sequence of permutations applied to a single cube state `C`. The
   sequence of cubes visited by `C` during execution is the program's
   *trajectory*. Reversibility becomes a property of the trajectory
   (each step has a known inverse permutation) rather than an
   architectural special case.

## 3. Where this sits relative to prior art

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
replaces Boolean-style computation with cube-geometry computation.

### Setun / Setnex

The original Setun (1958) used balanced ternary with 24 instructions.
Setnex is a contemporary clean-slate ternary ISA with 27-trit words
and three-way branching. Both encode balanced-ternary *values*; neither
encodes balanced-ternary *states as cube points* with geometric
semantics.

### Geometric algebra (GA)

Geometric algebra (Hestenes, Dorst) provides a mathematical language
for representing vectors, rotations, translations, reflections, and
projective operations as elements of a Clifford algebra. The continuous
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

The interesting number is *instructions per geometric operation*: BT-IS
needs 1 instruction to rotate a cube; the same is true of a scalar
balanced-ternary RISC. The architectural claim is not "fewer
instructions per geometric op" but "the cube *is* the operand": data,
instructions, addresses, and flags are all cubes. This uniformity is
what enables reversibility and three-way branching natively.

## 7. Open problems
implements the `Cl(3)` rotors. The prototype is mathematically
consistent with the BT-IS cube (rotors of 90° about axes correspond
to the cube's `ROT_*` instructions), but it is *not* the machine.

### Vector-symbolic architectures (VSA) / hyperdimensional computing

VSA represents symbols as high-dimensional real-valued vectors and
defines an algebra (binding, bundling, permutation) over them. HD
computing has been used for analogy, reasoning, and lightweight
classification.

VSA operates on *real-valued* high-dimensional vectors; BT-IS operates
on *ternary-valued* 3-dimensional vectors. The 27 states of the BT-IS
cube are not a "trick" — they are exactly the geometric space that the
3D balanced-ternary lattice defines. A VSA of dimension 27 with
balanced-ternary components recovers BT-IS.

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

> *Can geometric relationships among the 27 balanced-ternary states
> `{-1, 0, +1}^3` reduce the complexity of useful computation?*

This is the empirical question that BT-IS exists to test. The
hypothesis has two parts:

1. *Sufficiency.* BT-IS can express arithmetic, memory addressing,
   branching, and looping — i.e., the basic ingredients of universal
   computation. (Yes; demonstrated by the countdown and rotation
   trajectory programs in `programs/`.)

2. *Necessity / parsimony.* The geometric structure of the cube
   *reduces* the instruction count for certain natural workloads
   compared to a Boolean ISA expressing the same algorithm. (Open; not
   yet measured in the prototype.)

The prototype tests (1) — we can write non-trivial programs. It does
not yet test (2) — that requires benchmarks against a reference ISA
on workloads the architecture was designed for (3D vector rotation,
3D GoL, voxel neighborhood iteration, three-way branching).

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

Test coverage: 26 unit tests, all passing. End-to-end programs
demonstrate that geometric operations compose and that the trajectory
through cube state space is the program's execution.

## 6. Open problems

- **Reversibility.** A BT-IS program is a permutation of cube states
  composed at each step; every permutation has an inverse, so
  execution is in principle reversible. Implementing *automatic*
  reversibility (snapshotting the inverse trajectory alongside the
  forward one) is straightforward but not yet done.

- **Multi-word state.** The current VM has a single `C` cube as live
  state. Real programs need multiple live cubes (e.g. one for the
  loop counter, one for the current data value). A register file of
  cubes is a natural extension; the ISA currently has `C` and `F`.

- **Native hardware.** Once the abstract machine is mathematically
  sound, the question is whether the 27-entry LUTs can be implemented
  efficiently in dedicated hardware (FPGA, ASIC). The LUT structure
  is small enough (27 bytes per operation) that an FPGA could hold
  hundreds of distinct cube operations in on-chip memory.

- **Benchmarks.** The central hypothesis needs numbers. Candidate
  workloads: rotating a vector 1000 times, computing a GoL step on the
  27-cube, three-way-merge on a balanced-ternary sequence.

## 7. Naming

*BT-IS* (Bi-Ternary / 3D-Ternary Instruction System) is a working name.
The ChatGPT-suggested "bi-ternary machine language" is apt but the
"bi" prefix becomes misleading if the architecture is generalized
beyond `n = 2` or `n = 3` (cf. the general n-ternary transformation
space in the upstream discussion). *3D-Ternary* is precise about what
the prototype actually implements.
