// In-process benchmark for BT-IS VM.
//
// Runs the equivalent of programs/bench_rot.btis directly in Rust
// without the CLI / parse / exec overhead. Measures pure VM throughput.

use std::time::Instant;
use btis::asm::assemble;
use btis::vm::{VM, Instr};
use btis::isa::opcodes;

fn rot_z_90_program() -> Vec<Instr> {
    use opcodes::*;
    vec![
        Instr { opcode: LOAD_AXIS, arg: 0, target: 0 },  // +X
        Instr { opcode: ROT_Z_90,  arg: 0, target: 0 },
        Instr { opcode: ROT_Z_90,  arg: 0, target: 0 },
        Instr { opcode: ROT_Z_90,  arg: 0, target: 0 },
        Instr { opcode: ROT_Z_90,  arg: 0, target: 0 },
        Instr { opcode: HALT,      arg: 0, target: 0 },
    ]
}

fn main() {
    let n: u64 = std::env::args()
        .nth(1)
        .and_then(|s| s.parse().ok())
        .unwrap_or(100_000);

    let program = rot_z_90_program();
    let start = Instant::now();
    for _ in 0..n {
        let mut vm = VM::new(program.clone());
        vm.run().unwrap();
    }
    let elapsed = start.elapsed();
    let total_instrs = n * 6;
    let ns = elapsed.as_nanos() as u64;
    let per_run_us = ns / n / 1000;
    let ips = total_instrs * 1_000_000_000 / ns.max(1);

    println!("BT-IS in-process benchmark");
    println!("  iterations:  {}", n);
    println!("  per run:     {} us", per_run_us);
    println!("  total instr: {}", total_instrs);
    println!("  throughput:  {} instructions/sec", ips);

    // Sanity check the assemble path works too
    let src = std::fs::read_to_string("programs/bench_rot.btis").unwrap_or_default();
    if !src.is_empty() {
        let p = assemble(&src).expect("asm");
        let mut vm = VM::new(p);
        vm.run().unwrap();
    }
}
