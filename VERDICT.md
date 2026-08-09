# Verdict (v0.3.1)

> Final synthesis of Stages A through W5 as of the v0.3.1
> tag. Where the previous verdict (v0.2.0-niche) made a
> single label, this revision reports the measurements
> honestly and declines to label a result that the data
> does not support.

## Where the evidence lands

The bench numbers were re-measured end-to-end at v0.3.1
because the v0.2.0-niche / v0.3.0-negative tags reported
ratios on BT-IS and SCALAR programs that did not produce
the same output. The new measurements use a driver
(`benchmarks/stage_b_word.py` and
`benchmarks/stage_b_w5.py`) that **asserts output equality
before reporting any ratio** and exits non-zero on
mismatch.

| Workload | BT-IS | SCALAR | ratio (SCALAR / BT-IS) | match |
|---|---:|---:|---:|---|
| W1 rotations (7 op sequence) | 9 | 14 | 1.56× | yes |
| W2 voxel_count (3 alive face neighbors) | 34 | 52 | 1.53× | yes |
| W4 cubeadd_loop (10× of `C := C + C`) | 32 | 22 | 0.69× | yes |
| W5 48 $O_h$ inner loop | 281 | 384 | 1.37× | yes |

Reading: BT-IS is faster on W1, W2, and W5. BT-IS is
slower on W4. The single-workload "decisive" thresholds
defined in the v0.2.0 ROADMAP (≥10% on ≥3 workloads, or a
single ≥2× win) are not met. Neither is the "all measured
workloads lose" condition for "not worth pursuing."

**Honest position:** BT-IS as specified is competitive
with a fair SCALAR baseline on three of four measured
workloads, and is slower on one. There is no measured
workload where BT-IS decisively beats a fair SCALAR, and
no measured workload where it decisively loses. The
v0.2.0-niche label ("niche") and the v0.3.0-negative
framing ("not worth pursuing") were both artifacts of
comparing different programs on each side; neither is
supported by the v0.3.1 measurements.

## What each workload actually measures

**W1 rotations.** 7-op geometric sequence on `(1, 0, 0)`.
BT-IS's `load_axis` + named rotations cost 1 op each;
SCALAR's setup of the input cube costs 6 ops (3 `LOAD_IMM`
+ 3 `CGET`). Per-apply: 1 op on both. The win is
SCALAR's setup overhead, not the apply primitive.

**W2 voxel_count.** 3 alive face neighbors of `(0, 0, 0)`,
summed via cube-add. BT-IS's `cube_add` primitive reads
`C := C + mem[C]`; SCALAR uses `WADD C0, C1` after a
`MEM_LOAD_C`. BT-IS's operand-location advantage (the
cube is both address and value) saves one `MEM_LOAD_C` per
iteration.

**W4 cubeadd_loop.** 10 iterations of `C := C + C` on both
sides. The previous v0.2.0 1.47× win was on mismatched
programs (BT-IS did `C := C + mem[C]` which became a
no-op after iter 0). With both sides computing the same
recurrence, BT-IS pays 32 ops vs SCALAR's 22 — a 0.69×
loss. The cube-add primitive is **not** a load-bearing
win when both architectures compute the same thing.

**W5 48 $O_h$ inner loop.** Apply each of the 48 elements
of the cube's full octahedral symmetry group to `(1, 0,
0)` and emit the result. The output orbit is the 6 axial
states, each appearing 8 times (48 / 6 = 8). BT-IS loads
each permutation into R0 in 0-3 named `rot_*_r` /
`reflect_*_r` / `neg_r` instructions, then `apply_r 0` (1
op). SCALAR has no cube-copy primitive, so it must rebuild
the input cube from scratch each iteration (3 `LOAD_IMM` +
3 `CGET` = 6 ops). Per-apply: 1 op on both. The win is
SCALAR's per-iteration setup overhead.

The W5 program in this tag is the **inner loop of
canonicalization**, not full voxel canonicalization. Full
canonicalization (apply 48 group elements to all 27 cells
of a 3×3×3 pattern) would be 27× the inner loop on both
sides; since both architectures pay 1 op per
`apply_r` / `APPLY_PERM`, the per-cell ratio is 1:1 and
the 27× outer factor doesn't change the win. The 48×
"canonicalization flagship" claim in the v0.2.0 ROADMAP
was for a not-yet-implemented `apply_r_to_mem` opcode that
operates on a 27-cell pattern, not a single cube.

## Reversibility

**Status (v0.3.1):** the rotation / reflection subset of
the ISA is intrinsically reversible (each op is a group
element with an inverse in $O_h$). The full ISA,
including arithmetic and memory, is *journal-reversible*
via `vm.undo_all()`: every state-mutating step records a
prior value, and the journal can be replayed in reverse.

This is a Bennett-style history tape, not an architectural
property of BT-IS. The same mechanism would work for any
register VM. The intrinsic reversibility of the
rotation / reflection subset is a real architectural
property, but the subset is small (12 named ops) and
does not extend to programs that use arithmetic or memory.

The `vm.undo_all()` documentation in the previous
verdicts ("every BT-IS program is automatically reversible")
was an overclaim. The corrected framing above is in
`docs/STAGE_C_RESULTS.md` and `docs/positioning.md`.

## Turing-completeness (claim withdrawn)

> The v0.2.0-niche verdict stated "Turing-completeness
> proved." This claim is **withdrawn** at v0.3.1.
>
> The proof in `docs/turing_completeness.md` represents
> 2-counter machine counters as chains of cubes in
> `HashMap<Cube, Cube>`-keyed memory. The VM has at most
> 27 distinct cube keys (one per state of `{-1, 0, +1}^3`),
> so the proof's encoding cannot grow beyond 27 cells
> per counter. A 2-counter machine with counters that
> exceed 27 cannot be simulated.
>
> Re-deriving the proof requires an unbounded address
> space (a new `A ∈ ℕ` register type) and a corrected
> DEC algorithm. This is out of scope for v0.3.1; the
> Turing-completeness claim is unverified until the proof
> is rewritten.

## Native hardware (status: sketch, not measured)

`hardware/btis_core.v` is a **behavioral** Verilog model,
not a synthesized core. At v0.3.1, 12 of 13 rotation /
reflection tables are uninitialized, `IADD` / `ISUB` /
`CMP` / branch / `JMP` / `OUTI` / `OUTV` are TODO
no-ops, `CUBE_ADD` reads from `F` rather than `mem[C]`,
and there is no program counter or instruction memory.

The "~3000 LUTs + 9 BRAMs" figure in
`docs/STAGE_D_RESULTS.md` is a **projection** based on
counting what a complete implementation would need, not
a measurement. The "1 op / cycle" and "100-150 MHz"
figures are also projections. Real synthesis (yosys +
nextpnr or Vivado) has not been run and is environmentally
blocked: yosys is not installed and `sudo` is not
available on this machine.

Until synthesis is run, the Stage D numbers should be
read as design estimates, not as architectural claims.

## What v0.3.1 does not show

- That BT-IS has an architectural advantage on
  *general-purpose* workloads. The four measured
  workloads are geometric; SCALAR with similar
  primitives matches or beats BT-IS on the cube-add
  primitive.
- That the rotor registers give a general compositional
  advantage. The W5 win is setup-cost only; on a per-`apply`
  basis, BT-IS and SCALAR pay the same 1 op.
- That 3D Game-of-Life, balanced-ternary neural
  networks, or other domain workloads favor BT-IS. None
  have been implemented at v0.3.1.
- That native hardware synthesis is feasible. The
  Verilog model is incomplete; the area / latency / power
  numbers are projections.

## What v0.3.1 does show

- BT-IS is a working balanced-ternary cube machine with
  34 unit tests passing, Python cross-check, and a
  reversible VM.
- On a fair comparison (output equality asserted before
  ratio reported), BT-IS is **competitive with SCALAR**
  on rotations, voxel counting, and the 48-symmetry
  inner loop, and **slower on pure cube-add**. The win
  on W5 is the rotor-register setup cost, not the apply
  primitive itself.
- The 1.47× W4 win reported at v0.2.0-niche and the
  0.67× W5 loss reported at v0.3.0-negative were both
  artifacts of comparing different programs on each
  side. Neither claim is supported by the v0.3.1
  measurements.

## Recommendation

**Archive the project as a reference implementation, not
continue development toward the original thesis.** The
thesis was "BT-IS is a useful machine architecture with
a geometric primitive." The measurements at v0.3.1
support neither the "useful" claim (no decisive win) nor
its negation (no decisive loss). The architecture is
real, tested, and documented; it just doesn't show the
decisive advantage the original thesis claimed.

Possible uses for what exists:

1. **Teaching artifact.** A clean implementation of a
   balanced-ternary cube machine, suitable for a course
   on novel architectures or balanced-ternary computing.
2. **Reference implementation.** Other researchers can
   build on the codebase, the benchmarks, and the
   measurement methodology without re-deriving the math.
3. **Negative-result publication.** A short paper titled
   "We tried to design a useful balanced-ternary cube
   machine; here is what we found and why it didn't
   decisively work" would be honest, educational, and
   rare. The v0.3.1 measurements are the basis for such
   a paper, not the v0.2.0 numbers.

What v0.3.1 does *not* support:

- A "BT-IS is useful" claim.
- A "BT-IS is not worth pursuing" claim.
- A workshop paper claiming the architecture has
  measurable advantages on a real workload, until a
  workload is found where the 1.5× W2 / W5 wins extend
  to ≥2× or appear on a domain-relevant application.
