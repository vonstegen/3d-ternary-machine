//! BT-IS CLI driver: assemble a `.btis` source file and execute it.

use std::env;
use std::fs;
use std::process::ExitCode;

use btis::asm::assemble;
use btis::trace::Tracer;
use btis::vm::VM;

fn main() -> ExitCode {
    let args: Vec<String> = env::args().collect();
    let trace = args.iter().any(|a| a == "--trace");
    let positional: Vec<&String> = args.iter().skip(1).filter(|a| *a != "--trace").collect();
    if positional.is_empty() {
        eprintln!("usage: btis <source.btis> [--trace]");
        return ExitCode::from(2);
    }
    let src_path = positional[0];
    let src = match fs::read_to_string(src_path) {
        Ok(s) => s,
        Err(e) => { eprintln!("read error: {e}"); return ExitCode::from(1); }
    };
    let program = match assemble(&src) {
        Ok(p) => p,
        Err(e) => { eprintln!("assemble error: {e}"); return ExitCode::from(1); }
    };
    let mut vm = VM::new(program);
    if trace {
        let mut tr = Tracer::new(&mut vm);
        if let Err(e) = tr.run() {
            eprintln!("vm error: {e}");
            return ExitCode::from(1);
        }
        eprintln!("-- trace ({} steps) --", tr.trace.len());
        for s in &tr.trace {
            eprintln!("  IP={:>3} op={:>3} arg={:>2} C={} F={}",
                s.ip, s.opcode, s.arg, s.C, s.F);
        }
    } else if let Err(e) = vm.run() {
        eprintln!("vm error: {e}");
        return ExitCode::from(1);
    }

    // Emit output
    for e in &vm.output {
        match e {
            btis::vm::Emit::Int(i) => println!("INT {i}"),
            btis::vm::Emit::Cube(c) => println!("CUBE {c}"),
        }
    }
    ExitCode::SUCCESS
}
