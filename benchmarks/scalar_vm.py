"""SCALAR baseline: simple REBEL-style balanced-ternary RISC.

State: 8 trit-valued registers `R0..R7` and 8 cube-valued registers
`C0..C7`. A cube is 3 trits `(x, y, z)`. The ISA deliberately
treats cubes as 3 separate scalars: every "cube op" is decomposed
into 3 (or more) per-coord scalar ops.

This is the *non-geometric* baseline: the SCALAR machine has no
concept of "cube as a unit" — it must compose each geometric op
out of scalar per-coord ops.

ISA summary (each instruction is one step):

  LOAD_IMM rd, n        -- rd := n  (rd is a trit register, n in {-1,0,+1})
  TADD     rd, a, b     -- rd := a + b  (with carry, balanced ternary)
  TSUB     rd, a, b     -- rd := a - b
  TCMP     a, b         -- F := sign(a - b)
  BR_GT    L            -- if F > 0: jump
  BR_EQ    L            -- if F == 0: jump
  BR_LT    L            -- if F < 0: jump
  JMP      L            -- unconditional jump
  CGET     cd, i        -- C[cd].i := R[i]  (cube coord load)
  CPUT     i, cd        -- R[i] := C[cd].x  (cube coord store; we use x by convention)
  CADDX    cd1, cd2     -- C[cd1].x := C[cd1].x + C[cd2].x (no carry)
  CADDY    cd1, cd2     -- C[cd1].y := C[cd1].y + C[cd2].y
  CADDZ    cd1, cd2     -- C[cd1].z := C[cd1].z + C[cd2].z
  CARRY_X              -- propagate carry from C.x to C.y (per trit)
  CARRY_Y              -- propagate carry from C.y to C.z
  CARRY_Z              -- propagate carry past C.z (drop)
  APPLY_PERM cd, perm  -- apply a 27-element permutation to cube
  OUT_C    cd           -- emit cube
  OUT_T    rd           -- emit trit
  HALT

The instruction set is intentionally granular so that "BT-IS cube_add"
(which is 1 op) corresponds to "5 SCALAR ops" (3x CADD + 2 CARRY).
"""

import math
import sys
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Instr:
    opcode: str
    args: list


def _balanced_trit(sum_):
    """sum -> (digit, carry), sum in {-3..=3}."""
    return {
        3:  (0,  1),
        2:  (-1, 1),
        1:  (1,  0),
        0:  (0,  0),
        -1: (-1, 0),
        -2: (1, -1),
        -3: (0, -1),
    }[sum_]


# Permutation tables for APPLY_PERM (mirror BT-IS symmetry.rs).
def encode(x, y, z):
    return (x + 1) + 3 * (y + 1) + 9 * (z + 1)


def build_perm(f):
    p = [0] * 27
    for x in (-1, 0, 1):
        for y in (-1, 0, 1):
            for z in (-1, 0, 1):
                cur = encode(x, y, z)
                nx, ny, nz = f(x, y, z)
                p[cur] = encode(nx, ny, nz)
    return p


ROT_Z_90  = build_perm(lambda x, y, z: (-y, x, z))
ROT_Z_180 = build_perm(lambda x, y, z: (-x, -y, z))
ROT_X_90  = build_perm(lambda x, y, z: (x, -z, y))
ROT_Y_90  = build_perm(lambda x, y, z: (z, y, -x))
ROT_Y_180 = build_perm(lambda x, y, z: (-x, y, -z))
ROT_X_180 = build_perm(lambda x, y, z: (x, -y, -z))
ROT_Z_270 = build_perm(lambda x, y, z: (y, -x, z))
NEG       = build_perm(lambda x, y, z: (-x, -y, -z))


class VM:
    N_TRIT_REGS = 8
    N_CUBE_REGS = 8

    def __init__(self, program: List[Instr]):
        self.R = [0] * self.N_TRIT_REGS       # trit registers
        self.C = [(0, 0, 0)] * self.N_CUBE_REGS  # cube registers
        self.F = 0  # last compare: -1, 0, +1
        self.IP = 0
        self.mem = {}  # cube-keyed memory
        self.output = []
        self.steps = 0
        self.mutating_steps = 0
        self.halted = False
        self.program = program

    def run(self, max_steps=10_000_000):
        while not self.halted:
            if self.IP >= len(self.program):
                self.halted = True
                break
            if self.steps >= max_steps:
                raise RuntimeError(f"step limit {max_steps} exceeded")
            self.step()

    def step(self):
        instr = self.program[self.IP]
        next_ip = self.IP + 1
        self.steps += 1
        op = instr.opcode
        a = instr.args
        mutating = True

        if op == "HALT":
            self.halted = True
            mutating = False
        elif op == "NOP":
            mutating = False
        elif op == "LOAD_IMM":
            assert -1 <= a[1] <= 1
            self.R[a[0]] = a[1]
        elif op == "TADD":
            n = self.R[a[1]] + self.R[a[2]]
            d, c = _balanced_trit(n)
            # saturate at -1/+1; carry is recorded in a side flag we
            # ignore here (TADD alone does not propagate carry; carry
            # is explicit via CARRY_*).
            self.R[a[0]] = d
            # carry not recorded separately; CARRY_* handles propagation
            # in cube context.
        elif op == "TSUB":
            n = self.R[a[1]] - self.R[a[2]]
            d, c = _balanced_trit(n)
            self.R[a[0]] = d
        elif op == "TCMP":
            da = self.R[a[0]]; db = self.R[a[1]]
            if da > db: self.F = 1
            elif da < db: self.F = -1
            else: self.F = 0
        elif op == "BR_GT":
            if self.F > 0: next_ip = a[0]
        elif op == "BR_EQ":
            if self.F == 0: next_ip = a[0]
        elif op == "BR_LT":
            if self.F < 0: next_ip = a[0]
        elif op == "JMP":
            next_ip = a[0]
        elif op == "CGET":
            # C[cd].i := R[i]  (i is 0/1/2 for x/y/z)
            cube = list(self.C[a[0]])
            cube[a[2]] = self.R[a[1]]
            self.C[a[0]] = tuple(cube)
        elif op == "CPUT":
            # R[i] := C[cd].x
            self.R[a[0]] = self.C[a[1]][0]
        elif op == "CADDX":
            c1 = list(self.C[a[0]]); c2 = list(self.C[a[1]])
            c1[0] = c1[0] + c2[0]
            # no carry propagation
            self.C[a[0]] = tuple(c1)
        elif op == "CADDY":
            c1 = list(self.C[a[0]]); c2 = list(self.C[a[1]])
            c1[1] = c1[1] + c2[1]
            self.C[a[0]] = tuple(c1)
        elif op == "CADDZ":
            c1 = list(self.C[a[0]]); c2 = list(self.C[a[1]])
            c1[2] = c1[2] + c2[2]
            self.C[a[0]] = tuple(c1)
        elif op == "CARRY_X":
            # Propagate any overflow past +1 or below -1 in C[0].x to C[0].y.
            c = list(self.C[0])
            d, carry = _balanced_trit(c[0])
            c[0] = d
            c[1] = c[1] + carry
            self.C[0] = tuple(c)
        elif op == "CARRY_Y":
            c = list(self.C[0])
            d, carry = _balanced_trit(c[1])
            c[1] = d
            c[2] = c[2] + carry
            self.C[0] = tuple(c)
        elif op == "CARRY_Z":
            c = list(self.C[0])
            d, _ = _balanced_trit(c[2])
            c[2] = d
            self.C[0] = tuple(c)
        elif op == "APPLY_PERM":
            # perm is a[1]; cd is a[0]
            perm = a[1]
            x, y, z = self.C[a[0]]
            old_idx = encode(x, y, z)
            new_idx = perm[old_idx]
            nx = (new_idx % 3) - 1
            ny = ((new_idx // 3) % 3) - 1
            nz = (new_idx // 9) - 1
            self.C[a[0]] = (nx, ny, nz)
        elif op == "OUT_C":
            self.output.append(("vec", self.C[a[0]]))
        elif op == "OUT_T":
            self.output.append(("int", self.R[a[0]]))
        elif op == "MEM_STORE_C":
            # mem[C[cd]] := C[cd]
            addr = self.C[a[0]]
            self.mem[addr] = self.C[a[0]]
        elif op == "MEM_LOAD_C":
            # C[cd] := mem[C[cd]]
            addr = self.C[a[0]]
            self.C[a[0]] = self.mem.get(addr, (0, 0, 0))
        elif op == "MEM_STORE_T":
            # mem[R[r]] := (R[r], R[r], R[r])  (axial shortcut)
            addr = (self.R[a[0]], self.R[a[0]], self.R[a[0]])
            self.mem[addr] = (self.R[a[0]], self.R[a[0]], self.R[a[0]])
        elif op == "MEM_LOAD_T":
            # R[r] := mem[(R[r], R[r], R[r])].x
            addr = (self.R[a[0]], self.R[a[0]], self.R[a[0]])
            self.R[a[0]] = self.mem.get(addr, (0, 0, 0))[0]
        else:
            raise RuntimeError(f"unknown opcode: {op}")

        if mutating:
            self.mutating_steps += 1
        self.IP = next_ip


def run_btis(program_path):
    """Run a BT-IS program and return the VM's mutating-step count."""
    import subprocess
    out = subprocess.check_output(
        ["./target/debug/btis", "--trace", str(program_path)],
        cwd=".",
        text=True,
    )
    # parse trace output
    n = 0
    for line in out.splitlines():
        if line.startswith("  IP="):
            n += 1
    return n
