#!/usr/bin/env python3
"""Cross-verify that the Rust and Python BT-IS cube primitives agree.

Reads benchmarks/rust_tables.json (produced by `cargo run --bin
btis_dump_tables --release`) and compares each named rotation's 27-entry
LUT against the Python implementation in vrml/cube.py.
"""
import json
import sys
from pathlib import Path

# Make the python prototype importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "vrml_proto" / "python"))

import vrml.cube as pc  # noqa: E402

JSON_PATH = Path(__file__).resolve().parent.parent / "benchmarks" / "rust_tables.json"
if not JSON_PATH.exists():
    sys.stderr.write(f"missing {JSON_PATH}; run `cargo run --bin btis_dump_tables --release` first\n")
    sys.exit(2)

with open(JSON_PATH) as f:
    data = json.load(f)

# verify all 27 states match between Rust and Python
rust_states = {s["idx"]: (s["x"], s["y"], s["z"]) for s in data["states"]}
assert len(rust_states) == 27
for idx in range(27):
    x, y, z = pc.decode(idx)
    assert rust_states[idx] == (x, y, z), f"state {idx} mismatch"

print(f"OK: 27/27 cube states agree")

# verify per-permutation tables
def check(name: str, py_table):
    rust_table = data["perms"][name]
    assert len(rust_table) == 27
    mismatches = [(i, rust_table[i], py_table[i]) for i in range(27) if rust_table[i] != py_table[i]]
    if mismatches:
        print(f"FAIL {name}: {len(mismatches)} mismatches: {mismatches[:5]}")
        return False
    print(f"OK   {name}")
    return True

ok = True
for name, py in [
    ("ROT_Z_90",  pc.ROT_Z_90),
    ("ROT_Z_180", pc.ROT_Z_180),
    ("ROT_Z_270", pc.ROT_Z_270),
    ("ROT_X_90",  pc.ROT_X_90),
    ("ROT_X_180", pc.ROT_X_180),
    ("ROT_X_270", pc.ROT_X_270),
    ("ROT_Y_90",  pc.ROT_Y_90),
    ("ROT_Y_180", pc.ROT_Y_180),
    ("ROT_Y_270", pc.ROT_Y_270),
    ("REFLECT_X", pc.REFLECT_X),
    ("REFLECT_Y", pc.REFLECT_Y),
    ("REFLECT_Z", pc.REFLECT_Z),
    ("NEG",       pc.NEG),
]:
    ok &= check(name, py)

# Spot checks: orbits
def orbit(name, start, table):
    seen = []
    s = start
    for _ in range(8):
        s = table[s]
        seen.append(s)
    return seen

# (1,1,1) is the corner (1,1,1) -> encode = 13
# Under ROT_Z_90: (x,y,z)->(-y,x,z). (1,1,1)->(-1,1,1)=encode(-1,1,1)=0+3*2+9*0=6
assert pc.apply_perm(pc.ROT_Z_90, pc.Cube(1,1,1)) == pc.Cube(-1,1,1)
print("OK   orbit spot check: ROT_Z_90 on (1,1,1) = (-1,1,1)")

# 4x ROT_Z_90 = identity
for i in range(27):
    s = i
    for _ in range(4):
        s = pc.ROT_Z_90[s]
    assert s == i
print("OK   ROT_Z_90^4 = identity on all 27 states")

print()
print("=" * 50)
print("ALL CHECKS PASSED" if ok else "FAILURES")
sys.exit(0 if ok else 1)
