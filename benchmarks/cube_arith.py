"""Python reference for BT-IS cube arithmetic.

Mirrors the Rust implementation in `src/vm.rs::cube_add`. Used by
`cross_check.py` to verify that BT-IS programs produce the same
sequences as a direct Python computation.

A cube is a triple (x, y, z) with each coordinate in {-1, 0, +1}.
Cube addition is coordinate-wise with carry through (x, y, z):

    x = a.x + b.x  (in {-2..2})
    y = a.y + b.y + carry_x  (in {-3..3})
    z = a.z + b.z + carry_y  (in {-3..3})

Each coordinate is balanced-ternary with values in {-1, 0, +1} and
weights {1, 3, 9, 27, ...}. The 27 cube states form the group Z_3^3.
"""

# Truth table for sum -> (digit, carry), where sum is in {-3..=3} and
# sum = 3*carry + digit.
_TRIT_TABLE = {
    3:  ( 0,  1),
    2:  (-1,  1),
    1:  ( 1,  0),
    0:  ( 0,  0),
    -1: (-1,  0),
    -2: ( 1, -1),
    -3: ( 0, -1),
}


def _balanced_trit(sum_):
    return _TRIT_TABLE[sum_]


def cube_add(a, b):
    sx = a[0] + b[0]
    nx, cx = _balanced_trit(sx)
    sy = a[1] + b[1] + cx
    ny, cy = _balanced_trit(sy)
    sz = a[2] + b[2] + cy
    nz, _ = _balanced_trit(sz)  # carry past z is dropped
    return (nx, ny, nz)


def fib_cube(n):
    """F(0), F(1), ..., F(n) as cubes in Z_3^3 with cube_add."""
    a = (0, 0, 0)
    b = (1, 1, 1)  # F(1) = 1 in BT-3 encoding (digit +1, weight 1)
    out = [a]
    for _ in range(n):
        a, b = b, cube_add(a, b)
        out.append(a)
    return out


def to_int(cube):
    """Decode a cube as the integer x + 3y + 9z (signed)."""
    return cube[0] + 3 * cube[1] + 9 * cube[2]


if __name__ == "__main__":
    cubes = fib_cube(9)
    print("Fibonacci as cubes (Z_3^3 arithmetic):")
    for i, c in enumerate(cubes):
        print(f"  F({i}) = cube {c}  -> integer {to_int(c)}")
