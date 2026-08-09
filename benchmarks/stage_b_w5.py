"""W5 driver: BT-IS vs SCALAR, applying all 48 O_h permutations.

W5 is a multi-emit workload (48 outputs). The driver:

  1. Runs programs/w5_canon.btis on the BT-IS CLI and counts
     mutating steps (excluding HALT).
  2. Runs benchmarks/w5_canon/w5_scalar.py and gets the
     SCALAR output list + mutating_steps.
  3. Asserts the 48 outputs are equivalent (as multisets of
     cubes, since the O_h orbit of (1,0,0) is the 6 axial
     states, each appearing 8 times).
  4. Reports the per-architecture mutating-step count and
     the ratio (SCALAR / BT-IS, higher = BT-IS more efficient).
  5. Exits non-zero on output mismatch.
"""

import importlib
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "benchmarks"))
sys.path.insert(0, str(REPO / "benchmarks" / "w5_canon"))


def parse_btis_outputs(out: str):
    """Return the list of all CUBE lines emitted by the BT-IS CLI,
    in emission order."""
    cubes = []
    for line in out.splitlines():
        m = re.match(r"^CUBE \((-?\d+),(-?\d+),(-?\d+)\)$", line.strip())
        if m:
            cubes.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    return cubes


def run_btis(program_path: Path):
    bin_ = REPO / "target" / "debug" / "btis"
    if not bin_.exists():
        subprocess.check_call(["cargo", "build", "--quiet"], cwd=str(REPO))
    out = subprocess.check_output(
        [str(bin_), "--trace", str(program_path)],
        cwd=str(REPO),
        text=True,
        stderr=subprocess.STDOUT,
    )
    trace_steps = sum(1 for l in out.splitlines() if l.startswith("  IP="))
    # HALT is the last trace entry; exclude it.
    mutating = max(trace_steps - 1, 0)
    return parse_btis_outputs(out), mutating


def run_scalar(module_name: str):
    mod = importlib.import_module(module_name)
    out, mutating = mod.run()
    cubes = [t[1] for t in out if t[0] == "vec"]
    return cubes, mutating


def main():
    btis_out, btis_steps = run_btis(REPO / "programs" / "w5_canon.btis")
    scalar_out, scalar_steps = run_scalar("w5_scalar")

    print()
    print(f"BT-IS  W5: {len(btis_out)} outputs, {btis_steps} mutating steps")
    print(f"SCALAR W5: {len(scalar_out)} outputs, {scalar_steps} mutating steps")

    # Output equivalence: same multiset of cubes.
    btis_counts = Counter(btis_out)
    scalar_counts = Counter(scalar_out)
    same_counts = btis_counts == scalar_counts
    same_count = len(btis_out) == len(scalar_out)

    if same_counts and same_count:
        print()
        print(f"  output orbits match: {dict(btis_counts)}")
        print(f"  ratio (SCALAR / BT-IS): {scalar_steps / btis_steps:.2f}x")
        # Expected: 1.00x since both APPLY_PERM and apply_r are 1 op.
        # BT-IS pays the rotor-register setup cost (89 ops factored
        # across 48 perms); SCALAR pays cube-rebuild cost (6 ops per
        # perm = 288 ops).
        print()
        if btis_steps < scalar_steps:
            print(f"  BT-IS faster by {scalar_steps - btis_steps} steps "
                  f"({100 * (scalar_steps - btis_steps) / scalar_steps:.1f}%)")
        elif btis_steps > scalar_steps:
            print(f"  BT-IS slower by {btis_steps - scalar_steps} steps "
                  f"({100 * (btis_steps - scalar_steps) / scalar_steps:.1f}%)")
        else:
            print("  BT-IS and SCALAR are tied")
    else:
        print()
        print("FAIL: output mismatch")
        print(f"  BT-IS  counts: {dict(btis_counts)}")
        print(f"  SCALAR counts: {dict(scalar_counts)}")
        if not same_count:
            print(f"  length: BT-IS={len(btis_out)} vs SCALAR={len(scalar_out)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
