# Roadmap

> A staged plan to determine whether the 3D-Ternary Machine (BT-IS)
> is *useful* as a machine architecture — i.e., whether its geometric
> computational ontology provides a real, measurable advantage over
> conventional Boolean and scalar-balanced-ternary designs on at
> least one class of workloads.

The goal is a **decision**, not a celebration. Each stage has
*falsifiable* exit criteria. We treat "the hypothesis survives" and
"the hypothesis does not survive" as equally good outcomes; the
project is not advocacy.

---

## 0. Central hypothesis

Let `BT-IS` denote the 27-state balanced-ternary cube machine
(this repo), and let `SCALAR` denote a conventional balanced-ternary
RISC emulator that uses 27-trit words (REBEL-style) to express the
same algorithms.

> **H.** There exists a non-trivial class of algorithms `A` for which
> a `BT-IS` implementation uses *strictly fewer* state-mutating
> instructions than a `SCALAR` implementation, *and* the reduction
> is attributable to geometric structure of the cube (not just to a
> difference in representation).

Why this form:

- "Fewer instructions" is what would make the architecture *useful*.
  Equal-instruction-count work would make it merely *novel*.
- "State-mutating instructions" excludes pure output/move ops; we want
  the work itself to be smaller.
- "Geometric structure of the cube" rules out "the BT-IS version just
  uses a different encoding" wins. The reduction must come from the
  fact that data, instructions, addresses, and flags all live in the
  same geometric space.

We will measure `H` empirically in **Stage B**. Stages A, C, D, E
either sharpen the question or measure adjacent properties.

### Falsifiable predictions

P1. Three-way comparison (`CMP` + 3-way branch) replaces cascades of
    2-way branches in real code at non-trivial frequency.
P2. Cube-addressed memory (`STORE_C` / `LOAD_C`) collapses what would
    be multiple load/store + arithmetic ops in `SCALAR` into one
    geometric op, on geometric-locality workloads.
P3. Reversibility of execution is achievable at no asymptotic cost
    relative to forward execution (per-step undo is constant time).
P4. On 3D-rotation / voxel / balanced-ternary-arithmetic workloads,
    `BT-IS` instruction count is ≤ `SCALAR` instruction count, with
    ≥10% reduction in at least half the workloads.
P5. On native hardware (FPGA / ASIC), `BT-IS` can be implemented at
    area parity or below vs `SCALAR` for the same per-op cost.

### Success criteria for the project

- **Success (continue):** ≥3 of P1–P5 confirmed, P4 ≥ 10% reduction
  on at least 3 workloads, P5 within 2× area of `SCALAR`.
- **Niche (narrow publication):** P1, P3, P4 hold on a narrow class
  of workloads but P5 fails — software emulation is the practical
  realization.
- **Not worth pursuing (archive):** P4 fails on every workload we
  try, or P3 fails (no clean reversibility), or the architectural
  advantage turns out to be encoding-only.

---

## Stage A — Correctness and universality

**Goal:** show that BT-IS can express real algorithms, not just toy
rotation programs.

**Exit criteria:**

- [ ] Implement `fibonacci(n)` for several `n`, output the sequence.
- [ ] Implement `gcd(a, b)` for representative pairs.
- [ ] Implement a `3×3×3` Game-of-Life step (Bays' criteria).
- [ ] Implement a 3-axis sort of 27 cube-keyed records.
- [ ] Each program cross-checked against a Python reference.
- [ ] A paper-style proof (or rigorous argument) that the ISA is
      Turing-complete. The argument should reduce from a known
      Turing-complete model — most cleanly, a 2-counter machine or
      a Turing machine with bounded tape — and show that the BT-IS
      primitives suffice.

**What this stage can prove:** that the architecture can host real
programs and is computationally universal.

**What this stage cannot prove:** that the architecture has any
*advantage*. Universality is necessary, not sufficient.

**Estimated effort:** 2–4 weeks of focused work.

---

## Stage B — Expressiveness comparison (the key measurement)

**Goal:** measure the instruction count of BT-IS vs SCALAR on
realistic workloads. This is the empirical test of hypothesis `H`.

**Method:**

1. **Pick a workload set.** Candidates:
   - 3D vector rotation (single rotation, sequence of N rotations)
   - Voxel neighborhood iteration (read 6 or 26 neighbors, sum,
     decide)
   - Balanced-ternary arithmetic (multiply, divide, square root in
     `[-1, +1]` domain)
   - Three-way merge of sorted ternary sequences
   - 3D Game-of-Life step on a 27-cell neighborhood
   - Ternary neural-net layer (a 3×3 ternary-weight matrix applied
     to a 27-vector of inputs)

2. **Implement each workload twice.** Once in BT-IS, once in a
   SCALAR balanced-ternary RISC emulator (REBEL-style). Both must
   produce the same output for the same input.

3. **Measure and report:**
   - Total state-mutating instruction count
   - Code size (in instruction words)
   - State-space usage (peak number of live registers / memory cells)
   - Number of distinct cube states visited during execution
     (proxy for "geometric locality")

4. **Report per-workload.** Aggregate with mean, median, and
   per-workload table. The hypothesis `H` is confirmed if
   ≥50% of workloads show ≥10% reduction in instruction count.

**Exit criteria:**

- [ ] All six workloads implemented in both BT-IS and SCALAR.
- [ ] Cross-checked outputs match reference.
- [ ] Per-workload measurements published.
- [ ] Hypothesis confirmed / refuted for each workload.

**What this stage can prove:** whether the architecture has any
advantage, and on which workloads.

**What this stage cannot prove:** that the advantage will translate
to real-world speed (the SCALAR emulator may itself be inefficient;
the BT-IS advantage may vanish on real hardware).

**Estimated effort:** 1–2 months of focused work.

---

## Stage C — Reversibility and three-way branching

**Goal:** quantify the qualitative advantages BT-IS claims.

**Exit criteria:**

- [ ] A non-trivial reversible program (e.g., GoL step whose forward
      and inverse are both expressible as BT-IS trajectories and
      both run in the same time bound).
- [ ] Per-instruction undo cost measured and shown to be constant.
- [ ] A static count, per workload from Stage B, of:
      - BT-IS three-way branches used
      - Equivalent SCALAR cascade length (if-then-else sequences that
        the BT-IS branch replaces)
- [ ] Ratio reported.

**What this stage can prove:** the reversibility and 3-way-branching
claims are *real, not cosmetic*.

**What this stage cannot prove:** that reversibility matters in
practice (most software is not reversible).

**Estimated effort:** 2–4 weeks.

---

## Stage D — Native hardware feasibility

**Goal:** answer "could this be built?" and "would it be cheap?".

**Method:**

1. **FPGA prototype.** Synthesize a minimal BT-IS core (program
   counter, instruction memory, cube register file, 27-entry op
   LUTs, 3-way comparator, branch unit) on a low-cost FPGA
   (Lattice iCE40 or similar).
2. **Area.** Report LUT count, BRAM usage, DSP usage.
3. **Cycles per op.** Report critical-path latency and cycles per
   instruction.
4. **Power.** Use vendor tools (yosys + nextpnr for iCE40; Vivado
   for Xilinx) to estimate dynamic and static power.
5. **Compare.** Cite published REBEL or Setnex FPGA numbers if
   available; otherwise implement a minimal scalar balanced-ternary
   core on the same FPGA and compare directly.

**Exit criteria:**

- [ ] BT-IS core synthesizes and meets timing at ≥50 MHz.
- [ ] Area and power reported with methodology.
- [ ] Either:
    - P5 confirmed (BT-IS area ≤ 2× SCALAR), or
    - the gap is explained (e.g., LUT size dominates because
      BT-IS's 27-entry tables are too small to amortize BRAM).

**What this stage can prove:** whether native hardware is a real
option. This is the make-or-break question for the architecture's
*future*, separate from whether it has theoretical merit.

**What this stage cannot prove:** that production silicon is
worthwhile. FPGA results extrapolate imperfectly.

**Estimated effort:** 2–3 months (Verilog / nMigen / SpinalHDL).

---

## Stage E — Domain studies

**Goal:** identify the natural workloads for BT-IS and test the
hypothesis on them.

**Candidates (from the architecture's positioning):**

1. **3D Game-of-Life / cellular automata on the cube.** The
   architecture was literally designed around this: 27 cells, 27
   instructions per step, geometric locality.
2. **Voxel processing.** 3D image operations, signed-distance
   fields, level-set methods.
3. **Ternary neural-net primitives.** A 3×3 ternary-weight matrix
   multiply + a 3-way activation (essentially `sign(x)`). The
   `CMP` instruction *is* the activation function.
4. **Robotics transforms.** Compose rotations to compose
   end-effector orientations. The cube's rotation group is
   exactly the right tool.

**Exit criteria:**

- [ ] At least three workloads from the candidate list implemented
      and benchmarked.
- [ ] Honest write-up: which workloads saw a real benefit, which
      saw encoding parity, which saw an encoding cost.

**What this stage can prove:** the *niche* question (vs the
general-purpose question).

**Estimated effort:** 1–2 months.

---

## Stage F — Decision

**Goal:** synthesize measurements into a verdict and publish.

**Exit criteria:**

- [ ] `docs/RESULTS.md` written, summarizing Stages A–E with the
      actual numbers.
- [ ] `docs/positioning.md` updated to reflect what was learned.
- [ ] A `VERDICT.md` at the repo root, with one of:
      - "Useful: continue development, target Stage G (production)."
      - "Niche: publish, target specific workloads, halt general
        development."
      - "Not worth pursuing: archive the repo, preserve the
        theoretical contribution."
- [ ] A release tagged accordingly (`v0.2.0-useful`, `v0.2.0-niche`,
      or `v0.2.0-archived`).

---

## What this roadmap is *not*

It is **not** a commitment to a release schedule. Stages B and D
might fail and produce "niche" or "archive" outcomes; that's a
success for the project (we *learned something*), not a failure.

It is **not** advocacy. The hypothesis `H` is falsifiable, and the
verdict could be "no, this isn't useful". The roadmap respects that.

It is **not** a complete research program. A complete program
would also include: comparison to other recent ternary / vector /
geometric ISAs (Bos 2024, KAIST ART-9, etc.), a published paper, and
external review. Those are Stage G (publication) and are out of
scope for this repo until Stage F's verdict is in.

---

## Status

- **Stage A:** not started. Three programs (`countdown`, `voxel_pattern`,
  `rotor_reversible`) shipped at v0.1.0 as scaffolding, but `fib`,
  `gcd`, `3D GoL step`, and `3-axis sort` are pending.
- **Stage B:** not started.
- **Stage C:** not started.
- **Stage D:** not started.
- **Stage E:** not started.
- **Stage F:** not started.

See `docs/RESULTS.md` (will be created at Stage F) for the verdict.
