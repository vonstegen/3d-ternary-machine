"""Factor each of the 48 O_h permutations into a minimum-length
sequence of named BT-IS rotor-register ops.

Generator set (each is one BT-IS instruction):
  rot_x_90_r, rot_x_180_r, rot_x_270_r
  rot_y_90_r, rot_y_180_r, rot_y_270_r
  rot_z_90_r, rot_z_180_r, rot_z_270_r
  reflect_x_r, reflect_y_r, reflect_z_r
  neg_r

For each of the 48 O_h elements, BFS to find the shortest
generator sequence whose composition equals that element. The
sequence is then emitted as BT-IS instructions in the order
they should be applied to R0 (post-composition: each new
op becomes the left factor).
"""

import json
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "python"))
from vrml.cube import encode

PERMS_PATH = Path(__file__).resolve().parent / "oh_perms.json"
with open(PERMS_PATH) as f:
    perms = json.load(f)


# Generator set: name -> 27-entry permutation
# These are the same 9 axis rotations + 3 reflections + negation
# already defined in the BT-IS ISA. We re-derive them here from
# the O_h group elements (the first 9 proper rotations correspond
# to the named axis rotations; the 3 reflections to the improper
# elements with identity proper part; the negation to the
# inversion).
GENERATORS = {
    # Axis 90 / 180 / 270 rotations (from the first 9 of the
    # 24 proper rotations).
    "rot_x_90_r":   next(p for p in perms if p["name"] == "Rx90")["perm"],
    "rot_x_180_r":  next(p for p in perms if p["name"] == "Rx180")["perm"],
    "rot_x_270_r":  next(p for p in perms if p["name"] == "Rx270")["perm"],
    "rot_y_90_r":   next(p for p in perms if p["name"] == "Ry90")["perm"],
    "rot_y_180_r":  next(p for p in perms if p["name"] == "Ry180")["perm"],
    "rot_y_270_r":  next(p for p in perms if p["name"] == "Ry270")["perm"],
    "rot_z_90_r":   next(p for p in perms if p["name"] == "Rz90")["perm"],
    "rot_z_180_r":  next(p for p in perms if p["name"] == "Rz180")["perm"],
    "rot_z_270_r":  next(p for p in perms if p["name"] == "Rz270")["perm"],
    # Reflections
    "reflect_x_r":  next(p for p in perms if p["name"] == "iRx180")["perm"],
    "reflect_y_r":  next(p for p in perms if p["name"] == "iRy180")["perm"],
    "reflect_z_r":  next(p for p in perms if p["name"] == "iRz180")["perm"],
    # Negation (improper: I composed with negation)
    "neg_r":        next(p for p in perms if p["name"] == "iI")["perm"],
}


def compose(p, q):
    """p.then(q) = apply p first, then q."""
    return [q[p[i]] for i in range(27)]


def to_key(p):
    return tuple(p)


def factor_bfs(target):
    """BFS to find shortest generator sequence whose composition
    equals `target`."""
    target_key = to_key(target)
    identity = list(range(27))
    if target_key == to_key(identity):
        return []

    # State: (current_perm, sequence_so_far)
    # We want to find a sequence of generators g_1, g_2, ..., g_k
    # such that g_k ∘ ... ∘ g_2 ∘ g_1 = target.
    # BFS forward from identity, applying generators, until we
    # reach target.
    initial_key = to_key(identity)
    queue = deque([(identity, [])])
    visited = {initial_key}
    while queue:
        cur, seq = queue.popleft()
        for gname, gperm in GENERATORS.items():
            new_perm = compose(cur, gperm)
            new_key = to_key(new_perm)
            if new_key in visited:
                continue
            new_seq = seq + [gname]
            if new_key == target_key:
                return new_seq
            visited.add(new_key)
            queue.append((new_perm, new_seq))
    raise RuntimeError(f"could not factor permutation {target_key}")


def main():
    sequences = {}
    for entry in perms:
        name = entry["name"]
        target = entry["perm"]
        seq = factor_bfs(target)
        sequences[name] = seq
        print(f"{name:12s}: {len(seq)} ops: {seq}")
    # Sanity: max sequence length.
    max_len = max(len(s) for s in sequences.values())
    print(f"\nmax factorization length: {max_len}")

    out = Path(__file__).resolve().parent / "factor_sequences.json"
    with open(out, "w") as f:
        json.dump(sequences, f, indent=2)
    print(f"wrote factor sequences to {out}")


if __name__ == "__main__":
    main()
