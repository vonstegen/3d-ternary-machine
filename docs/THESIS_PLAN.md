# Thesis plan

> How the existing BT-IS prototype could be turned into a Masters
> thesis and what additional work would be required for a PhD-level
> research contribution.
>
> This document is a *plan*, not the thesis itself. The thesis would
> have to be written from scratch; this plan tells you what each
> section could contain.

---

## 1. The Masters-level paper

A Masters thesis is the right scope for v0.2.0-niche as it stands.
The claim is *modest* (a niche advantage on cube-arithmetic
workloads, demonstrated empirically) and *defensible* (the
measurements exist, the math is sound, the verdict is honest).

### Suggested title

> **The 3D-Ternary Machine: A Cube-Geometry Machine Architecture
> with Verified Reversibility and a Niche Instruction-Count
> Advantage**

### Target venue

A Masters thesis at a CS department; a workshop paper at venues
like:

- **MEMOCODE** — IEEE/ACM International Conference on Formal
  Methods and Models for System Design
- **ARITH** — IEEE Symposium on Computer Arithmetic
- **DCFS** — IFIP/IEEE International Conference on Dependable
  Systems and Networks

The Masters paper does *not* need a top-tier venue. The honest
verdict ("niche") is a feature for a thesis committee, not a
weakness — the contribution is well-defined and falsifiable.

### Structure (8 chapters)

**Chapter 1 — Introduction (10 pp)**

- The 3D-ternary cube as a primitive machine element.
- Why geometric primitives might matter for instruction count.
- The roadmap approach: 6 stages, falsifiable exit criteria.
- The verdict in one paragraph.

**Chapter 2 — Background (15 pp)**

- Balanced ternary history (Setun 1958, REBEL 2024, Setnex).
- Geometric algebra (Hestenes, Dorst) and its continuous relaxation.
- Vector-symbolic architectures (Kanerva).
- Existing cube-lattice work in physics and chemistry (lessons).
- The 27-state cube in combinatorial geometry.

**Chapter 3 — The Cube and Its Symmetry Group (15 pp)**

- Definition of the cube `{-1, 0, +1}^3`.
- Encoding `(x, y, z) -> idx = (x+1) + 3*(y+1) + 9*(z+1)`.
- The decomposition 1 + 6 + 12 + 8 = 27 and its geometric meaning.
- The octahedral group O (24 rotations) and full symmetry group
  O_h (48 elements including reflections).
- Orbit structure: axial orbit = 6, corner orbit = 8.
- 13 named permutations as 27-entry lookup tables.

**Chapter 4 — The BT-IS ISA (20 pp)**

- Register file: `C`, `F`, `R0..R7`, `D0..D3`, IP, stack, mem.
- Opcode map (rotation, reflection, cube arithmetic, comparison,
  branching, memory, control).
- Symbolic assembly syntax.
- Why 4 cube data registers, not more, not fewer.
- Discussion of the v0.1.0 → v0.2.0 ISA evolution.

**Chapter 5 — The Virtual Machine and Reversibility (15 pp)**

- The dispatch table.
- The undo log: per-step `Undo` enum, `apply_undo`, `undo_all`.
- Worked example: a 6-instruction program reversed in one call.
- Complexity analysis: undo is O(n) per program, O(1) per step.

**Chapter 6 — Turing Completeness (10 pp)**

- Reduction to Minsky's 2-counter machine.
- Encoding: chain of cubes as a counter, `CYCLE_X` for
  increment/decrement with carry/borrow.
- Constructive proof (polynomial blow-up).

**Chapter 7 — Empirical Evaluation (25 pp)**

- Implementation: Rust VM + assembler + CLI + Python cross-check.
- Stage B measurements: W1/W2/W4 vs SCALAR baseline.
- Stage C: reversibility + 3-way branching quantification.
- Stage D: Verilog model and area estimates.
- Stage E: domain study analysis.
- The honest verdict: niche, with specific recommendations.

**Chapter 8 — Conclusions and Future Work (10 pp)**

- Summary of contributions.
- Limitations (no real FPGA synthesis, register-file weakness).
- Roadmap to v0.3.0 (D4..D7, 3D GoL step, real synthesis).
- Open theoretical questions.

**Appendices (variable)**

- A: full ISA reference (reproduces `docs/ISA.md`).
- B: full benchmark scripts and output.
- C: source listings of all `.btis` programs.
- D: reproducibility instructions.

### Estimated length

~120 pages including appendices. ~70 pages of main text.

### Estimated effort

The chapter drafts already exist in the repo as documentation
chunks. The main work is *integration* and *literature review*:

1. **Literature review** (2-3 weeks): the prior-art positioning
   in `docs/positioning.md` is a starting point but a Masters
   thesis needs a deeper survey. Specifically:
   - REBEL / Bos 2024 thesis: read in full.
   - Setun 1958: find an English translation or summary.
   - Geometric algebra computing: read Dorst, Hestenes.
   - VSA / hyperdimensional: read Kanerva.
2. **Integration** (2 weeks): rewrite the existing docs as a
   coherent narrative, add transition text, fix notation.
3. **Stage D follow-up** (1 week, optional): run yosys + nextpnr
   on the Verilog core to get real synthesis numbers.
4. **Writing polish** (2 weeks): diagrams, captions, references.

Total: ~2 months of focused work.

### What the Masters paper is *not*

- It is **not** a paper claiming general-purpose superiority. The
  verdict is niche and the thesis should be honest about that.
- It is **not** a paper with real hardware numbers. The Stage D
  estimates are estimates. Real synthesis is a PhD-level
  extension.
- It is **not** a paper with a full 3D GoL step. The step is
  scaffolding only; full implementation is a Stage F follow-up.

A committee reviewing the Masters paper should come away
thinking "this is a real contribution to the design space of
novel machine architectures, with clear measurements and an
honest assessment of where it does and doesn't win." That's the
right outcome.

---

## 2. The PhD-level extension

A PhD thesis is *not* "the Masters thesis with more pages." It's
a research program that opens new questions and answers them.
For BT-IS the natural PhD-level questions are:

### Q1 — Is the niche big enough?

If D4..D7 fixes the W2 voxel-count loss, what's the next workload
that fails? The PhD thesis should sweep the workload space and
characterize where BT-IS wins, ties, and loses as a function of
the workload's structure.

### Q2 — Can the geometric primitive be made cheaper?

`cube_add` takes 1 BT-IS op. Can a *programmable* geometric
primitive be designed — e.g., a cube-arithmetic instruction
parameterized by an arbitrary permutation table? This is the
analogue of microcoded CISC vs RISC: BT-IS is currently
"hardwired cube-arithmetic"; a programmable primitive would be
"cube-arithmetic as data".

### Q3 — What does a real chip look like?

Take the Stage D estimates to real silicon. Options:

- **FPGA tape-out**: synthesize on a low-cost FPGA (Lattice
  iCE40 or Xilinx Artix-7), measure cycles per op, area, power.
  This is weeks of FPGA work.
- **ASIC tape-out**: tape out a small chip on an open PDK
  (e.g., Skywater 130nm). This is months of work and ~$10k-100k
  for a multi-project wafer run.
- **Compare to REBEL silicon**: if REBEL has been fabricated,
  compare die photos. If not, build a REBEL core in the same
  process and compare.

### Q4 — Is the geometric primitive *uniquely* useful?

Or could a cleverer scalar ISA get the same wins? The Stage B
SCALAR baseline is a first cut. A more sophisticated SCALAR
(e.g., one with a fused "cube-add" micro-op that takes two
cube-addressed operands) might match BT-IS's instruction count.
The PhD thesis should investigate this carefully.

### Q5 — Can BT-IS be useful for *new* problems?

The PhD thesis should find at least one application where BT-IS's
properties (reversibility, cube-arithmetic, geometric locality)
are *enabling* — not just faster than SCALAR, but enabling
algorithms that wouldn't be natural on a scalar ISA.

Candidate applications:

- **Reversible debugging**: run a program forward, inspect, undo,
  branch — natively reversible, no checkpoint cost.
- **3D GoL as a benchmark**: a "natural" workload that exercises
  the architecture's geometric primitives maximally.
- **Ternary neural network inference**: cube activations match
  `sign(x)`.
- **Voxel-grid PDE solvers**: spatial locality maps onto cube
  memory.

### PhD thesis structure (sketch)

**Chapter 1-7**: Masters thesis, polished.

**Chapter 8**: The v0.3.0 fix — D4..D7 and a full 3D GoL step.

**Chapter 9**: Real FPGA synthesis. Area, latency, power
measurements.

**Chapter 10**: Application — one of the candidates above,
implemented and measured.

**Chapter 11**: Theoretical extensions — the programmable
geometric primitive, alternative SCALAR baselines, the
niche characterization.

**Chapter 12**: Conclusions and open problems.

Estimated length: 200-250 pages.

### Estimated effort

3-5 years of full-time research:

- Year 1: v0.3.0 (D4..D7, 3D GoL), real FPGA synthesis.
- Year 2: application implementation and measurement.
- Year 3: theoretical extensions, paper submissions.
- Years 4-5: writing, defense, follow-up publications.

---

## 3. Practical advice

If you're considering this path:

1. **Start with the Masters**. Don't skip to PhD-level questions
   until the Masters work is complete and you've internalized what
   the prototype actually is.

2. **Use the existing prototype as leverage.** 34 unit tests, a
   Python cross-check, a SCALAR baseline, and a Verilog model
   already exist. A Masters student starting from scratch would
   take 6 months to reach the same point.

3. **Find a supervisor with one of these specialties**:
   - Computer architecture (for the hardware questions)
   - Programming languages / type theory (for the geometric
     primitive formalization)
   - Non-standard computation (for the cellular-automata angle)

4. **Pick the application early.** A PhD thesis needs *one*
   application where the architecture is genuinely useful. Don't
   try to characterize the full niche — find one workload that
   works, characterize it deeply, and let the niche emerge from
   that case study.

5. **Be honest about the verdict.** The v0.2.0-niche verdict is
   not a failure — it's a finding. A PhD thesis that *strengthens*
   the niche into "useful" (by adding D4..D7, by implementing the
   3D GoL step, by real synthesis) is more valuable than a thesis
   that handwaves past the limitations.

---

## 4. What this repo *is not*

This repo is **not** a thesis. It's:

- A working prototype (Rust VM, Python cross-check, 9 .btis
  programs).
- A research log (Stages A-F documented, measurements taken,
  verdict published).
- A reproduction artifact (anyone can `cargo test` and
  `python3 benchmarks/stage_b.py` to verify).

To make it a thesis, you need:

- A coherent narrative (not 8 documentation files; one thesis
  with 8 chapters).
- A literature review (the existing positioning is a starting
  point, not the final review).
- Real FPGA synthesis (Stage D's estimates are not enough).
- A defense (or viva, depending on jurisdiction).

The repo is *most* of the way there for a Masters; it's about a
third of the way for a PhD.
