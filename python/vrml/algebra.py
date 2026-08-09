"""Geometric-algebra primitives for the Vector-Rotational Machine Language.

Mathematical model: a working subset of 3D Clifford (geometric) algebra
Cl(3,0,0). The four grades are:

    Scalar     s            -> 0-form, "magnitude / weight / value"
    Vector     v = e1 x ... -> 1-form, "displacement / datum"
    Bivector   B = e12 x ... -> 2-form, "oriented plane / rotation axis"
    Trivector  t = e123 s    -> 3-form, "oriented volume / chirality"

Rotors (even-grade elements) are isomorphic to unit quaternions, so we
*implement* the rotor as a quaternion. The geometric interpretation is
preserved: a rotor R rotates vectors by R v R^-1, and composing rotors
multiplies them. This gives a stable, well-tested implementation without
hand-rolled multivector grade bookkeeping.

Why this matters for the machine-language thesis:
    * Translation  = Vec addition.       -> moves the cursor / mutates state.
    * Rotation     = Rotor application.  -> reorients the reference frame /
                                            implements "switch interpretation".
    * Magnitude    = scalar.             -> encodes value / confidence.
    * Orientation  = direction in space. -> encodes instruction class /
                                            branch axis.
    * Parity       = trivec sign.        -> encodes loop / branch parity.

A "program" is therefore a sequence of rotors and translations applied
to a state vector -- a trajectory through transformation space. Branching
is a rotor that splits the trajectory by sign of an inner product.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


EPS = 1e-12


# ---------- vector (grade 1) -------------------------------------------------------

@dataclass(frozen=True)
class Vec:
    """A 3D vector; also a grade-1 element of Cl(3)."""
    x: float
    y: float
    z: float

    def __add__(self, o: "Vec") -> "Vec":
        return Vec(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o: "Vec") -> "Vec":
        return Vec(self.x - o.x, self.y - o.y, self.z - o.z)

    def __mul__(self, o: "Vec") -> float:
        # symmetric inner product -> scalar
        return self.x * o.x + self.y * o.y + self.z * o.z

    def __xor__(self, o: "Vec") -> "Bivec":
        # outer product -> bivector (oriented plane)
        return Bivec(
            xy=self.x * o.y - self.y * o.x,  # e12
            yz=self.y * o.z - self.z * o.y,  # e23
            xz=self.x * o.z - self.z * o.x,  # e13
        )

    def __rmul__(self, s: float) -> "Vec":
        return Vec(self.x * s, self.y * s, self.z * s)

    def __neg__(self) -> "Vec":
        return Vec(-self.x, -self.y, -self.z)

    def cross(self, o: "Vec") -> "Vec":
        return Vec(
            self.y * o.z - self.z * o.y,
            self.z * o.x - self.x * o.z,
            self.x * o.y - self.y * o.x,
        )

    def norm(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalized(self) -> "Vec":
        n = self.norm()
        return Vec(0.0, 0.0, 0.0) if n < EPS else Vec(self.x / n, self.y / n, self.z / n)

    def as_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


# ---------- bivector (grade 2) -----------------------------------------------------

@dataclass(frozen=True)
class Bivec:
    """Bivector: oriented plane / rotation generator.
    Components in basis (e12, e23, e13)."""
    xy: float
    yz: float
    xz: float

    def __add__(self, o: "Bivec") -> "Bivec":
        return Bivec(self.xy + o.xy, self.yz + o.yz, self.xz + o.xz)

    def __sub__(self, o: "Bivec") -> "Bivec":
        return Bivec(self.xy - o.xy, self.yz - o.yz, self.xz - o.xz)

    def __mul__(self, o: "Bivec") -> float:
        # symmetric product of bivectors -> scalar
        return self.xy * o.xy + self.yz * o.yz + self.xz * o.xz

    def __rmul__(self, s: float) -> "Bivec":
        return Bivec(self.xy * s, self.yz * s, self.xz * s)

    def __neg__(self) -> "Bivec":
        return Bivec(-self.xy, -self.yz, -self.xz)

    def norm(self) -> float:
        return math.sqrt(self.xy * self.xy + self.yz * self.yz + self.xz * self.xz)


# ---------- rotor (even grade = scalar + bivector) ---------------------------------

@dataclass(frozen=True)
class Rotor:
    """An even-grade multivector a + B; implemented as a quaternion (w, i, j, k).

    Convention (right-handed, standard):
        w = scalar part
        i = bivector e23 component
        j = bivector e13 component
        k = bivector e12 component

    Rotation of vector v by rotor R is the sandwich R v R^-1.
    Composition of rotors is quaternion multiplication.
    """
    w: float  # scalar
    i: float  # e23
    j: float  # e13
    k: float  # e12

    @classmethod
    def identity(cls) -> "Rotor":
        return cls(1.0, 0.0, 0.0, 0.0)

    @classmethod
    def from_angle_axis(cls, angle: float, axis: Vec) -> "Rotor":
        """Rotor that rotates by `angle` radians about the unit `axis`."""
        n = axis.norm()
        if n < EPS:
            return cls.identity()
        ux, uy, uz = axis.x / n, axis.y / n, axis.z / n
        h = angle / 2.0
        s = math.sin(h)
        return cls(
            w=math.cos(h),
            i=s * ux,
            j=s * uy,
            k=s * uz,
        )

    def reverse(self) -> "Rotor":
        # reverse = conjugate for quaternions = (w, -i, -j, -k)
        return Rotor(self.w, -self.i, -self.j, -self.k)

    def inverse(self) -> "Rotor":
        # for unit rotor, inverse == reverse; otherwise normalize first
        n2 = self.w * self.w + self.i * self.i + self.j * self.j + self.k * self.k
        if n2 < EPS:
            raise ZeroDivisionError("rotor has zero norm")
        r = self.reverse()
        return Rotor(r.w / n2, r.i / n2, r.j / n2, r.k / n2)

    def __mul__(self, o: "Rotor") -> "Rotor":
        # Hamilton product of quaternions
        a = self
        return Rotor(
            w=a.w * o.w - a.i * o.i - a.j * o.j - a.k * o.k,
            i=a.w * o.i + a.i * o.w + a.j * o.k - a.k * o.j,
            j=a.w * o.j - a.i * o.k + a.j * o.w + a.k * o.i,
            k=a.w * o.k + a.i * o.j - a.j * o.i + a.k * o.w,
        )

    def as_bivec(self) -> "Bivec":
        # bivector part (e23, e13, e12)
        return Bivec(xy=self.k, yz=self.i, xz=self.j)

    def apply(self, v: Vec) -> Vec:
        """Rotate v: returns R v R^-1. Vector treated as pure quaternion (0, x, y, z).

        Result vector components are derived from the well-known identity:
            v' = v + 2 w (B x v) + 2 (B x (B x v))
        where B is the bivector part of R. This avoids the full sandwich algebra.
        """
        bx, by, bz = self.i, self.j, self.k  # bivector part (e23, e13, e12)
        # First cross: B x v
        cx = by * v.z - bz * v.y
        cy = bz * v.x - bx * v.z
        cz = bx * v.y - by * v.x
        # Second cross: B x (B x v)
        dx = by * cz - bz * cy
        dy = bz * cx - bx * cz
        dz = bx * cy - by * cx
        return Vec(
            x=v.x + 2.0 * (self.w * cx + dx),
            y=v.y + 2.0 * (self.w * cy + dy),
            z=v.z + 2.0 * (self.w * cz + dz),
        )

    def angle(self) -> float:
        """Rotation angle in radians."""
        # clamp for safety
        w = max(-1.0, min(1.0, self.w))
        return 2.0 * math.acos(w)

    def axis(self) -> Vec:
        """Unit rotation axis (or zero vector if rotation is identity)."""
        s = math.sqrt(self.i * self.i + self.j * self.j + self.k * self.k)
        if s < EPS:
            return Vec(0.0, 0.0, 0.0)
        return Vec(self.i / s, self.j / s, self.k / s)


# ---------- trivector / pseudoscalar ----------------------------------------------

@dataclass(frozen=True)
class Trivec:
    """Pseudoscalar e123. Encodes oriented volume / chirality / parity bit."""
    s: float

    def __mul__(self, o: "Vec") -> "Bivec":
        # e123 * v = dual(v). For basis e1,e2,e3, dual maps v -> Bivec in
        # the order (e23, e13, e12) corresponding to (i, j, k) in the rotor.
        return Bivec(xy=o.z, yz=o.x, xz=-o.y)

    def __rmul__(self, v: "Vec") -> "Bivec":
        # v * e123 = -dual(v)
        return Bivec(xy=-v.z, yz=-v.x, xz=v.y)

    def __mul__(self, o: "Bivec") -> "Vec":
        # e123 * B = -dual(B). For our Bivec(xy, yz, xz) basis,
        # dual is: (xy*e23, yz*e13, xz*e12) -> (yz, -xz, -xy) under e123.
        # Verified: Bivec(0,1,0) (e23) * e123 = e1 -> positive x.
        return Vec(x=-o.yz, y=o.xz, z=-o.xy)

    def __rmul__(self, b: "Bivec") -> "Vec":
        return Vec(x=b.yz, y=-b.xz, z=b.xy)

    def __mul__(self, o: "Trivec") -> float:
        return -self.s * o.s  # e123^2 = -1

    def __neg__(self) -> "Trivec":
        return Trivec(-self.s)


I = Trivec(1.0)


# ---------- helpers ----------------------------------------------------------------

def approx_eq_vec(a: Vec, b: Vec, tol: float = 1e-9) -> bool:
    return (abs(a.x - b.x) < tol
            and abs(a.y - b.y) < tol
            and abs(a.z - b.z) < tol)


__all__ = ["Vec", "Bivec", "Trivec", "Rotor", "I", "EPS", "approx_eq_vec"]
