"""W2 SCALAR (word-width): voxel neighborhood count.

Mirror of programs/w2_voxel_count.btis. Both programs:

  1. Initialise 3 alive face neighbors of (0,0,0) at addresses
     (+X, -X, +Y). Each is stored in mem as its own address:
     mem[addr] = addr.
  2. Accumulator C0 := (0,0,0).
  3. For each of the 3 alive neighbors, set C1 = addr, MEM_LOAD_C
     to fetch the value, WADD C0 with C1.
  4. Emit C0.

Result: (0,1,0) on both architectures.

stage_b_word.py asserts the BT-IS and SCALAR outputs match
before reporting an instruction-count ratio.
"""
from scalar_vm_word import VM, Instr


def build():
    addrs = [
        ( 1,  0,  0),
        (-1,  0,  0),
        ( 0,  1,  0),
    ]
    p = []
    # Initialise: mem[addr] := addr for each of 3 alive neighbors.
    for addr in addrs:
        for k, v in enumerate(addr):
            p += [Instr("LOAD_IMM", [k, v]), Instr("CGET", [0, k, k])]
        p += [Instr("MEM_STORE_C", [0])]

    # Reset accumulator: C0 := (0,0,0).
    for k in range(3):
        p += [Instr("LOAD_IMM", [k, 0]), Instr("CGET", [0, k, k])]

    # Accumulation: for each alive neighbor, C1 = addr, MEM_LOAD_C, WADD.
    for addr in addrs:
        for k, v in enumerate(addr):
            p += [Instr("LOAD_IMM", [k, v]), Instr("CGET", [1, k, k])]
        p += [Instr("MEM_LOAD_C", [1])]
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
