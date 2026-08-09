"""Build the 48 permutations of the cube-symmetry group O_h.

O_h = 24 proper rotations (octahedral group O)
    + 24 improper rotations (each rotation composed with inversion)

The 24 proper rotations of the cube are:
  - Identity
  - 90, 180, 270 degree rotations about the 3 face-axes (X, Y, Z)
  - 180 degree rotations about the 6 face-diagonal axes
  - 120, 240 degree rotations about the 4 body-diagonal axes

Each is represented as a 27-entry lookup table: PERM[i] = j means
state i maps to state j under this transformation.

The 120-degree body-diagonal rotations are derived by conjugating
R_111 (the (1,1,1) axis 120-deg rotation) with the face-axis
reflection that maps (1,1,1) to the target axis:

  R_axis = REFLECT_conj . R_111 . REFLECT_conj
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "python"))
from vrml.cube import encode


def build_perm_from_fn(f):
    perm = [0] * 27
    for x in (-1, 0, 1):
        for y in (-1, 0, 1):
            for z in (-1, 0, 1):
                i = encode(x, y, z)
                nx, ny, nz = f(x, y, z)
                perm[i] = encode(nx, ny, nz)
    return perm


def compose(f, g):
    """f.then(g): apply f, then g."""
    return lambda x, y, z: g(*f(x, y, z))


def reflect_x(x, y, z):
    return (-x, y, z)


def reflect_y(x, y, z):
    return (x, -y, z)


def reflect_z(x, y, z):
    return (x, y, -z)


def negation(x, y, z):
    return (-x, -y, -z)


# --- 24 proper rotations of the cube ---

# 120 around (1,1,1): cycle x -> y -> z -> x
R111_120 = lambda x, y, z: (z, x, y)
# 120 around (-1,1,1) = REFLECT_X . R_111 . REFLECT_X
# REFLECT_X then R_111: (x,y,z) -> (-x,y,z) -> (z,-x,y)
# then REFLECT_X: (z,-x,y) -> (-z,-x,y)
Rm11_120 = compose(reflect_x, compose(R111_120, reflect_x))
# 120 around (1,-1,1) = REFLECT_Y . R_111 . REFLECT_Y
# (x,y,z) -> (x,-y,z) -> (z,x,-y) -> (z,x,-y)
R1m1_120 = compose(reflect_y, compose(R111_120, reflect_y))
# 120 around (1,1,-1) = REFLECT_Z . R_111 . REFLECT_Z
# (x,y,z) -> (x,y,-z) -> (-z,x,y) -> (y,-z,-x)
R11m_120 = compose(reflect_z, compose(R111_120, reflect_z))

# 240 around (1,1,1): cycle x -> z -> y -> x (inverse of 120)
R111_240 = lambda x, y, z: (y, z, x)
# 240 around (-1,1,1): inverse of Rm11_120 = REFLECT_X . R_111_240 . REFLECT_X
Rm11_240 = compose(reflect_x, compose(R111_240, reflect_x))
# 240 around (1,-1,1): inverse of R1m1_120
R1m1_240 = compose(reflect_y, compose(R111_240, reflect_y))
# 240 around (1,1,-1): inverse of R11m_120
R11m_240 = compose(reflect_z, compose(R111_240, reflect_z))


ROTATIONS = [
    # Identity
    ("I",        lambda x, y, z: ( x,  y,  z)),

    # 90 / 180 / 270 around face axes (X, Y, Z)
    ("Rx90",     lambda x, y, z: ( x, -z,  y)),
    ("Rx180",    lambda x, y, z: ( x, -y, -z)),
    ("Rx270",    lambda x, y, z: ( x,  z, -y)),
    ("Ry90",     lambda x, y, z: ( z,  y, -x)),
    ("Ry180",    lambda x, y, z: (-x,  y, -z)),
    ("Ry270",    lambda x, y, z: (-z,  y,  x)),
    ("Rz90",     lambda x, y, z: (-y,  x,  z)),
    ("Rz180",    lambda x, y, z: (-x, -y,  z)),
    ("Rz270",    lambda x, y, z: ( y, -x,  z)),

    # 180 around face-diagonal axes (6 of them)
    ("Rxy180",   lambda x, y, z: ( y,  x, -z)),
    ("Rxmy180",  lambda x, y, z: (-y, -x, -z)),
    ("Rxz180",   lambda x, y, z: ( z, -y,  x)),
    ("Rxzm180",  lambda x, y, z: (-z, -y, -x)),
    ("Ryz180",   lambda x, y, z: (-x,  z,  y)),
    ("Ryzm180",  lambda x, y, z: (-x, -z, -y)),

    # 120 / 240 around body-diagonal axes (4 axes, two rotations each)
    ("R111_120", R111_120),
    ("R111_240", R111_240),
    ("Rm11_120", Rm11_120),
    ("Rm11_240", Rm11_240),
    ("R1m1_120", R1m1_120),
    ("R1m1_240", R1m1_240),
    ("R11m_120", R11m_120),
    ("R11m_240", R11m_240),
]


def main():
    assert len(ROTATIONS) == 24, f"expected 24 rotations, got {len(ROTATIONS)}"
    perm_list = []
    for name, fn in ROTATIONS:
        p = build_perm_from_fn(fn)
        perm_list.append({"name": name, "perm": p})
    # 24 improper rotations: each proper rotation composed with inversion.
    for name, fn in ROTATIONS:
        composed = (lambda f: lambda x, y, z: negation(*f(x, y, z)))(fn)
        p = build_perm_from_fn(composed)
        perm_list.append({"name": f"i{name}", "perm": p})

    assert len(perm_list) == 48

    out = Path(__file__).resolve().parent / "oh_perms.json"
    with open(out, "w") as f:
        json.dump(perm_list, f, indent=2)
    print(f"wrote 48 O_h permutations to {out}")

    for entry in perm_list:
        perm = entry["perm"]
        assert sorted(perm) == list(range(27)), \
            f"{entry['name']} is not a bijection"


if __name__ == "__main__":
    main()
