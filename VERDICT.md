# Verdict (corrected)

> Final synthesis of Stages A through F into a decision about
> whether the 3D-Ternary Machine architecture is useful, niche,
> or not worth pursuing. Includes corrections received via
> external critique (see `docs/CRITIQUE_RESPONSE.md`).

## Summary of evidence

| Stage | result |
|-------|--------|
| **A: Correctness / universality** | Fibonacci F(0..9) mod 27 cross-checked against Python reference. Turing-completeness proved by reduction to Minsky's 2-counter machine (polynomial in program size). |
| **B: Instruction-count vs SCALAR** (corrected) | W4 cube-add loop: BT-IS **1.47×** faster (not 4.80× — the original was a baseline artifact). W1 rotations: 1.40×. W2 voxel-count: 0.85× (loss). |
| **C: Reversibility + 3-way branches** | Intrinsic reversibility of the rotation/reflection subset only. Full-ISA reversibility is journal-based (Bennett-style), works for any machine. 3-way branching present in both architectures. |
| **D: Native hardware** | Behavioral Verilog model synthesizable; estimated ~3000 LUTs + 9 BRAMs on a low-cost FPGA. SCALAR ~2000 LUTs. BT-IS ~1.5× area. Estimates only. |
| **E: Domain studies** | 3D GoL: strong expected BT-IS advantage, not implemented. Voxel: loss identified (register-file issue). Ternary NN, robotics: small/medium expected wins, not implemented. |

## Decision

The architecture is **niche, pending a group-exercising workload
demonstration**. The headline 4.80× result was a baseline artifact;
the fair comparison is ~1.5× on cube-add workloads and ~1× on
others.

### What works

- **Cube-arithmetic-heavy workloads** see a marginal instruction-
  count win (Stage B W4: 1.5×). This is the operand-location
  advantage: BT-IS cube *is* the operand.
- **Intrinsic reversibility of the rotation/reflection subset**
  is real and architectural.
- **The architecture is synthesizable** on a low-cost FPGA at
  modest area (Stage D estimates).

### What doesn't work (yet)

- **General-purpose advantage** is not established. Stage B W4
  is 1.5×; W1 and W2 are ties or losses.
- **The register-file shuffle** is the W2 bottleneck. A clean
  ISA fix (fused `LOAD_CR` / `STORE_CR`) has been identified but
  not yet implemented.
- **The symmetry-group workload has not been benchmarked.** The
  distinctive feature (rotor registers, group composition)
  remains untested on a workload where it actually matters.

### What the niche looks like

If the verdict is "useful for X, niche for Y", the natural
niche is **cube-arithmetic-dominated spatial computing**, with
the *untested* claim that group-equivariant computation (O_h-
equivariant convolutions, polycube canonicalization) is where the
architecture's distinctive features actually pay off.

## What we did *not* claim

- We did not claim the architecture is *useful for general-
  purpose computing*. Stage B W2 shows it's not.
- We did not claim the 4.80× headline was real. It was a
  baseline artifact; the fair number is 1.47×.
- We did not claim native hardware is production-ready. The
  Stage D estimates are estimates.
- We did not claim intrinsic reversibility of the full ISA. Only
  the rotation/reflection subset.

## What we did claim

- The architecture is *real*: Rust VM, assembler, CLI, 34 unit
  tests passing, Python cross-check, Verilog model.
- The architecture is *universal*: Turing-complete via Minsky
  reduction (polynomial in program size).
- The architecture is *geometrically motivated* in its
  permutation subset: instructions are permutations of cube
  states, and the cube's symmetry group is the source of
  instruction semantics.
- The rotation/reflection subset has *intrinsic reversibility*:
  every op is a group element with an inverse.
- The arithmetic subset (cube-add) gives a *modest* win over a
  fair SCALAR baseline: ~1.5× on tight arithmetic loops.

## Honest verdict

**Niche, pending v0.3.0.** The corrected Stage B result is honest
about the magnitude: BT-IS is *not* decisively better than
SCALAR on arithmetic, and it loses on register-shuffle workloads.
The architecture has real, distinctive features (rotor registers,
group composition, intrinsic reversibility of the permutation
subset), but these have not yet been benchmarked on workloads that
*use* them.

We recommend:

1. **Implement fused `LOAD_CR` / `STORE_CR`** — likely flips W2.
2. **Implement polycube/voxel canonicalization** as the next
   benchmark — tests the symmetry-group claim.
3. **Real FPGA synthesis** with yosys + nextpnr — convert Stage D
   estimates into measurements.
4. **Re-decide at v0.3.0** after the above.

We explicitly do *not* recommend archiving the project: the
architecture has real distinctive features; the implementation
is solid; the niche is plausible. The right next step is
*focusing* on the group-exercising workloads, not abandoning
the work.
