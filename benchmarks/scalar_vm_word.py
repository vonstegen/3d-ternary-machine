"""SCALAR baseline — WORD-WIDTH variant.

Same state as scalar_vm.py (8 trit + 8 cube registers) but with
a fair cube-wide ALU:

  WADD  cd1, cd2     -- C[cd1] := C[cd1] + C[cd2]  (full 27-state
                          add with carry through x, y, z, in one op)
  WSUB  cd1, cd2     -- full 27-state subtract, one op
  WCMP  cd1, cd2     -- F := sign(C[cd1].x - C[cd2].x)  (3-way)

  LOAD_IMM / CGET / CPUT / APPLY_PERM / OUT_C / OUT_T / HALT
  unchanged.

The word-width SCALAR matches REBEL's "27-trit word" model: a
single cube is one operand, and cube-add is one instruction.
This is the *fair* baseline the Stage B critique demanded.

Compare against:
- scalar_vm.py (per-trit, explicit carries) -- the original
  baseline. Tends to make BT-IS look better than it should
  on arithmetic-heavy workloads.
- scalar_vm_word.py (this file) -- a fair cube-wide ALU.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class Instr:
    opcode: str
    args: list


def _balanced_trit(sum_):
    return {
        3:  ( 0,  1),
        2:  (-1,  1),
        1:  ( 1,  0),
        0:  ( 0,  0),
        -1: (-1,  0),
        -2: ( 1, -1),
        -3: ( 0, -1),
    }[sum_]


def _cube_add(a, b):
    sx = a[0] + b[0]
    nx, cx = _balanced_trit(sx)
    sy = a[1] + b[1] + cx
    ny, cy = _balanced_trit(sy)
    sz = a[2] + b[2] + cy
    nz, _ = _balanced_trit(sz)
    return (nx, ny, nz)


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
ROT_Z_270 = build_perm(lambda x, y, z: (y, -x, z))
ROT_X_90  = build_perm(lambda x, y, z: (x, -z, y))
ROT_X_180 = build_perm(lambda x, y, z: (x, -y, -z))
ROT_X_270 = build_perm(lambda x, y, z: (x, z, -y))
ROT_Y_90  = build_perm(lambda x, y, z: (z, y, -x))
ROT_Y_180 = build_perm(lambda x, y, z: (-x, y, -z))
ROT_Y_270 = build_perm(lambda x, y, z: (-z, y, x))
NEG       = build_perm(lambda x, y, z: (-x, -y, -z))


class VM:
    def __init__(self, program: List[Instr]):
        self.R = [0] * 8
        self.C = [(0, 0, 0)] * 8
        self.F = 0
        self.IP = 0
        self.mem = {}
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
                raise RuntimeError("step limit")
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
        elif op == "TCMP":
            da, db = self.R[a[0]], self.R[a[1]]
            self.F = 1 if da > db else (-1 if da < db else 0)
        elif op == "BR_GT":
            if self.F > 0: next_ip = a[0]
        elif op == "BR_EQ":
            if self.F == 0: next_ip = a[0]
        elif op == "BR_LT":
            if self.F < 0: next_ip = a[0]
        elif op == "JMP":
            next_ip = a[0]
        elif op == "CGET":
            cube = list(self.C[a[0]])
            cube[a[2]] = self.R[a[1]]
            self.C[a[0]] = tuple(cube)
        elif op == "CPUT":
            self.R[a[0]] = self.C[a[1]][0]
        elif op == "WADD":
            # word-width cube add: one instruction
            self.C[a[0]] = _cube_add(self.C[a[0]], self.C[a[1]])
        elif op == "WSUB":
            self.C[a[0]] = _cube_add(self.C[a[0]],
                                     (-self.C[a[1]][0],
                                      -self.C[a[1]][1],
                                      -self.C[a[1]][2]))
        elif op == "WCMP":
            # 3-way compare on cube .x
            da, db = self.C[a[0]][0], self.C[a[1]][0]
            self.F = 1 if da > db else (-1 if da < db else 0)
        elif op == "APPLY_PERM":
            perm = a[1]
            x, y, z = self.C[a[0]]
            new_idx = perm[encode(x, y, z)]
            nx = (new_idx % 3) - 1
            ny = ((new_idx // 3) % 3) - 1
            nz = (new_idx // 9) - 1
            self.C[a[0]] = (nx, ny, nz)
        elif op == "OUT_C":
            self.output.append(("vec", self.C[a[0]]))
        elif op == "OUT_T":
            self.output.append(("int", self.R[a[0]]))
        elif op == "MEM_STORE_C":
            self.mem[self.C[a[0]]] = self.C[a[0]]
        elif op == "MEM_LOAD_C":
            self.C[a[0]] = self.mem.get(self.C[a[0]], (0, 0, 0))
        else:
            raise RuntimeError(f"unknown opcode: {op}")

        if mutating:
            self.mutating_steps += 1
        self.IP = next_ip
