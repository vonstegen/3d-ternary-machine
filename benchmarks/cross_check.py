#!/usr/bin/env python3
"""Cross-check BT-IS programs against Python references.

For each program in the `programs/` directory, run it through the
BT-IS CLI and compare its output to a Python reference.

Currently:
    - fibonacci.btis   vs cube_arith.fib_cube
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "benchmarks"))
import cube_arith  # noqa: E402


def run_btis(program_path: Path, repo: Path) -> list[tuple[str, tuple]]:
    """Run a .btis file and parse its output into a list of cubes."""
    out = subprocess.check_output(
        [str(repo / "target" / "debug" / "btis"), str(program_path)],
        cwd=str(repo),
        text=True,
    )
    cubes = []
    for line in out.strip().splitlines():
        if line.startswith("CUBE "):
            m = re.match(r"CUBE \((-?\d+),(-?\d+),(-?\d+)\)", line)
            if m:
                x, y, z = int(m.group(1)), int(m.group(2)), int(m.group(3))
                cubes.append(("cube", (x, y, z)))
        elif line.startswith("INT "):
            n = int(line[4:])
            cubes.append(("int", n))
    return cubes


def check_fibonacci(repo: Path) -> bool:
    program = repo / "programs" / "fibonacci.btis"
    if not program.exists():
        print(f"SKIP fibonacci: {program} not found")
        return True
    print(f"CHECK fibonacci: {program.name}")
    actual = run_btis(program, repo)
    expected = [("cube", c) for c in cube_arith.fib_cube(9)]
    if actual == expected:
        print(f"  OK: {len(actual)} cubes match Python reference")
        return True
    print(f"  FAIL: {len(actual)} cubes; expected {len(expected)}")
    for i, (a, e) in enumerate(zip(actual, expected)):
        if a != e:
            print(f"    [{i}] got {a}, expected {e}")
    if len(actual) != len(expected):
        print(f"    length mismatch")
    return False


def main() -> int:
    repo = REPO
    btis_bin = repo / "target" / "debug" / "btis"
    if not btis_bin.exists():
        print(f"building BT-IS (no binary at {btis_bin})")
        subprocess.check_call(
            ["cargo", "build", "--quiet"], cwd=str(repo),
        )
    ok = True
    ok &= check_fibonacci(repo)
    print()
    print("ALL CHECKS PASSED" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
