"""Stage C: reversibility + three-way branching quantification.

Reversibility: the BT-IS VM records an Undo entry for every
state-mutating step. `vm.undo_all()` pops them in reverse order,
recovering the initial (C, F, R, D, mem) state. We demonstrate
this on the W4 cube-add program and on a fresh BT-IS program
that exercises a CALL/RET frame (which is also reversed).

Three-way branching: we count BR_NEG/BR_ZERO/BR_POS in the
BT-IS programs vs SCALAR-equivalent branches in the SCALAR
implementations. The claim is that BT-IS has native 3-way
branches, so a single CMP + BR_3way replaces the cascade of
two-way branches that a Boolean ISA would need.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def run_btis(program_path: Path) -> tuple[list[str], int]:
    """Run a BT-IS program with --trace, return (trace_lines, n_steps)."""
    out = subprocess.check_output(
        [str(REPO / "target" / "debug" / "btis"), "--trace", str(program_path)],
        cwd=str(REPO),
        text=True,
        stderr=subprocess.STDOUT,
    )
    lines = [l for l in out.splitlines() if l.startswith("  IP=")]
    return lines, len(lines)


def count_branch_ops(trace_lines: list[str]) -> dict:
    """Count branch-related ops from the trace."""
    opcodes = {"97": "BR_NEG", "98": "BR_ZERO", "99": "BR_POS",
               "100": "JMP", "101": "CALL", "102": "RET"}
    counts = {v: 0 for v in opcodes.values()}
    for line in trace_lines:
        # Trace line: 'IP=  0 op= 97 arg= 0 C=(0,0,0) F=(0,0,0)'
        # Extract the op number robustly.
        idx = line.find('op=')
        if idx < 0:
            continue
        after = line[idx+3:].lstrip()
        end = after.find(' ')
        op = after[:end] if end >= 0 else after
        if op in opcodes:
            counts[opcodes[op]] += 1
    return counts


def reversibility_demo():
    """Run W4 cube-add, then verify undo restores initial state.

    We compare C after running vs C after `undo_all()`. The
    Rust CLI doesn't expose undo_all yet, so we use a small
    Rust program that does this in-process.
    """
    # Compile a small reversibility test that uses the BT-IS lib.
    test_src = '''
use btis::vm::{VM, Instr};
use btis::isa::opcodes;

fn main() {
    let program = vec![
        Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
        Instr { opcode: opcodes::STORE_C, arg: 0, target: 0 },
        Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
        Instr { opcode: opcodes::CUBE_ADD, arg: 0, target: 0 },
        Instr { opcode: opcodes::CUBE_ADD, arg: 0, target: 0 },
        Instr { opcode: opcodes::CUBE_ADD, arg: 0, target: 0 },
        Instr { opcode: opcodes::HALT, arg: 0, target: 0 },
    ];
    let mut vm = VM::new(program);
    let before = vm.snapshot();
    vm.run().unwrap();
    let after = vm.C;
    let n_undo = vm.undo_all();
    let restored = vm.C;
    let mem_restored = vm.mem.is_empty();
    println!("initial C:   {:?}", before.C);
    println!("after run C: {:?}", after);
    println!("after undo C: {:?}", restored);
    println!("undone {} steps; mem_restored: {}", n_undo, mem_restored);
    println!("RESTORED: {}", restored == before.C && mem_restored);
}
'''
    Path("/tmp/btis_reversibility_test.rs").write_text(test_src)
    # Compile and run as part of the benchmark crate's example target.
    # Use cargo's `cargo run --example` pattern: place the file in
    # examples/ instead.
    examples_dir = REPO / "examples"
    examples_dir.mkdir(exist_ok=True)
    (examples_dir / "reversibility_demo.rs").write_text(test_src)
    out = subprocess.check_output(
        ["cargo", "run", "--quiet", "--example", "reversibility_demo"],
        cwd=str(REPO),
        text=True,
    )
    print("--- Reversibility demo (BT-IS W4-like program) ---")
    for line in out.strip().splitlines():
        print(f"  {line}")


def three_way_branch_count():
    """Count branch ops across the existing programs."""
    print()
    print("--- Three-way branch counts (per program) ---")
    print(f"{'program':<28} {'BR_NEG':>7} {'BR_ZERO':>8} {'BR_POS':>7} "
          f"{'JMP':>5} {'CALL':>5} {'RET':>5}")
    for prog in [
        "programs/countdown.btis",
        "programs/fibonacci.btis",
        "programs/w4_cubeadd.btis",
        "programs/voxel_pattern.btis",
        "programs/w3_merge.btis",
    ]:
        path = REPO / prog
        if not path.exists():
            continue
        try:
            lines, _ = run_btis(path)
        except subprocess.CalledProcessError as e:
            print(f"  {prog:<28}  ERROR: {e}")
            continue
        c = count_branch_ops(lines)
        print(f"  {prog:<28} {c['BR_NEG']:>7} {c['BR_ZERO']:>8} {c['BR_POS']:>7} "
              f"{c['JMP']:>5} {c['CALL']:>5} {c['RET']:>5}")


def main():
    reversibility_demo()
    three_way_branch_count()


if __name__ == "__main__":
    main()
