"""Stage B (corrected): BT-IS vs WORD-WIDTH SCALAR baseline.

After critique: the original trit-granular SCALAR (CADDX +
CARRY_X + ...) was a hobbled baseline. REBEL-style ISAs use
word-width cube operations; the fair comparison uses
`WADD cd1, cd2` as a single cube-add op.
"""
import importlib
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "benchmarks"))


def count_btis_steps(program_path: Path) -> int:
    bin_ = REPO / "target" / "debug" / "btis"
    if not bin_.exists():
        subprocess.check_call(["cargo", "build", "--quiet"], cwd=str(REPO))
    out = subprocess.check_output(
        [str(bin_), "--trace", str(program_path)],
        cwd=str(REPO),
        text=True,
        stderr=subprocess.STDOUT,
    )
    return sum(1 for l in out.splitlines() if l.startswith("  IP="))


def run_word_scalar(module_name: str) -> tuple:
    mod = importlib.import_module(module_name)
    return mod.run()


def main():
    rows = []
    for name, prog, mod in [
        ("W1 rotations",   "programs/w1_rotations.btis",    "w1_word_scalar"),
        ("W2 voxel_count", "programs/w2_voxel_count.btis",  "w2_word_scalar"),
        ("W4 cubeadd_loop","programs/w4_cubeadd.btis",       "w4_word_scalar"),
    ]:
        prog_path = REPO / prog
        btis = count_btis_steps(prog_path)
        _, scalar = run_word_scalar(mod)
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
