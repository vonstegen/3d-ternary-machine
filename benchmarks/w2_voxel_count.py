"""W2 SCALAR: voxel neighborhood count via per-coord addition."""
from scalar_vm import VM, Instr


def build():
    p = []
    # Initialize 8 neighbor memory cells. We need an "accumulator
    # address" and we use C0 = accumulator coord, then mem[(C0.x,
    # C0.y, C0.z)] holds the running total.
    #
    # Simpler: keep accumulator in R0 (trit), accumulate by adding
    # the .x of each neighbor.

    # Set up neighbor values in mem at fixed addresses.
    # mem[(1,0,0)] := (1,0,0) -- alive
    p += [
        Instr("LOAD_IMM", [0, 1]),
        Instr("CGET", [0, 0, 0]),
        Instr("LOAD_IMM", [1, 0]),
        Instr("CGET", [0, 1, 1]),
        Instr("CGET", [0, 1, 2]),
        # C0 = (1, 0, 0)
        Instr("MEM_STORE_C", [0]),
    ]
    # mem[(-1,0,0)] := dead -- we use (0,0,0) which we leave as default 0
    # So skip.

    # mem[(0,1,0)] := alive
    p += [
        Instr("LOAD_IMM", [0, 0]),
        Instr("CGET", [0, 0, 0]),
        Instr("LOAD_IMM", [1, 1]),
        Instr("CGET", [0, 1, 1]),
        Instr("CGET", [0, 1, 2]),
        # C0 = (0, 1, 0)
        Instr("MEM_STORE_C", [0]),
    ]
    # mem[(0,0,-1)] := alive (use -1 trits)
    p += [
        Instr("LOAD_IMM", [0, 0]),
        Instr("CGET", [0, 0, 0]),
        Instr("LOAD_IMM", [1, 0]),
        Instr("CGET", [0, 1, 1]),
        Instr("LOAD_IMM", [1, -1]),
        Instr("CGET", [0, 1, 2]),
        # C0 = (0, 0, -1)
        Instr("MEM_STORE_C", [0]),
    ]
    # mem[(-1,-1,-1)] := alive
    p += [
        Instr("LOAD_IMM", [0, -1]),
        Instr("CGET", [0, 0, 0]),
        Instr("CGET", [0, 1, 1]),
        Instr("CGET", [0, 1, 2]),
        Instr("MEM_STORE_C", [0]),
    ]

    # Accumulator in R0. For each of 4 alive neighbors, fetch
    # mem[neighbor].x into R1, add to R0.
    for addr in [(1, 0, 0), (0, 1, 0), (0, 0, -1), (-1, -1, -1)]:
        # C0 := addr
        for k, v in enumerate(addr):
            p += [
                Instr("LOAD_IMM", [k, v]),
                Instr("CGET", [0, k, k]),
            ]
        # C0 = addr
        # R1 := mem[addr].x (we use MEM_LOAD_C then CPUT)
        p += [
            Instr("MEM_LOAD_C", [0]),
            Instr("CPUT", [1, 0]),  # R1 = C0.x
            # TADD: R0 := R0 + R1 (with saturating carry)
            Instr("TADD", [0, 0, 1]),
        ]

    # emit
    p += [Instr("OUT_T", [0]), Instr("HALT", [])]
    return p


def run():
    vm = VM(build())
    vm.run()
    return vm.output, vm.mutating_steps


if __name__ == "__main__":
    out, m = run()
    print(f"SCALAR W2: mutating_steps={m} output={out}")
