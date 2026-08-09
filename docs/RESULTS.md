# RESULTS (final)

> Consolidated results from Stages A through W5. Includes corrections
> received via external critique. The headline: **BT-IS has no
> measured workload where it decisively beats a fair SCALAR
> baseline.**

## Headline

After Stages B, W5, and the corrected Stage E:

| workload | BT-IS | SCALAR (fair) | ratio |
|----------|------:|--------------:|------:|
| W1 rotations | 10 | 14 | 1.40× |
| W2 voxel_count | 72 | 61 | 0.85× (loss) |
| W4 cubeadd_loop | 15 | 22 | 1.47× |
| W5 composition | 21 | 14 | 0.67× (loss) |

(`ratio` = SCALAR / BT-IS. Higher = BT-IS more efficient.)

- **W4 (cube-add)**: 1.47× win. The cube-add primitive is
  genuinely faster than SCALAR's word-width ALU, by ~50%.
- **W5 (composition)**: BT-IS is *slower*. SCALAR with equivalent
  primitives (`WCOMPOSE`, `WINVERT`, `WLOAD_PERM`, `WAPPLY`)
  matches BT-IS op-for-op, and SCALAR has less setup overhead.
- **W2 (voxel-count)**: BT-IS loses by 15%.

The "geometric primitive is an architectural advantage" claim
is **not supported** by these measurements. The cube-add win is
modest (1.47×), and other workloads either tie or lose.

## Architecture properties confirmed

- **Cube primitive**: 27 states, decomposition 1 + 6 + 12 + 8.
- **Turing completeness**: proved by reduction to Minsky's
  2-counter machine.
- **Intrinsic reversibility** of the rotation/reflection subset.
- **Three-way branching**: present in both architectures.
- **Synthesizability**: estimated ~3000 LUTs + 9 BRAMs.

## What's NOT confirmed

- That BT-IS has an architectural advantage on *any* workload.
- That the cube-add primitive is a load-bearing win (it's 1.47×,
  not 4-100× as previously projected).
- That the rotor registers / composition give compositional
  leverage (W5 shows they don't, when SCALAR is given equivalent
  primitives).
- That a 3D GoL step would be a win (not implemented; analysis
  suggests ~1.5× at best).

## Implementation status

- Rust crate: 34 unit tests passing.
- 7 `.btis` example programs including Fibonacci (cross-checked)
  and Stage B + W5 benchmarks.
- Python prototype + cross-verification harness: working.
- W5 cross-checked: BT-IS output (0, -1, 0) matches Python
  reference for input (1, 0, 0).

## Decision criteria revisited

- **Useful** (continue general): would require BT-IS to win by
  ≥10% on ≥3 workloads. Currently 0 of 4 measured workloads
  meet that bar (W4 is 1.47× = 47% > 10%, but only one).
  **Useful: not established.**
- **Niche**: would require a single workload with real win. **W4
  is the only candidate, at 1.47×.** That's marginal, not niche.
- **Not worth pursuing** (archive): would require all measured
  workloads to lose. W1 and W4 are wins, just not big ones.

The honest position is **between niche and not-worth-pursuing**:
BT-IS as specified does not decisively beat a fair SCALAR
baseline on any measured workload. It does *not* lose either —
it's approximately equivalent on most workloads.

## Recommendations

1. **Do not invest in more ISA extensions.** The extensions
   added for W5 (`ROT_*_R`) did not produce a win; SCALAR
   matches with its own primitives.
2. **Do not invest in 3D GoL step implementation.** Expected
   ratio (~1.5×) is below the "decisive win" threshold.
3. **Consider archiving the project.** The architecture does not
   demonstrate an architectural advantage on measured workloads.
   The math and implementation are sound, but the *thesis* the
   math supports is "BT-IS is approximately equivalent to SCALAR
   on this class of problems" — not a publishable claim.
4. **Or, alternative: reframe the contribution.** BT-IS as a
   *teaching artifact* — a clean, well-tested implementation of a
   balanced-ternary cube machine — may have pedagogical value
   even without an architectural advantage. This is a real
   contribution; it just isn't a research paper.

## What's next

The roadmap's verdict (Stage F) is now: **the architecture does
not demonstrate a decisive advantage on measured workloads.** The
honest next step is either:

(a) Archive the project. The implementation stays as a clean
    reference for cube-lattice balanced-ternary machines.

(b) Reframe as a teaching artifact. The code, tests, and
    documentation are well-suited for a course on novel machine
    architectures or balanced-ternary computing.

(c) Search for a workload where the architecture does win. This
    requires thinking *outside* cube-add and composition — the two
    natural primitives have been measured and they don't
    decisively favor BT-IS.

Path (c) is the open question. The previous critique suggested
"polynomial canonicalization under O_h" as a candidate; that has
been tested in W5 and fails.

## Honest reading

This is the right answer. The architecture was a reasonable
hypothesis; the hypothesis has been tested; the test result is
"approximately equivalent to a fair baseline." That's a valid
research outcome.

The codebase is real, working, well-tested, and well-documented.
It does not demonstrate an architectural advantage, but it is
a clean implementation of a balanced-ternary cube machine. That
is a contribution, just not the one originally proposed.
