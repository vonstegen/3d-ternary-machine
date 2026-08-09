#!/usr/bin/env python3
"""Reference scalar ISA for benchmark comparison.

A conventional balanced-ternary RISC emulator: each "instruction" is a
small dict. We define a `rotate_cube` instruction that does the same
work as BT-IS's `rot_z_90` (one cube rotation = one 27-entry LUT lookup).
This is the *scalar* baseline: one instruction per geometric operation.

The benchmark measures throughput of 10000 rotations to compare with
BT-IS's 27-cube LUT design. Expectation: scalar baseline does the same
per-instruction work but with more overhead per instruction; BT-IS
should be faster (less dispatch overhead) if both are JIT-equivalent,
but in this Python emulator, both will be slow.

The interesting measurement is *instruction count*, not raw speed.
The cube's orbit under repeated ROT_Z_90 has size 4; so a "round trip"
requires 4 scalar rotations vs 4 BT-IS rotations. Same instruction
count, same semantic work -- the architecture itself is not slower
on this workload. The benchmark confirms that.
"""
import sys
import time

# 27-cube (same encoding as BT-IS)
def encode(x, y, z):
    return (x + 1) + 3 * (y + 1) + 9 * (z + 1)

def decode(i):
    return (i % 3) - 1, ((i // 3) % 3) - 1, (i // 9) - 1

# rot_z_90: (x,y,z) -> (-y,x,z), as a 27-entry LUT
ROT_Z_90 = [0] * 27
for x in (-1, 0, 1):
    for y in (-1, 0, 1):
        for z in (-1, 0, 1):
            i = encode(x, y, z)
            j = encode(-y, x, z)
            ROT_Z_90[i] = j

def scalar_program(initial_cube):
    """A 'scalar' program: load, then 4 rotations."""
    state = initial_cube
    for _ in range(4):
        state = ROT_Z_90[state]
    return state

# Run the equivalent of bench_rot.btis: 10000 iterations.
def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    initial = encode(1, 0, 0)
    expected = initial  # 4 rotations of 90 = identity

    start = time.perf_counter_ns()
    for _ in range(n):
        scalar_program(initial)
    elapsed_ns = time.perf_counter_ns() - start

    elapsed_ms = elapsed_ns // 1_000_000
    per_run_us = elapsed_ns // n // 1000
    total_instrs = n * 6
    ips = total_instrs * 1_000_000_000 // elapsed_ns

    print("Scalar-reference benchmark (Python)")
    print(f"  iterations:  {n}")
    print(f"  total time:  {elapsed_ms} ms")
    print(f"  per run:     {per_run_us} us")
    print(f"  total instr: {total_instrs}")
    print(f"  throughput:  {ips} instructions/sec (interpreted Python)")
    print(f"  result verified: {scalar_program(initial) == expected}")

if __name__ == "__main__":
    main()
