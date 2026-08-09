"""W4 SCALAR: repeated cube-add."""
from scalar_vm import VM, Instr


def build():
    p = []
    # Initialize: mem[(1,1,1)] := (1,1,1); C0 := (1,1,1).
    p += [
        Instr("LOAD_IMM", [0, 1]),
        Instr("CGET", [0, 0, 0]),
        Instr("LOAD_IMM", [1, 1]),
        Instr("CGET", [0, 1, 1]),
        Instr("CGET", [0, 1, 2]),
        Instr("MEM_STORE_C", [0]),  # mem[(1,1,1)] := C0
        # Re-load C0 = (1,1,1) for the loop
        Instr("LOAD_IMM", [0, 1]),
        Instr("CGET", [0, 0, 0]),
        Instr("LOAD_IMM", [1, 1]),
        Instr("CGET", [0, 1, 1]),
        Instr("CGET", [0, 1, 2]),
    ]
    # Each cube-add takes: CADDX + CADDY + CADDZ + CARRY_X + CARRY_Y + CARRY_Z = 6 ops.
    # We unroll 10 iterations.
    for _ in range(10):
        p += [
            Instr("CADDX", [0, 0]),  # C0.x := C0.x + C0.x  (no carry!)
            Instr("CADDY", [0, 0]),  # same for y, z
            Instr("CADDZ", [0, 0]),
            # Now propagate carry chain. We need CARRY_X to look at C0.x.
            # Our CARRY_X assumes the cube is in C0.
            Instr("CARRY_X", []),
            Instr("CARRY_Y", []),
            Instr("CARRY_Z", []),
        ]
    p += [Instr("OUT_C", [0]), Instr("HALT", [])]
    return p


def run():
    vm = VM(build())
    vm.run()
    return vm.output, vm.mutating_steps


if __name__ == "__main__":
    out, m = run()
    print(f"SCALAR W4: mutating_steps={m} output={out}")
