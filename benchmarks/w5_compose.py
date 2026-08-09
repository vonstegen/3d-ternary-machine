"""Python reference for the W5 benchmark.

W5: "permutation composition" — the workload that exercises
BT-IS's distinctive feature (first-class rotor registers with
COMPOSE_R / INVERSE_R / APPLY_R).

The task: build a permutation R = R_a * R_b * R_a * R_c *
R_a^-1 * R_b * R_c * R_a from three base rotations, apply R to a
cube state, emit the result.

This is the workload where:
- BT-IS uses rotor registers and COMPOSE_R (1 op per composition).
- SCALAR must compose permutations manually, by repeated
  APPLY_PERM ops on 27-entry tables.

The instruction-count comparison is the benchmark.
"""
from cube_arith import cube_add  # unused but imported for consistency
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
from vrml.cube import ROT_Z_90, ROT_X_90, ROT_Y_90  # noqa


def compose(a, b):
    """Permutation composition: a then b. Returns new permutation table."""
    out = [0] * 27
    for i in range(27):
        out[i] = b[a[i]]
    return out


def apply_perm(perm, cube_idx):
    return perm[cube_idx]


def invert(perm):
    inv = [0] * 27
    for i, j in enumerate(perm):
        inv[j] = i
    return inv


def build_R():
    """Build R = R_a * R_b * R_a * R_c * R_a^-1 * R_b * R_c * R_a."""
    R_a = ROT_Z_90
    R_b = ROT_X_90
    R_c = ROT_Y_90
    R_a_inv = invert(R_a)
    R = compose(compose(compose(compose(compose(compose(compose(R_a, R_b), R_a), R_c), R_a_inv), R_b), R_c), R_a)
    return R


def reference(initial_cube_idx, R):
    return apply_perm(R, initial_cube_idx)


if __name__ == "__main__":
    R = build_R()
    initial = 13  # encode(0, 0, 0) = center
    final = reference(initial, R)
    print(f"W5 reference: cube idx {initial} -> {final}")
