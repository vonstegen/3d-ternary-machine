"""W5 SCALAR (word-width): apply all 48 O_h permutations to one cube.

This is the inner loop of voxel canonicalization. The full
algorithm (apply 48 group elements to all 27 cells of a pattern)
costs the same on both architectures because both have an O(1)
APPLY_PERM primitive. The discriminating question is whether
BT-IS's rotor-register APPLY_R can be cheaper than SCALAR's
APPLY_PERM per single application.

Both primitives are 1 op per apply. The honest expectation is
ratio = 1.00x. Any deviation measures setup cost, not the
primitive itself.

Pattern: input cube (1, 0, 0). For each of the 48 O_h elements,
apply that permutation to the input, emit the resulting cube.

The SCALAR VM has no cube-copy primitive, so each iteration
rebuilds C0 = (1, 0, 0) from scratch (6 ops). This is the
SCALAR's setup cost; BT-IS's equivalent (using rotor registers
with `apply_r`) is the comparison point.

stage_b_word.py will be extended to also run W5; both
architectures emit the same 48 outputs.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "python"))
from scalar_vm_word import VM, Instr
from oh import build_perm_from_fn, ROTATIONS, negation


def load_perms():
    """Return a list of 48 27-entry permutations."""
    perms = []
    for name, fn in ROTATIONS:
        perms.append((name, build_perm_from_fn(fn)))
    for name, fn in ROTATIONS:
        composed = (lambda f: lambda x, y, z: negation(*f(x, y, z)))(fn)
        perms.append((f"i{name}", build_perm_from_fn(composed)))
    return perms


def build():
    p = []
    perms = load_perms()
    for name, perm in perms:
        # Setup C0 = (1, 0, 0). 6 ops.
        p += [
            Instr("LOAD_IMM", [0, 1]), Instr("LOAD_IMM", [1, 0]), Instr("LOAD_IMM", [2, 0]),
            Instr("CGET", [0, 0, 0]), Instr("CGET", [0, 1, 1]), Instr("CGET", [0, 2, 2]),
        ]
        # Apply permutation to C0. 1 op.
        p += [Instr("APPLY_PERM", [0, perm])]
        # Emit C0. 1 op.
        p += [Instr("OUT_C", [0])]

    p += [Instr("HALT", [])]
    return p


def run():
    vm = VM(build())
    vm.run()
    return vm.output, vm.mutating_steps


if __name__ == "__main__":
    out, m = run()
    print(f"SCALAR-word W5: mutating_steps={m}")
    print(f"  total: {len(out)} outputs (expected 48)")
