# Deep-research prompt: 3D-Ternary Machine (BT-IS)

> A self-contained prompt that asks another AI to do a deep research
> dive into the BT-IS thesis across the web — finding prior art,
> finding related work, identifying missing citations, and locating
> any prior implementation or analysis the project has missed.
>
> Version: matches repo state at tag `v0.3.0-negative`.

---

You are asked to do a **deep web research dive** into the following
research project. Please be exhaustive: read the linked
repository, locate prior-art papers, identify any implementation
that already does what BT-IS claims, and report findings.

## 1. The project

**Repo:** https://github.com/vonstegen/3d-ternary-machine
**Tag:** `v0.3.0-negative`

The project proposes a **3D-Ternary Machine** (BT-IS): a machine
architecture whose primitive state is a balanced-ternary 3-vector in
`{-1, 0, +1}^3` (the **cube**, 27 states), and whose primitive
operations are permutations of cube states induced by the cube's
symmetry group.

The cube decomposes geometrically: 1 center, 6 axial, 12
face-diagonal, 8 corner states.

Key ISA features:

- 9 axis-aligned rotations, 3 reflections, 1 inversion (`ROT_*`,
  `REFLECT_*`, `NEG`) — each one cube-symmetry permutation.
- **First-class rotor registers** `R0..R7` holding cube-symmetry
  permutations as values, with `COMPOSE_R`, `INVERSE_R`,
  `APPLY_R`, `MOV_R`.
- 4 cube data registers `D0..D3` for general-purpose cube
  scratch space, with `MOV_CD`, `MOV_DC`, `STORE_D`, `LOAD_D`.
- `CUBE_ADD` — full 27-state addition with carry through (x, y, z).
- `CYCLE_X/Y/Z` — cyclic single-coordinate increment, no
  saturation.
- `CMP` + `BR_NEG/BR_ZERO/BR_POS` — native three-way comparison
  and branching.
- `STORE_C` / `LOAD_C` — memory addressed by cube coordinates.
- Reversibility: `vm.undo_all()` (Bennett-style journal).

## 2. The current verdict (load-bearing)

The project's own measurements (Stages B and W5, with corrected
word-width SCALAR baseline) show:

| workload | BT-IS | SCALAR (fair) | ratio |
|----------|------:|--------------:|------:|
| W1 rotations | 10 | 14 | 1.40× |
| W2 voxel_count | 72 | 61 | 0.85× |
| W4 cubeadd_loop | 15 | 22 | 1.47× |
| **W5 composition** | **21** | **14** | **0.67× (loss)** |

`ratio` = SCALAR / BT-IS. **W5 (the canonicalization flagship)
loses.** The architectural claim "rotor registers give
compositional leverage" is *not* demonstrated with a fair SCALAR.

The project's own verdict (in `VERDICT.md`): *"between niche and
not-worth-pursuing."* The codebase is a clean reference
implementation; it does not prove the original thesis.

## 3. The research questions

For each of the following, please do a deep web search and
report findings. Cite URLs and (where possible) PDFs. Be
specific: paper titles, authors, years, venues.

### Q1 — Prior art: balanced-ternary ISAs

The project compared itself against:
- **REBEL / Bos 2024** (University of South-Eastern Norway PhD
  thesis: *Beyond 0 and 1*).
- **Setun (1958)**, **Setnex** (modern clean-slate 27-trit ISA).
- **KAIST ART-9** (24-trit balanced-ternary RISC).

What other balanced-ternary ISAs, CPUs, or experimental machines
exist that the project did *not* consider? Are there any
balanced-ternary *vector* or *geometric* ISAs from the 1970s-80s
Soviet/Russian computing literature?

### Q2 — Prior art: cube-lattice / group-element computation

The project's rotor registers are first-class group elements with
COMPOSE/INVERSE/APPLY. This is the lineage of:

- **Toffoli / Fredkin / conservative logic** (reversible
  computing).
- **Pendulum** (Frank, 2017).
- **Group-equivariant neural networks** (Cohen/Welling, E(3)-NNs).

What *other* machines have first-class group elements as
operands? Are there reversible / permutation-based machines
that the project has missed?

### Q3 — Prior art: GF(3) / ternary linear algebra machines

The 27-cube states can be encoded as GF(3)^3 vectors. Cube-add
is GF(3)^3 addition. Are there *GF(3) linear-algebra machines*
in the literature (pre-1980 or modern)? Any ternary CAM
(content-addressable memory) designs?

### Q4 — Prior art: balanced-ternary neural-network hardware

The architecture has a 3-way activation native (`CMP` +
`BR_*`). Modern ternary neural-network hardware (e.g., BitNet,
TernaryLLM) often uses {0, 1, -1} weights. Any prior work on
*balanced-ternary ML hardware* that the project missed?

### Q5 — "Symmetry-dominated" workloads

Claude (in the project's review log) proposed three workloads:

- **Polycube / voxel-pattern canonicalization under O_h.**
- **O_h-equivariant convolution** (group-averaged kernels).
- **Ternary Golay [11,6,5] decoding** (GF(3) codes with rich
  symmetry).

The project implemented the first *kind* (permutation
composition) and it *lost* to fair SCALAR. Are there other
canonicalization workloads where the group structure is the
inner loop? Specifically: has anyone published a benchmark where
*first-class group elements* (vs per-op scalar ops) gives a
measured speedup?

### Q6 — Existing implementations of cube-symmetric ISAs

Search GitHub, GitLab, and academic code repos for any
implementation of:
- A 27-state cube machine
- A balanced-ternary vector ISA (3-trit words, not 27-trit
  scalars)
- A rotor-register / permutation-register architecture
- A machine with cube-addressed memory

### Q7 — Negative-result publications

The project ended with a negative result (W5 loss). Are there
published papers titled something like:
- "Why balanced-ternary ISAs don't outperform binary ISAs"
- "An empirical evaluation of the BT-IS / REBEL architecture"
- "Lessons from the Setun project"

### Q8 — Verilog synthesis of cube machines

The project has a behavioral Verilog model in
`hardware/btis_core.v`. Has anyone actually synthesized a
balanced-ternary CPU on an FPGA? Cite specific synth reports
(area, frequency, power).

### Q9 — The Minsky-reduction argument

The Turing-completeness proof in `docs/turing_completeness.md`
reduces BT-IS to Minsky's 2-counter machine. Is this reduction
correct? Has anyone else proved similar reductions for
cube-based or balanced-ternary machines?

### Q10 — Specific missing citations

Look at `docs/positioning.md` §3 (prior art). List any paper,
book, or project that *should* be cited there but isn't. Be
specific.

## 4. What to skip

Please *do not* spend time on:
- Generic "ternary computing" pages (e.g., Wikipedia). Cite
  primary sources.
- Speculative claims about BT-IS's value. The project's own
  measurements have shown it does *not* decisively beat SCALAR.
  Cite sources, not opinions.
- The project's own documentation. Read it, but don't cite it
  as if it were prior art.

## 5. What to deliver

A single response with:
1. **Findings** — paper / project / URL with one-sentence
   description per finding.
2. **For each of Q1–Q10**: a "covered" or "not found in this
   search" verdict.
3. **A bibliography** of all sources you cite.
4. **Specific recommendations** for the project's
   `docs/positioning.md`: which references to add, which
   comparisons to drop, which framing to adjust.

Be specific. Cite URLs and titles. The project authors will
verify your work before acting on it.

---

(End of deep-research prompt. Repo: github.com/vonstegen/3d-ternary-machine
@ v0.3.0-negative. Tag the response with the date and the
verdict per question.)
