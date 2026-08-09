"""Stage B benchmark driver.

Runs each Stage B workload in BT-IS and in the SCALAR baseline,
counts mutating instruction steps, and reports the comparison.

The four workloads (W1..W4) probe different architectural features:

  W1: pure 27-state LUT ops (rotations). Expected: equal cost.
  W2: cube-arithmetic + cube memory (voxel count). Expected: BT-IS favored.
  W3: 3-way comparison + branch (merge step). Expected: equal cost.
  W4: pure cube-add loop. Expected: BT-IS strongly favored.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "benchmarks"))


def count_btis_steps(program_path: Path) -> int:
    """Run a BT-IS program with --trace and count steps."""
    bin_ = REPO / "target" / "debug" / "btis"
    if not bin_.exists():
        subprocess.check_call(["cargo", "build", "--quiet"], cwd=str(REPO))
    out = subprocess.check_output(
        [str(bin_), "--trace", str(program_path)],
        cwd=str(REPO),
        text=True,
        stderr=subprocess.STDOUT,
    )
    n = sum(1 for line in out.splitlines() if line.startswith("  IP="))
    return n


def run_scalar(workload_module: str) -> tuple:
    """Import and run a SCALAR workload, return (output, mutating_steps)."""
    import importlib
    mod = importlib.import_module(workload_module)
    return mod.run()


def measure_w1():
    btis = count_btis_steps(REPO / "programs" / "w1_rotations.btis")
    out, scalar_steps = run_scalar("w1_rotations")
    return btis, scalar_steps


def measure_w2():
    btis = count_btis_steps(REPO / "programs" / "w2_voxel_count.btis")
    out, scalar_steps = run_scalar("w2_voxel_count")
    return btis, scalar_steps


def measure_w4():
    btis = count_btis_steps(REPO / "programs" / "w4_cubeadd.btis")
    out, scalar_steps = run_scalar("w4_cubeadd")
    return btis, scalar_steps


def main():
    rows = []
    for name, fn in [("W1 rotations", measure_w1),
                     ("W2 voxel_count", measure_w2),
                     ("W4 cubeadd_loop", measure_w4)]:
        btis, scalar = fn()
        rows.append((name, btis, scalar))

    print()
    print(f"{'workload':<22} {'BT-IS':>8} {'SCALAR':>8} {'ratio':>8}")
    print("-" * 50)
    for name, btis, scalar in rows:
        ratio = scalar / btis if btis else float('inf')
        print(f"{name:<22} {btis:>8} {scalar:>8} {ratio:>7.2f}x")

    print()
    print("'ratio' is SCALAR / BT-IS. Higher = BT-IS more efficient.")


if __name__ == "__main__":
    main()
