"""Generate the BT-IS w5_canon program.

For each of the 48 O_h permutations:
  1. Reset R0 to identity: `load_r 0` (1 op).
  2. Apply the factored sequence of named BT-IS ops to R0
     (k ops, k in [0, 3]).
  3. Load C = (1, 0, 0): `load_axis X` (1 op).
  4. Apply R0 to C: `apply_r 0` (1 op).
  5. Emit: `outc` (1 op).

Total per iteration: 4 + k ops. The setup cost is k, the inner
loop is fixed at 4 ops.

Writes programs/w5_canon.btis.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "python"))
from vrml.cube import decode  # noqa

PERMS_PATH = Path(__file__).resolve().parent / "oh_perms.json"
FACTOR_PATH = Path(__file__).resolve().parent / "factor_sequences.json"

with open(PERMS_PATH) as f:
    perms = json.load(f)
with open(FACTOR_PATH) as f:
    sequences = json.load(f)


def main():
    out_lines = [
        "; w5_canon.btis — W5: apply all 48 O_h permutations to (1,0,0).",
        ";",
        "; The inner loop of voxel canonicalization under O_h.",
        "; For each of 48 group elements, load the permutation into",
        "; R0 from identity, then apply R0 to C = (1, 0, 0) and emit.",
        ";",
        "; Mirror of benchmarks/w5_canon/w5_scalar.py. Both programs",
        "; emit 48 outputs covering the orbit of (1,0,0) under O_h,",
        "; which is exactly the 6 axial states {+/-X, +/-Y, +/-Z},",
        "; each appearing 8 times.",
        ";",
        "; stage_b_word.py asserts the BT-IS and SCALAR outputs",
        "; match before reporting an instruction-count ratio.",
        "",
    ]

    total_setup = 0
    for entry in perms:
        name = entry["name"]
        seq = sequences[name]
        out_lines.append(f"; --- permutation {name} (factor length {len(seq)}) ---")
        out_lines.append("load_r 0       ; R0 := identity")
        for op in seq:
            out_lines.append(f"{op} 0   ; R0 := {op.split('_r')[0]}.then(R0)")
        out_lines.append("load_axis X    ; C := (1, 0, 0)")
        out_lines.append("apply_r 0      ; C := R0(C)")
        out_lines.append("outc           ; emit C")
        out_lines.append("")
        total_setup += len(seq)

    out_lines.append("halt")
    out_lines.append("")

    out_path = Path(__file__).resolve().parent.parent.parent / "programs" / "w5_canon.btis"
    out_path.write_text("\n".join(out_lines))
    print(f"wrote {out_path}")
    print(f"  48 permutations, total setup cost: {total_setup} ops")
    print(f"  per-iter cost: 4 (load_r + load_axis + apply_r + outc) + k (factor length)")


if __name__ == "__main__":
    main()
