use btis::asm::assemble;

fn main() {
    let src = "compose_r 0 1\n";
    let program = assemble(src).unwrap();
    for (i, instr) in program.iter().enumerate() {
        println!("Instr {}: opcode={} arg={} target={}", i, instr.opcode, instr.arg, instr.target);
    }
}
