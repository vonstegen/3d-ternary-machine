"""Sanity checks for the geometric-algebra primitives (continuous GA prototype).

These verify that the rotor/vector math is correct. They will become
cross-checks for the Rust crate's discrete cube operations.

The continuous GA layer is now a *reference implementation* / *continuous
relaxation* of the discrete 27-state cube. The real architecture lives in
the `btis` Rust crate.
"""

import math
import sys
sys.path.insert(0, "/tmp/vrml_proto/python")

from vrml.algebra import Vec, Bivec, Rotor


def approx_eq_vec(a, b, tol=1e-9):
    return abs(a.x - b.x) < tol and abs(a.y - b.y) < tol and abs(a.z - b.z) < tol


def test_rotor_identity():
    R = Rotor.identity()
    v = Vec(1, 2, 3)
    assert approx_eq_vec(R.apply(v), v)


def test_rotor_90_x():
    R = Rotor.from_angle_axis(math.pi / 2, Vec(1, 0, 0))
    assert approx_eq_vec(R.apply(Vec(0, 1, 0)), Vec(0, 0, 1))
    assert approx_eq_vec(R.apply(Vec(0, 0, 1)), Vec(0, -1, 0))


def test_rotor_90_y():
    R = Rotor.from_angle_axis(math.pi / 2, Vec(0, 1, 0))
    assert approx_eq_vec(R.apply(Vec(0, 0, 1)), Vec(1, 0, 0))
    assert approx_eq_vec(R.apply(Vec(1, 0, 0)), Vec(0, 0, -1))


def test_rotor_90_z():
    R = Rotor.from_angle_axis(math.pi / 2, Vec(0, 0, 1))
    assert approx_eq_vec(R.apply(Vec(1, 0, 0)), Vec(0, 1, 0))
    assert approx_eq_vec(R.apply(Vec(0, 1, 0)), Vec(-1, 0, 0))


def test_rotor_180_inverts():
    R = Rotor.from_angle_axis(math.pi, Vec(0, 1, 0))
    assert approx_eq_vec(R.apply(Vec(1, 0, 0)), Vec(-1, 0, 0))


def test_rotor_composition():
    Rz = Rotor.from_angle_axis(math.pi / 2, Vec(0, 0, 1))
    R = Rz * Rz
    assert approx_eq_vec(R.apply(Vec(1, 0, 0)), Vec(-1, 0, 0))


def test_rotor_inverse():
    Rz = Rotor.from_angle_axis(1.234, Vec(0, 0, 1))
    Rzinv = Rz.inverse()
    R = Rz * Rzinv
    assert approx_eq_vec(R.apply(Vec(3, -2, 5)), Vec(3, -2, 5), tol=1e-10)


def test_norm_preserved():
    import random
    random.seed(0)
    for _ in range(20):
        axis = Vec(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))
        ang = random.uniform(-3, 3)
        R = Rotor.from_angle_axis(ang, axis)
        v = Vec(random.uniform(-5, 5), random.uniform(-5, 5), random.uniform(-5, 5))
        n0 = v.norm()
        n1 = R.apply(v).norm()
        assert abs(n0 - n1) < 1e-9


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
        except Exception as e:
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
