"""Instruction set for the Vector-Rotational Machine Language (VRML).

The ISA is deliberately tiny: every opcode is a geometric verb
(translation, rotation, projection, intersection, composition, comparison).
Higher-level constructs (arithmetic, branching, memory, subroutines) are
derived from these primitives.

Operand conventions:
    A, B          : vector registers
    S             : scalar register (float; integer values are encoded as
                   rounded floats -- the VM has no integer type, by design,
                   because integers are a special case of scalars under the
                   same geometric interpretation.)
    R0..R7        : rotor (transformation) registers
    P             : current program rotor (read-only for the program)
    C             : state / cursor vector
    F             : flag vector (gt, eq, lt) from the last CMP
    addr          : memory address (non-negative integer)
    k             : axis label (string: "X", "Y", "Z", "XI", "YI", "ZI", etc.)
    target        : label (string)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, Union, Optional

# operand types
Operand = Union[str, int, float, Tuple[float, float, float]]


@dataclass(frozen=True)
class Instr:
    opcode: str
    args: Tuple[Operand, ...] = ()

    def __repr__(self) -> str:
        if not self.args:
            return f"{self.opcode}"
        return f"{self.opcode} " + ", ".join(_fmt(a) for a in self.args)


def _fmt(a):
    if isinstance(a, str):
        return a
    if isinstance(a, tuple):
        return "(" + ", ".join(repr(x) for x in a) + ")"
    return repr(a)


# The full opcode table.  Keep these stable; the assembler keys on them.
OPCODES = {
    # vector / scalar data movement
    "LOAD_AXIS",     # LOAD_AXIS k            -> A = unit(k)
    "LOAD_VEC",      # LOAD_VEC x,y,z         -> A = Vec(x,y,z)
    "LOADI",         # LOADI s                -> S = float(s)
    "MOV",           # MOV dst, src           -> dst = src
    "OUTI",          # OUTI S                 -> emit scalar S
    "OUTV",          # OUTV A|C               -> emit vector

    # geometric primitives -- the heart of the machine
    "TRANSLATE",     # TRANSLATE C|A, v       -> dst += v       (translation)
    "ROTATE",        # ROTATE C|A, Rk         -> dst = Rk.apply(dst)   (rotation)
    "ROTATE_AXIS",   # ROTATE_AXIS dst, k, theta  -> dst = R(k, theta).apply(dst)
    "COMPOSE",       # COMPOSE Rd, Rs         -> Rd = Rd * Rs   (compose rotors)
    "INVERSE",       # INVERSE Rk             -> Rk = Rk.inverse()
    "PROJ",          # PROJ A, B, t           -> A = lerp(A, B, t) (project)
    "INTERSECT",     # INTERSECT A, B         -> A = A ^ B (bivector)
    "SCALE",         # SCALE A, s             -> A = s * A
    "NORM",          # NORM A                 -> S = A.norm()
    "INNER",         # INNER A, B             -> S = A * B (dot)
    "CROSS",         # CROSS A, B             -> A = A.cross(B)
    "DUAL",          # DUAL A                 -> A = I * A  (vec <-> bivec)

    # comparison / branching (control flow as geometry)
    "CMP",           # CMP A, B               -> F = sign(A-B)
    "BRANCH_GT",     # BRANCH_GT target       -> if F.x>0: jump
    "BRANCH_EQ",     # BRANCH_EQ target       -> if F.y>0: jump
    "BRANCH_LT",     # BRANCH_LT target       -> if F.z>0: jump
    "BRANCH_AXIS",   # BRANCH_AXIS k, target  -> if C projected on k > 0: jump
    "JMP",           # JMP target             -> unconditional jump
    "CALL",          # CALL target            -> push frame, jump
    "RET",           # RET                    -> pop frame
    "HALT",          # HALT                   -> stop

    # memory (addresses are coordinates in a 1D lattice)
    "STORE",         # STORE A|S, addr        -> mem[addr] = src
    "LOAD",          # LOAD A, addr           -> A = mem[addr]
}


# fixed axis table for symbolic LOAD_AXIS / ROTATE_AXIS
AXES = {
    "X":  (1.0, 0.0, 0.0),
    "Y":  (0.0, 1.0, 0.0),
    "Z":  (0.0, 0.0, 1.0),
    "XI": (-1.0, 0.0, 0.0),
    "YI": (0.0, -1.0, 0.0),
    "ZI": (0.0, 0.0, -1.0),
}


def axis_vec(name: str):
    from .algebra import Vec
    return Vec(*AXES[name])
