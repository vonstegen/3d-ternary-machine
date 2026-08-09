"""W4 SCALAR (word-width): repeated cube-add.

Mirrors the BT-IS W4 cube-add loop, using the word-width SCALAR
benchmark/scalar_vm_word.py. Each iteration is one WADD op
(= one BT-IS cube_add op).
"""
from scalar_vm_word import VM, Instr


def build():
    p = []
    # Initialize: mem[(1,1,1)] := (1,1,1); C0 := (1,1,1).
    # 7 setup ops to put C0 = (1,1,1) and write it to mem.
    p += [
        Instr("LOAD_IMM", [0, 1]),
        Instr("CGET", [0, 0, 0]),
        Instr("LOAD_IMM", [1, 1]),
        Instr("CGET", [0, 1, 1]),
        Instr("CGET", [0, 1, 2]),
        Instr("MEM_STORE_C", [0]),
        # Reload C0 = (1,1,1) for the loop
        Instr("LOAD_IMM", [0, 1]),
        Instr("CGET", [0, 0, 0]),
        Instr("LOAD_IMM", [1, 1]),
        Instr("CGET", [0, 1, 1]),
        Instr("CGET", [0, 1, 2]),
    ]
    # 10 iterations: 10 WADD ops.
    for _ in range(10):
        p += [Instr("WADD", [0, 0])]
    p += [Instr("OUT_C", [0]), Instr("HALT", [])]
    return p


def run():
    vm = VM(build())
    vm.run()
    return vm.output, vm.mutating_steps


if __name__ == "__main__":
    out, m = run()
    print(f"SCALAR-word W4: mutating_steps={m} output={out}")
