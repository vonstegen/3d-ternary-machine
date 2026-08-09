"""W1 SCALAR (word-width): 3D rotation sequence.

Mirrors programs/w1_rotations.btis exactly. Both programs:

  1. Load (1, 0, 0) into the active cube.
  2. Apply: rot_z_90, rot_x_90, rot_y_180, rot_z_270, rot_x_180,
            reflect_x, neg.
  3. Emit the result.

benchmarks/stage_b_word.py asserts the BT-IS and SCALAR outputs
match before reporting an instruction-count ratio.
"""
from scalar_vm_word import VM, Instr, ROT_Z_90, ROT_X_90, ROT_Y_180, ROT_Z_270, ROT_X_180, REFLECT_X, NEG


def build():
    p = [
        # C0 := (1, 0, 0)
        Instr("LOAD_IMM", [0, 1]),
        Instr("CGET", [0, 0, 0]),
        Instr("LOAD_IMM", [1, 0]),
        Instr("CGET", [0, 1, 1]),
        Instr("LOAD_IMM", [1, 0]),
        Instr("CGET", [0, 1, 2]),
        # 7 geometric ops, same order as programs/w1_rotations.btis
        Instr("APPLY_PERM", [0, ROT_Z_90]),
        Instr("APPLY_PERM", [0, ROT_X_90]),
        Instr("APPLY_PERM", [0, ROT_Y_180]),
        Instr("APPLY_PERM", [0, ROT_Z_270]),
        Instr("APPLY_PERM", [0, ROT_X_180]),
        Instr("APPLY_PERM", [0, REFLECT_X]),
        Instr("APPLY_PERM", [0, NEG]),
        Instr("OUT_C", [0]),
        Instr("HALT", []),
    ]
    return p


def run():
    vm = VM(build())
    vm.run()
    return vm.output, vm.mutating_steps


if __name__ == "__main__":
    out, m = run()
    print(f"SCALAR-word W1: mutating_steps={m} output={out}")
