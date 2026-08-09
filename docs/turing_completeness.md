# Turing completeness of BT-IS

> **Status at v0.3.1: claim withdrawn.** The proof that
> previously appeared in this document is unsound. The
> archive of the broken proof is preserved below as a
> historical record. Re-deriving the proof is out of
> scope for v0.3.1.

## 1. Why the previous proof is unsound

The previous proof (`docs/turing_completeness.md` at
v0.2.0-niche and v0.3.0-negative) attempted to reduce
BT-IS to Minsky's 2-counter machine by encoding each
counter as a chain of cubes in `HashMap<Cube, Cube>`-
keyed memory. Two distinct errors invalidated the proof.

**Error 1 — bounded address space.** The proof
represented each counter as a chain of cubes, one cube
per balanced-ternary digit, stored at addresses
`mem[k_c]`, `mem[k_c + 1]`, ... where `k_c` is itself a
cube. The `HashMap<Cube, Cube>` has keys drawn from
`{-1, 0, +1}^3` — 27 distinct keys. Therefore:

- A counter can be represented as a chain of at most
  ~27 cubes before the address space runs out.
- A 2-counter machine with counter values exceeding
  `3^27` cannot be simulated.
- The "unbounded memory" caveat in §5 of the previous
  proof (line 119-124) was incorrect: `HashMap<Cube,
  Cube>` is finite in cardinality, not just "finite in
  practice." Minsky machines with unbounded counter
  values cannot be simulated.

The proof as written only established Turing-completeness
for 2-counter machines whose counter values stay bounded
by `3^27`. That's a finite-state machine, not a
Turing-complete one.

**Error 2 — wrong DEC algorithm.** The proof's DEC
algorithm (§3.2) was: "walk to the most-significant
non-zero digit, decrement it, propagate borrow." This is
not balanced-ternary subtraction. Concrete counterexample:

- Counter value `2` encoded as `mem[k_c].x = -1,
  mem[k_c + 1].x = +1` (representing `1·(-1) + 3·(+1) = 2`).
- DEC walks to the most-significant non-zero: `+1` at
  `mem[k_c + 1]`.
- Decrement `+1` → `0` with no borrow (since `0` is
  in `{-1, 0, +1}`).
- Result: `mem[k_c].x = -1, mem[k_c + 1].x = 0`,
  representing `-1` — but the correct result of `2 - 1`
  is `+1`, not `-1`.

The correct DEC algorithm is LSD-walk with borrow:
decrement the least-significant non-zero digit, propagate
borrow to the next digit only if the LSD wrapped from
`-1` to `+1` (rather than from `0` to `-1`). The previous
proof did not describe this algorithm.

## 2. What the architecture actually is

The v0.3.1 implementation supports:

- A finite 27-state cube register `C` (per
  `src/cube.rs:N = 27`).
- 8 rotor registers `R[0..7]`, each holding a 27-entry
  permutation table.
- 4 cube data registers `D[0..3]`.
- A `HashMap<Cube, Cube>`-keyed memory with at most 27
  distinct keys.
- An instruction set of ~50 opcodes (rotations,
  reflections, arithmetic, comparison, branches, memory,
  control).

This is a finite-state machine with bounded memory
(cardinality at most `27^N` for some `N` dependent on
how the registers and memory are used). It is **not**
Turing-complete as specified at v0.3.1.

## 3. What would be required to establish TC

To make BT-IS Turing-complete, two changes are needed:

**Change A — unbounded address space.** Add a new
address type `A ∈ ℕ` (or an unbounded balanced-ternary
address word) and three-operand register-memory ops:

```
ALOAD  Rdst, [A]      ; C := mem[A]
ASTORE [A], Rsrc       ; mem[A] := C
AINC   [A]             ; A := A + 1
ADEC   [A]             ; A := A - 1
```

Cube values continue to live in `mem[C]` (cube-keyed),
but address generation is unbounded. The two memory
spaces are independent.

**Change B — correct DEC algorithm.** Replace the
proof's MSD-decrement with LSD-walk-with-borrow. The
correct algorithm is:

```
DEC(c, k_zero, k_nonzero):
  # Walk from k_c toward higher indices.
  # At each step, if mem[curr].x is not 0, decrement
  # it. If it wrapped from -1 to +1, propagate borrow
  # to the next cube (CYCLE_X in reverse). If no borrow
  # propagates, stop.
  # If the entire chain is zero, branch to k_zero.
  # Else, branch to k_nonzero.
```

With these two changes, the Minsky reduction is sound.
The proof sketch in §3-4 of the previous version
(`docs/turing_completeness.md` git history at v0.2.0-
niche and earlier) is otherwise structurally correct —
the encoding, the INC algorithm, the 3-way branch all
work. The two errors above are local to the address
space and the DEC step.

## 4. What's stored here

For reference, the previous (broken) proof is preserved
in the git history of `docs/turing_completeness.md`. The
last commit that contained it is in the v0.3.0-negative
tag. The proof is also available in the v0.2.0-niche tag.

To see the broken proof:

```bash
git show v0.2.0-niche:docs/turing_completeness.md
git show v0.3.0-negative:docs/turing_completeness.md
```

The proof is left in git history (not deleted) because
the errors are part of the project's research record and
removing them would obscure what was tried. The current
file marks the claim as withdrawn.

## 5. Practical implications

At v0.3.1:

- The architecture is a clean reference implementation
  of a balanced-ternary cube machine. It runs the
  workloads in `programs/`, all the unit tests, and the
  Python cross-check.
- It is *not* Turing-complete. The "TC proved" claim
  in the v0.2.0-niche verdict was incorrect.
- The "intrinsic reversibility of the rotation /
  reflection subset" claim is unaffected and remains
  true: each of the 12 named geometric ops is a group
  element with an inverse in $O_h$.
- The "journal-based reversibility via `vm.undo_all()`"
  claim is also unaffected: the undo log is a Bennett
  history tape that works for any register VM, including
  this one.
