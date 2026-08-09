"""Python mirror of the Rust cube primitive.

Used for cross-verification: the same 27-state cube, the same
encode/decode, and the same orbit structure. The Rust crate is the
real implementation; this module exists so that a Python harness can
exercise the same operations and assert they agree.
"""

from dataclasses import dataclass
from typing import Tuple


N = 27  # 3^3


def encode(x: int, y: int, z: int) -> int:
    assert -1 <= x <= 1 and -1 <= y <= 1 and -1 <= z <= 1
    return (x + 1) + 3 * (y + 1) + 9 * (z + 1)


def decode(i: int) -> Tuple[int, int, int]:
    assert 0 <= i < N
    return (i % 3) - 1, ((i // 3) % 3) - 1, (i // 9) - 1


@dataclass(frozen=True)
class Cube:
    x: int
    y: int
    z: int

    def __post_init__(self):
        assert -1 <= self.x <= 1
        assert -1 <= self.y <= 1
        assert -1 <= self.z <= 1

    @classmethod
    def from_idx(cls, idx: int) -> "Cube":
        x, y, z = decode(idx)
        return cls(x, y, z)

    @property
    def idx(self) -> int:
        return encode(self.x, self.y, self.z)

    @property
    def is_center(self) -> bool:
        return self.x == 0 and self.y == 0 and self.z == 0

    @property
    def is_axial(self) -> bool:
        n = (self.x != 0) + (self.y != 0) + (self.z != 0)
        return n == 1

    @property
    def is_face_diag(self) -> bool:
        n = (self.x != 0) + (self.y != 0) + (self.z != 0)
        return n == 2

    @property
    def is_corner(self) -> bool:
        n = (self.x != 0) + (self.y != 0) + (self.z != 0)
        return n == 3

    @property
    def tuple(self) -> Tuple[int, int, int]:
        return (self.x, self.y, self.z)


ALL = [Cube(x, y, z) for z in (-1, 0, 1) for y in (-1, 0, 1) for x in (-1, 0, 1)]


# ---- coordinate-function permutation builder (mirrors symmetry.rs) -----

def build_perm(f):
    p = [0] * N
    for x in (-1, 0, 1):
        for y in (-1, 0, 1):
            for z in (-1, 0, 1):
                cur = encode(x, y, z)
                nx, ny, nz = f(x, y, z)
                p[cur] = encode(nx, ny, nz)
    return p


ROT_Z_90  = build_perm(lambda x, y, z: (-y, x, z))
ROT_Z_180 = build_perm(lambda x, y, z: (-x, -y, z))
ROT_Z_270 = build_perm(lambda x, y, z: (y, -x, z))
ROT_X_90  = build_perm(lambda x, y, z: (x, -z, y))
ROT_X_180 = build_perm(lambda x, y, z: (x, -y, -z))
ROT_X_270 = build_perm(lambda x, y, z: (x, z, -y))
ROT_Y_90  = build_perm(lambda x, y, z: (z, y, -x))
ROT_Y_180 = build_perm(lambda x, y, z: (-x, y, -z))
ROT_Y_270 = build_perm(lambda x, y, z: (-z, y, x))
NEG       = build_perm(lambda x, y, z: (-x, -y, -z))
REFLECT_X = build_perm(lambda x, y, z: (-x, y, z))
REFLECT_Y = build_perm(lambda x, y, z: (x, -y, z))
REFLECT_Z = build_perm(lambda x, y, z: (x, y, -z))


def apply_perm(p, c: Cube) -> Cube:
    return Cube.from_idx(p[c.idx])


if __name__ == "__main__":
    # Quick sanity: 1 + 6 + 12 + 8 = 27
    ce = sum(1 for c in ALL if c.is_center)
    ax = sum(1 for c in ALL if c.is_axial)
    fd = sum(1 for c in ALL if c.is_face_diag)
    co = sum(1 for c in ALL if c.is_corner)
    assert (ce, ax, fd, co) == (1, 6, 12, 8), (ce, ax, fd, co)
    print(f"python cube: {N} states; shape counts = {(ce, ax, fd, co)}")

    # ROT_Z_90^4 = identity
    four = [ROT_Z_90[ROT_Z_90[ROT_Z_90[ROT_Z_90[i]]]] for i in range(N)]
    assert four == list(range(N))
    print("ROT_Z_90^4 = identity verified")

    # Round-trip: apply ROT_X_90 to (0,1,0) -> (0,0,1)
    v = Cube(0, 1, 0)
    assert apply_perm(ROT_X_90, v) == Cube(0, 0, 1)
    print("ROT_X_90: (0,1,0) -> (0,0,1) verified")
