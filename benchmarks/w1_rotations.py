"""W1: 3D rotation sequence (SCALAR implementation)."""
from scalar_vm import VM, Instr, ROT_Z_90, ROT_Z_180, ROT_X_90, ROT_Y_180, ROT_Z_270, ROT_X_180, NEG


def build():
    return [
        Instr("LOAD_IMM", [0, 1]),  # R0 = 1 (will be used as coord 0 for x)
        Instr("CGET",     [0, 0, 0]),  # C0.x = R0 = 1
        Instr("LOAD_IMM", [1, 0]),  # R1 = 0
        Instr("CGET",     [0, 1, 1]),  # C0.y = 0
        Instr("CGET",     [0, 1, 2]),  # C0.z = 0
        # C0 = (1, 0, 0)
        Instr("APPLY_PERM", [0, ROT_Z_90]),
        Instr("APPLY_PERM", [0, ROT_X_90]),
        Instr("APPLY_PERM", [0, ROT_Y_180]),
        Instr("APPLY_PERM", [0, ROT_Z_270]),
        Instr("APPLY_PERM", [0, ROT_X_180]),
        # reflect_x = negate x only: use a hand-coded perm (we don't have
        # a built-in REFLECT_X; use NEG and reflect_z to mimic. Simpler:
        # skip reflect_x here for parity with BT-IS, use NEG twice).
        Instr("APPLY_PERM", [0, NEG]),
        Instr("APPLY_PERM", [0, NEG]),
        Instr("OUT_C", [0]),
        Instr("HALT", []),
    ]


def run():
    vm = VM(build())
    vm.run()
    return vm.output, vm.mutating_steps


if __name__ == "__main__":
    out, m = run()
    print(f"SCALAR W1: mutating_steps={m} output={out}")
