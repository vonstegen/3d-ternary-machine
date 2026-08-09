"""Verify the 48 O_h permutations form a group.

Checks:
  1. Bijectivity (already checked by oh.py).
  2. Identity is the first element.
  3. Each permutation's inverse is in the list.
  4. The composition of any two permutations is in the list.
  5. Negation (i x, y, z) -> (-x, -y, -z) maps to the
     "improper" half (24 elements).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "python"))
from vrml.cube import encode, decode

PERMS_PATH = Path(__file__).resolve().parent / "oh_perms.json"
with open(PERMS_PATH) as f:
    perms = json.load(f)


def compose(p, q):
    """p.then(q) means apply p first, then q. Returns r such that
    r[i] = q[p[i]]."""
    return [q[p[i]] for i in range(27)]


def inverse(p):
    inv = [0] * 27
    for i, j in enumerate(p):
        inv[j] = i
    return inv


def is_identity(p):
    return p == list(range(27))


# Map permutation -> index for fast lookup.
def to_key(p):
    return tuple(p)


perm_keys = {to_key(p["perm"]): p["name"] for p in perms}

# 1. Identity present?
assert "I" in [p["name"] for p in perms]
# 2. Negation present?  Find it.
neg = [-1] * 27
for x in (-1, 0, 1):
    for y in (-1, 0, 1):
        for z in (-1, 0, 1):
            i = encode(x, y, z)
            ni = encode(-x, -y, -z)
            neg[i] = ni
assert to_key(neg) in perm_keys, "negation not in O_h"

# 3. Each element's inverse is in the list.
for p in perms:
    inv = inverse(p["perm"])
    assert to_key(inv) in perm_keys, \
        f"inverse of {p['name']} not in O_h"

# 4. Closure under composition.
total_pairs = 0
missing = 0
for a in perms:
    for b in perms:
        total_pairs += 1
        c = compose(a["perm"], b["perm"])
        if to_key(c) not in perm_keys:
            missing += 1
            if missing < 5:
                # Print first 5 missing compositions to help debug.
                ax, ay, az = decode(0)
                print(f"MISSING: {a['name']} . {b['name']}: "
                      f"maps (0,0,0)={encode(ax,ay,az)} -> {c[0]}")
assert missing == 0, f"O_h not closed: {missing}/{total_pairs} missing"

# 5. Group order is 48.
assert len(perms) == 48

# 6. Negation maps proper <-> improper.
proper = [p for p in perms if not p["name"].startswith("i")]
improper = [p for p in perms if p["name"].startswith("i")]
assert len(proper) == 24
assert len(improper) == 24

# For each proper element p, the composition p . NEG should be in improper.
for p in proper:
    composed = compose(p["perm"], neg)
    assert to_key(composed) in perm_keys
    # The composed name should start with "i"
    assert perm_keys[to_key(composed)].startswith("i")

# Print a summary.
print(f"O_h group: {len(perms)} elements")
print(f"  {len(proper)} proper rotations")
print(f"  {len(improper)} improper rotations")
print(f"  closure verified over all {total_pairs} pairs")
