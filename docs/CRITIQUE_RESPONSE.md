# Response to Claude's critique

> A point-by-point response to the sharp critique delivered on the
> project. Where the critique lands, we fix it; where it doesn't,
> we say so explicitly. This is part of the project's working record
> and is preserved in the repo as a transparency artifact.

---

## 1. Two incompatible semantics / W4 is not a geometric win

**Status: partially right, partially wrong.**

The critique that `cube_add` treats coordinates as *positional
digits with place value*, not as interchangeable spatial axes,
is correct. The W4 win (4.8× vs SCALAR) is a 3-wide-arithmetic
advantage, not a geometric one. Rotations and `cube_add` are
indeed algebraically unrelated in BT-IS.

What survives:

- BT-IS's instruction set *has* both geometric ops (rotations)
  and arithmetic ops (cube_add). These are separate primitives.
  Calling the architecture "geometric" because it has rotations
  was overreach.
- The honest framing is: **BT-IS has a 27-state cube as its
  primitive, with both a rotation/permutation algebra and an
  arithmetic algebra on that cube's coordinates.** The two
  algebras don't unify; they're separate ISA features.

The "BT-IS ≈ 3-lane ternary SIMD with a signed permutation
network" reframe is fair. We accept it. The thesis should say so.

What we *do* still have that the critique concedes:

- **3-way branches** — yes, SCALAR has them too. Not a discriminator.
- **Orbit-based instruction encoding** — the cube's symmetry
  group is the source of 13 named ops; a SIMD machine doesn't
  get that for free. This is the architectural property that
  needs to be defended, and §3's "polynomial canonicalization"
  is the right benchmark.

**The decomposition 1+6+12+8 — "is 27 load-bearing?"** The
critique is correct: this expansion is `Σ C(n,k) * 2^k` over
nonzero coordinates, identical at every dimension. The
*number* 27 is not special; it's the smallest nontrivial case
where the symmetry group is interesting (the octahedral group
has 24 elements at n=3, 120 at n=4, etc.). The thesis should
say so. We do not claim 27 is sacred.

---

## 2. SCALAR baseline strawmanned

**Status: this is the strongest criticism. Likely correct.**

The critique is right: REBEL uses 27-trit *words*, and a fair
SCALAR baseline should add a 3-trit quantity in one instruction,
not six per-coordinate ops. Our SCALAR implementation is
trit-granular (the `TADD` op carries within a single trit), which
hobbles it.

**Action: re-run Stage B with a word-width SCALAR.**

This is a substantial re-implementation but it is the right
thing to do. We need:

- A SCALAR variant where `TADD` operates on 3-trit fields at a
  time, with internal carry chain hidden from the program.
- Re-run W1/W2/W4 against this baseline.
- The W4 result may collapse from 4.8× toward 1×. If so, the
  honest verdict shifts from "niche" to "the geometry must carry
  everything" or even "not worth pursuing".

This is the most important fix from the critique. Without it,
the headline measurement is suspect.

(Track this in a follow-up: re-do Stage B with a fair word-width
SCALAR before claiming any quantitative instruction-count win.)

---

## 3. Factual errors

### 3a. "Reversibility is automatic / by construction" — wrong

**Status: accepted, retracted.**

The critique is correct: `vm.undo_all()` is a journal. Bennett's
history-tape trick. It works for *any* machine — bolting it
onto SCALAR would give SCALAR the same property. That is not
"intrinsic reversibility."

The restricted claim that *is* defensible:

- The **rotation/reflection subset** of BT-IS is intrinsically
  reversible. Every `ROT_*` / `REFLECT_*` / `NEG` op is a
  permutation of cube states with an inverse in the group. You
  can run the inverse `R.inverse()` and reach the prior state
  with no journal.

The full claim that fails:

- `STORE_C` is destructive. The cube's arithmetic ops
  (`CUBE_ADD`, `IADD`) are not bijective on cubes with multiple
  representations. So BT-IS as a whole is *not* intrinsically
  reversible. The journal is doing real work.

**Action:** rewrite the reversibility section of
`docs/positioning.md` and `docs/STAGE_C_RESULTS.md` to claim
*intrinsic reversibility of the rotation/reflection subset*,
not of the full ISA. The journal-based `vm.undo_all()` is still
useful, but it should be presented as Bennett-style history
reversal, not as architectural intrinsic reversibility.

### 3b. "Polynomial-time Turing equivalence"

**Status: withdrawn at v0.3.1.** The "polynomial blow-up"
wording was the action item from the original critique, but
the more fundamental issue is that the underlying TC proof
is unsound (see `docs/turing_completeness.md` at v0.3.1).
The proof assumes unbounded cube-keyed memory, which the
VM does not have. Polynomial-blow-up wording is moot when
the reduction itself does not hold.

The earlier "polynomial in program size" action item is
retained here for the historical record but is no longer
the relevant fix.

### 3c. VSA "special case at dimension 3" — misclassified

**Status: accepted, retracted.**

The critique is correct: VSA's properties (concentration of
measure, robust superposition, etc.) emerge at *high* dimension.
d=3 shares only the alphabet. The "VSA special case at
dimension 3" framing is wrong and invites the wrong critique.

**Action:** remove or substantially rewrite the VSA comparison
in `docs/positioning.md` §5. Either drop the comparison entirely
or reframe it as: "BT-IS is a low-dimensional ternary alphabet
machine; it does not share VSA's high-dimensional statistical
properties."

### 3d. Orbit sizes and |O_h|=48 — correct

**Status: no action.**

We verified: orbit of axial = 6, orbit of corner = 8,
|O_h| = 48. The math checks.

---

## 4. Closest prior art

**Status: accepted.**

The critique's prior-art list is better than ours:

- **Toffoli / reversible / permutation-based architectures**:
  BT-IS's rotation/reflection subset is in this lineage.
- **Pendulum / Frank's reversible computing**: Pendulum uses
  group-element manipulation as first-class values. Our rotor
  registers (`R0..R7`) are Pendulum-style.
- **Group-equivariant neural networks** (Cohen/Welling): the
  cube's symmetry group is the natural domain here.

The critique also notes:

- **Ternary content-addressable memory**: STORE/LOAD addressed
  by cube coordinates is a tiny associative structure. Worth
  flagging in the prior-art section.
- **GF(3) linear-algebra machines**: 3-trit values are GF(3)
  elements. Cube arithmetic is GF(3)^3 linear-ish algebra. Worth
  flagging.

REBEL is still a comparison point (it's the most recent
balanced-ternary ISA), but it should not be presented as the
closest prior art. The closest is the reversible / group-element
family.

**Action:** rewrite §5 of `docs/positioning.md` to lead with
Pendulum and group-equivariant computation, with REBEL as a
modern ternary comparison rather than a primary reference.

---

## 5. Workloads that actually test the claim

**Status: accepted; this is the most useful part of the critique.**

The critique proposes three workloads that *actually* test
whether the symmetry group is doing work, not just whether
3-wide arithmetic is faster:

1. **Polycube/voxel canonicalization** — hashing 3×3×3 patterns
   to a canonical form under O_h. The 48 group ops applied via
   rotor compose/apply is the inner loop. SCALAR pays full
   price per symmetry. **This is the right flagship benchmark.**

2. **O_h-equivariant convolution** — group-averaged 3D kernels
   in E(3)-equivariant NNs. Connects to the live ternary-NN
   thread (BitNet, etc.). Worth pursuing if Q1 above pans out.

3. **Ternary Golay [11,6,5] decoding** — GF(3) codes with rich
   symmetry. Niche but rigorous. Worth a paragraph if not a
   full benchmark.

**Action:** make polycube/voxel canonicalization the *new*
flagship workload (replacing or supplementing 3D GoL). It
directly tests the symmetry group's value.

---

## 6. ISA fix for W2 — fused permute-on-load/store

**Status: better suggestion than adding D4..D7.**

The critique's suggestion is: add a rotor operand to `LOAD_C`
and `STORE_C`. `LOAD_C Rk, addr` reads `mem[addr]` and applies
`Rk` to it on the way to `C`. One instruction replaces the
`load_d → mov_dc → apply_r` shuffle that the W2 voxel-count
program does repeatedly.

This is cleaner than widening the register file. It also
preserves the "honest register file" property that made the
W2 loss a useful diagnostic.

**Action:** add `LOAD_CR` and `STORE_CR` opcodes. Re-run W2.

If W2 still loses after this, *then* widen the register file.

---

## Summary of action items

In priority order:

1. **Re-run Stage B with a fair word-width SCALAR.** If W4
   collapses toward 1×, the verdict shifts. (Highest priority;
   everything depends on this.)
2. **Rewrite reversibility claims** to be about the rotation/
   reflection subset, not the full ISA. Update positioning.md
   and STAGE_C_RESULTS.md.
3. **Rewrite prior art §5** to lead with Pendulum / reversible
   / group-equivariant computation. Add GF(3) and ternary CAM.
   Drop the VSA misframing.
4. **Add LOAD_CR / STORE_CR** (fused permute on memory ops).
   Re-run W2 voxel count.
5. **Make polycube/voxel canonicalization the flagship workload.**
   Replace or supplement 3D GoL.
6. **Tighten wording** on "polynomial" in turing_completeness.md
   to specify "polynomial in program size." *(Superseded at
   v0.3.1: the entire TC proof was withdrawn, not just the
   polynomial wording. See `docs/turing_completeness.md`.)*

These are not all the same urgency. Items 1, 2, and 6 are
honesty fixes (don't claim things that aren't true). Items 3, 4,
and 5 are direction fixes (better benchmarks, cleaner ISA).

The headline 4.8× number from Stage B is suspect until item 1
is done. The verdict may shift from "niche" to "no claim"
depending on what the fair SCALAR reveals.

This is exactly the kind of feedback the project needed. Many
thanks.
