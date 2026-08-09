"""W2 SCALAR (word-width): voxel neighborhood count."""
from scalar_vm_word import VM, Instr


def build():
    p = []
    # Initialize 4 alive neighbors at fixed addresses in mem.
    for addr in [(1, 0, 0), (0, 1, 0), (0, 0, -1), (-1, -1, -1)]:
        for k, v in enumerate(addr):
            p += [
                Instr("LOAD_IMM", [k, v]),
                Instr("CGET", [0, k, k]),
            ]
        # C0 = addr
        p += [Instr("MEM_STORE_C", [0])]

    # Accumulator in C0. For each alive neighbor, fetch it into C1,
    # WADD C0 with C1.
    # Set C1 = addr:
    for addr in [(1, 0, 0), (0, 1, 0), (0, 0, -1), (-1, -1, -1)]:
        for k, v in enumerate(addr):
            p += [
                Instr("LOAD_IMM", [k + 4, v]),  # use R4..R6 for setup
                Instr("CGET", [1, k, k]),
            ]
        # C1 = addr; mem[C1] = value
        p += [Instr("MEM_LOAD_C", [1])]
        # WADD C0 += C1
        p += [Instr("WADD", [0, 1])]

    p += [Instr("OUT_C", [0]), Instr("HALT", [])]
    return p


def run():
    vm = VM(build())
    vm.run()
    return vm.output, vm.mutating_steps


if __name__ == "__main__":
    out, m = run()
    print(f"SCALAR-word W2: mutating_steps={m} output={out}")
