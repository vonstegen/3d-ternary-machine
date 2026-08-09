# Verdict (final)

> Final synthesis of Stages A through W5. The honest verdict is
> **between niche and not-worth-pursuing**: BT-IS as specified
> does not decisively beat a fair SCALAR baseline on any measured
> workload, but it doesn't decisively lose either.

## Summary of evidence

| Stage | result |
|-------|--------|
| **A: Correctness / universality** | Fibonacci F(0..9) cross-checked. Turing-completeness proved. |
| **B: vs SCALAR baseline (corrected)** | W4: 1.47×. W1: 1.40×. W2: 0.85× (loss). |
| **C: Reversibility** | Intrinsic for rotation/reflection subset. Journal-based for full ISA. |
| **D: Native hardware** | Behavioral Verilog, ~3000 LUTs + 9 BRAMs (estimates). |
| **E: Domain studies (revised)** | Projected ratios removed. Voxel loss measured. Others unimplemented. |
| **W5: Composition flagship** | BT-IS = 21 ops. SCALAR (fair) = 14. **BT-IS slower.** |

## Decision

**Between niche and not-worth-pursuing.**

The architecture does *not* show an architectural advantage on
the two strongest natural workloads (W4 cube-add, W5 composition).
With a fair SCALAR baseline, the ratios are:

- W4 cube-add: BT-IS 1.47× faster (modest)
- W5 composition: BT-IS 0.67× (slower — i.e., BT-IS is *slower*)
- W2 voxel-count: BT-IS 0.85× (loss)
- W1 rotations: BT-IS 1.40× (small win)

There is no measured workload where BT-IS decisively beats a
fair SCALAR. The W4 win is modest (50% better), the W5 loss
is the more telling result because it tests the *rotor registers*
directly.

### What the W5 result actually says

W5 (permutation composition) is the workload that exercises
BT-IS's distinctive feature — first-class group elements with
`COMPOSE_R`. The result: with both architectures given
equivalent primitives (`WCOMPOSE`, `WINVERT`, `WLOAD_PERM`,
`WAPPLY`), BT-IS is *slower* (21 vs 14 ops) because of setup
overhead (5 `load_r` + 4 `ROT_*_R` ops vs 1 `wload_perm` literal).

**The rotor-register advantage disappears when SCALAR is given
the same primitives.** The architectural claim "first-class
group elements give compositional leverage" is not demonstrated.

## What this means

The hypothesis the project started with ("BT-IS is a useful
machine architecture with a geometric primitive") has been
tested. The result: **partially supported on cube-add, not
supported on composition.** Overall: not decisive enough to
publish as a positive result.

## What we did *not* claim

- That BT-IS is *useful for general-purpose computing*. The
  measurements show it's approximately equivalent to a fair SCALAR.
- That the 4.80× (original) or 1.47× (corrected) headline is a
  decisive win. It's modest at best.
- That the rotor registers / group composition give an
  architectural advantage. W5 shows they don't, with fair
  SCALAR.

## What we did claim

- The architecture is *real*: Rust VM, assembler, CLI, 34 unit
  tests passing, Python cross-check.
- The architecture is *universal*: Turing-complete.
- The cube arithmetic gives a *modest* win over a fair SCALAR.
- The rotation/reflection subset has *intrinsic reversibility*.

## Honest verdict

**Not a publishable positive result.** The measurements do not
support the original hypothesis strongly enough to justify a
research paper claiming BT-IS is useful.

The codebase is **a clean reference implementation** of a
balanced-ternary cube machine. It is well-tested, well-documented,
and honest about its limitations. This is a contribution, but
it is not the contribution the original thesis claimed.

## Recommendation

**Stop here.** Don't continue development with the goal of
proving the original thesis. The evidence against it is now
substantial.

Possible uses for what exists:

1. **Teaching artifact.** A clean implementation of a
   balanced-ternary cube machine, suitable for a course on
   novel architectures or balanced-ternary computing.
2. **Reference implementation.** Other researchers can build
   on the codebase, the benchmarks, and the measurement
   methodology without re-deriving the math.
3. **Negative-result publication.** A short paper titled "We
   tried to design a useful balanced-ternary cube machine; here
   is what we found and why it didn't work" would be honest,
   educational, and rare.

The right next step depends on what the user wants:
- If they want a thesis, this is **not** the thesis. They
  should pick a different topic.
- If they want a clean codebase, this **is** the codebase.
- If they want a negative-result publication, this **is** the
  paper — write it up and submit to a workshop.
