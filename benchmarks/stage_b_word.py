"""Stage B (corrected): BT-IS vs WORD-WIDTH SCALAR baseline.

After critique: the original trit-granular SCALAR (CADDX +
CARRY_X + ...) was a hobbled baseline. REBEL-style ISAs use
word-width cube operations; the fair comparison uses
`WADD cd1, cd2` as a single cube-add op.

This runner asserts that BT-IS and SCALAR produce the same
output on each workload before reporting an instruction-count
ratio. A workload that fails the equality check is reported
as FAIL and the script exits non-zero.
"""
import importlib
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "benchmarks"))


def _scalar_final(output_list):
    """SCALAR returns a list of ('vec', tuple) / ('int', n) tuples.
    Return the last emitted value, normalised to match the BT-IS
    parser's single-tuple form."""
    if not output_list:
        return None
    tag, val = output_list[-1]
    return (tag, val)


def parse_btis_output(out: str):
    """Return the last CUBE/INT line emitted by the BT-IS CLI."""
    for line in reversed(out.splitlines()):
        m = re.match(r"^CUBE \((-?\d+),(-?\d+),(-?\d+)\)$", line.strip())
        if m:
            return ("vec", (int(m.group(1)), int(m.group(2)), int(m.group(3))))
        m = re.match(r"^INT (-?\d+)$", line.strip())
        if m:
            return ("int", int(m.group(1)))
    return None


def run_btis(program_path: Path):
    """Run the BT-IS CLI on `program_path` and return
    (output_tuple, mutating_step_count). Mutating step count
    excludes HALT, matching the SCALAR convention."""
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
    return parse_btis_output(out), mutating


def run_word_scalar(module_name: str):
    mod = importlib.import_module(module_name)
    out, mutating = mod.run()
    return _scalar_final(out), mutating


def main():
    workloads = [
        ("W1 rotations",    "programs/w1_rotations.btis",   "w1_word_scalar"),
        ("W2 voxel_count",  "programs/w2_voxel_count.btis", "w2_word_scalar"),
        ("W4 cubeadd_loop", "programs/w4_cubeadd.btis",     "w4_word_scalar"),
    ]

    rows = []
    failures = []
    for name, prog, mod in workloads:
        prog_path = REPO / prog
        btis_out, btis_steps = run_btis(prog_path)
        scalar_out, scalar_steps = run_word_scalar(mod)
        ok = btis_out == scalar_out
        rows.append((name, btis_out, btis_steps, scalar_out, scalar_steps, ok))
        if not ok:
            failures.append(name)

    print()
    print(f"{'workload':<22} {'btis_out':>16} {'SCALAR':>16} "
          f"{'btis':>6} {'SCALAR':>6} {'ratio':>7} {'ok':>4}")
    print("-" * 84)
    for name, btis_out, btis_steps, scalar_out, scalar_steps, ok in rows:
        ratio = (scalar_steps / btis_steps) if btis_steps else float('inf')
        print(f"{name:<22} {str(btis_out):>16} {str(scalar_out):>16} "
              f"{btis_steps:>6} {scalar_steps:>6} {ratio:>6.2f}x "
              f"{'OK' if ok else 'FAIL':>4}")
    print()
    print("'ratio' is SCALAR / BT-IS. Higher = BT-IS more efficient.")
    print("Output equality is required before the ratio is meaningful.")

    if failures:
        print()
        print(f"FAIL: output mismatch on {failures}")
        sys.exit(1)
    print()
    print("All workloads produce matching BT-IS and SCALAR outputs.")


if __name__ == "__main__":
    main()
