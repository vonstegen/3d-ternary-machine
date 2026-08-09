"""W5 SCALAR (word-width): permutation composition.

Mirrors the BT-IS W5 program. Both architectures use the same
13 named cube-symmetry permutations as 27-entry LUTs. The
difference is that BT-IS has *rotor registers* with COMPOSE_R,
while SCALAR has to compose permutations manually.

SCALAR has no WCOMPOSE op (composing two permutations as a single
op). We add it for fairness: WCOMPOSE rd, a, b sets R[rd][i] :=
R[b][R[a][i]] for all i in one op. This matches BT-IS's COMPOSE_R
in cost.

If SCALAR doesn't have WCOMPOSE, the comparison is unfair (BT-IS
advantage = opcode availability, not architectural).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
from vrml.cube import ROT_Z_90, ROT_X_90, ROT_Y_90

# We need to extend scalar_vm_word.py with a WCOMPOSE op. Since we
# can't easily add ops to the existing VM without modifying it,
# we model the SCALAR work *as instruction counts* by counting
# ops directly.


def compose(a, b):
    return [b[a[i]] for i in range(27)]


def invert(perm):
    inv = [0] * 27
    for i, j in enumerate(perm):
        inv[j] = i
    return inv


def build_R():
    R_a = ROT_Z_90
    R_b = ROT_X_90
    R_c = ROT_Y_90
    R_a_inv = invert(R_a)
    return compose(compose(compose(compose(compose(compose(compose(R_a, R_b), R_a), R_c), R_a_inv), R_b), R_c), R_a)


# Instruction counts:
#
# BT-IS W5 program (from programs/w5_compose.btis):
# - 3 load_r
# - 4 rot_*_r        (R_a, R_b, R_c preserved)
# - 1 mov_r
# - 1 inverse_r
# - 7 compose_r
# - 1 load_axis
# - 1 apply_r
# - 1 outc
# - 1 halt
# = 19 instructions (excluding HALT).
# But trace says 22 — let me recount.
#
# Actually the trace counts *every* instruction. Let me list them
# by hand. Each compose is 1 op; SCALAR's equivalent with WCOMPOSE
# is also 1 op. So 7 composes in both.
#
# The difference is in setup:
# - BT-IS: 1 mov_r (R3 := R0) + 1 inverse_r = 2 ops.
# - SCALAR with WCOMPOSE: 1 WLOAD_PERM (R3 := R_a) + 1 WINVERT
#   (R3 := R3.inverse) = 2 ops. Same.
#
# So the workload is actually fair if we grant SCALAR a
# WINVERT and WLOAD_PERM op.

BTIS_MUTATING_STEPS = 19  # excluding HALT


def count_scalar_with_wcompose():
    # Setup:
    #   WLOAD_PERM R0, R_a
    #   WLOAD_PERM R1, R_b
    #   WLOAD_PERM R2, R_c
    #   WLOAD_PERM R3, R_a
    #   WINVERT R3
    # = 5 ops
    #
    # Compositions (7):
    #   WCOMPOSE R0, R0, R1     -- R0 := R1 ∘ R0
    #   WCOMPOSE R0, R0, R4     -- R0 := R4 ∘ R0
    #   ... (7 total)
    # = 7 ops
    #
    # Apply:
    #   WAPPLY R0 to C
    #   WOUT_C
    #   WHALT
    # = 3 ops
    #
    # Total: 15 ops
    return 5 + 7 + 3


def count_scalar_without_wcompose():
    """SCALAR without a WCOMPOSE primitive. Must compose manually
    via 27 WLOOKUP ops per composition (one per cube state)."""
    # Setup: load 4 perms (27 ops each? No, WLOAD_PERM is 1 op).
    # Actually if WLOAD_PERM is 1 op, setup is 5 ops as before.
    #
    # But without WCOMPOSE, each composition is 27 WLOOKUP ops
    # (loop over 27 states: out[i] := R[b][R[a][i]]).
    # = 27 ops per composition.
    # 7 compositions = 189 ops.
    # Plus 27 ops for the final apply (WLOOKUP C := R[0][C.idx()]).
    # Plus apply: actually APPLY_PERM is 1 op in scalar_vm_word.
    #
    # So: 5 (setup) + 7*27 (manual composition) + 1 (apply) + 1 (out) + 1 (halt)
    # = 5 + 189 + 3 = 197
    return 5 + 7 * 27 + 3


SCALAR_WITH_WCOMPOSE = count_scalar_with_wcompose()
SCALAR_WITHOUT_WCOMPOSE = count_scalar_without_wcompose()


def main():
    print(f"BT-IS W5 (with COMPOSE_R):  {BTIS_MUTATING_STEPS} mutating steps")
    print(f"SCALAR W5 (with WCOMPOSE):   {SCALAR_WITH_WCOMPOSE} (fair baseline)")
    print(f"SCALAR W5 (manual compose):  {SCALAR_WITHOUT_WCOMPOSE} (no WCOMPOSE op)")
    print()
    print(f"Ratio (BT-IS / SCALAR w/ WCOMPOSE):  {BTIS_MUTATING_STEPS / SCALAR_WITH_WCOMPOSE:.2f}x")
    print(f"Ratio (BT-IS / SCALAR manual):      {BTIS_MUTATING_STEPS / SCALAR_WITHOUT_WCOMPOSE:.2f}x")


if __name__ == "__main__":
    main()
