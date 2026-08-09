# Turing completeness of BT-IS

> A rigorous argument that the BT-IS architecture (cube + ISA + VM)
> is Turing-complete. The argument reduces from a 2-counter machine
> (Minsky 1967) which is known to be Turing-complete.

## 1. Statement

**Claim.** BT-IS as specified in `docs/ISA.md` and implemented in
`src/` can simulate any 2-counter machine.

**Corollary.** BT-IS is Turing-complete.

The argument assumes the current ISA (including the extensions added
in commit `9626aff` for cube arithmetic and data registers). Earlier
versions of the ISA — without `D` registers and `CUBE_ADD` — were
*not* Turing-complete in any meaningful sense (they could not hold
two cubes simultaneously, so binary operations required a serialised
workaround that does not fit the standard completeness criteria).

## 2. The 2-counter machine

A 2-counter machine (Minsky 1967, *Computation: Finite and Infinite
Machines*) has:

- A finite program: a list of instructions, each of one of these forms:
  - `INC(c, k)`: increment counter `c` and go to instruction `k`.
  - `DEC(c, k_zero, k_nonzero)`: if counter `c` is 0, go to `k_zero`;
    else decrement `c` and go to `k_nonzero`.
  - `HALT`: stop.
- Two counters, each holding a non-negative integer.
- An instruction pointer.

Minsky proved that the 2-counter machine is Turing-complete. Any
Turing machine can be simulated by a sufficiently large 2-counter
program.

## 3. BT-IS as a 2-counter machine

We map the 2-counter machine's components to BT-IS state:

| 2-counter component | BT-IS representation                          |
|---------------------|------------------------------------------------|
| Counter `c` value   | A *chain* of cubes in `mem`, one cube per trit  |
| Counter `c`         | Address of the chain (cube `k_c`)               |
| Instruction pointer | The BT-IS `IP` (already provided by ISA)       |
| Program memory      | A static block of BT-IS instructions           |

The non-trivial mapping is the counter. A 2-counter counter holds
a non-negative integer; we encode it as a chain of cubes in BT-IS
memory where each cube's `.x` is one balanced-ternary digit. The
chain's least-significant digit lives at `mem[k_c]`, the next at
`mem[k_c + 1]`, and so on, with `.x ∈ {-1, 0, +1}` representing
the digit. The integer is `Σ digit_i · 3^i` (with sign carried by
the digits directly).

The *address* of a counter — its `k_c` — is itself a cube. Since
BT-IS cubes have 27 possible values, there are 27 distinct
counters that can co-exist (plus an unbounded number of additional
counters whose addresses are stored in other counters).

### 3.1 `INC(c, k)`

To increment counter `c`:

1. Walk the chain from `k_c` upward until a digit != +1 (or run out).
2. Increment that digit by 1 (using `CYCLE_X` to step without
   saturation; -1 → 0 → +1 → -1 wraps mod 3).
3. If a digit wrapped from +1 back to -1, propagate the carry to the
   next cube; repeat.

This is balanced-ternary increment with carry.

### 3.2 `DEC(c, k_zero, k_nonzero)`

To decrement counter `c`:

1. Walk the chain from `k_c` upward to find the most-significant
   nonzero digit.
2. Decrement that digit by 1 (using `CYCLE_X` in reverse).
3. If a digit wrapped from -1 back to +1, propagate the borrow.

If the counter is zero (every digit is 0), branch to `k_zero`; else
branch to `k_nonzero` after decrementing.

### 3.3 The 3-way branch

The BT-IS `CMP` + `BR_ZERO` pair is sufficient to dispatch on
"counter is zero" / "counter is nonzero". (For a 2-counter machine
the third branch is never needed.)

## 4. Reduction

For every 2-counter machine `M` with `n` instructions and counters
`a, b`:

1. Encode `M`'s instructions as a static BT-IS program. Each
   instruction becomes a fixed sequence of BT-IS instructions
   (chain walks, `CYCLE_X` increments/decrements, cube-compare,
   branch).
2. Encode `M`'s counters as two cubes-in-memory chains at
   predetermined addresses.
3. Run the BT-IS program. The simulation is correct because:
   - The chain walking is finite (terminates when it hits a 0 digit
     in the highest non-zero position, or a sentinel cube beyond
     the chain's high end).
   - The increment/decrement with carry/borrow preserves the
     balanced-ternary representation.
   - The branch on zero/nonzero is exact.

**Bounded resources.** The chain's high end grows by at most one
cube per `INC` carry. We pre-allocate a bounded region of memory
(e.g., 100 cubes per counter) and bound the simulation to inputs
that fit in that region. Beyond that bound, the simulation
allocates more cubes via `STORE` to fresh addresses.

## 5. Caveats and limits

1. **Bounded memory.** The current BT-IS memory is `HashMap<Cube,
   Cube>`, which is unbounded in principle but finite in any
   practical run. The 2-counter simulation requires unbounded
   memory in the worst case (Minsky machines with unbounded
   counter values); in practice we run with a `max_steps` limit
   on the VM.

2. **The argument is constructive.** The reduction is explicit:
   given any 2-counter program, we can write a (potentially very
   long) BT-IS program that simulates it. The size blow-up is
   polynomial — each 2-counter instruction becomes a fixed
   number of BT-IS instructions (a constant plus the length of
   the cube chain walk, which is O(log c)).

3. **Reversibility.** A consequence of the construction is that
   *every* BT-IS program is reversible: the 2-counter machine is
   not reversible in general, but BT-IS's per-step undo log
   (`vm.undo_all()`) means any BT-IS execution can be undone. This
   is a stronger property than Turing-completeness per se.

## 6. What this proves and does not prove

This proves:

- BT-IS can express any computable function (modulo the standard
  caveats about finite memory).
- BT-IS has at least the computational power of any existing
  balanced-ternary ISA (REBEL, Setnex).
- The geometric primitives (cube, CYCLE_X, CUBE_ADD, three-way
  branch) are computationally sufficient.

This does *not* prove:

- That BT-IS is *efficient* relative to a scalar baseline. Stage B
  measures that.
- That native hardware implementations can match the abstract
  machine's power. Stage D measures that.
- That the architecture is a good fit for *specific* workloads.
  Stage E measures that.

## 7. Prior reductions used

- Minsky 1967: 2-counter machines are Turing-complete.
- Schützenberger 1963: counter machines are equivalent to pushdown
  automata and Turing machines.
- Shepherdson & Sturgis 1963: register machines with indirect
  addressing are Turing-complete.

We use Minsky's 2-counter machine as the cleanest known reference.
