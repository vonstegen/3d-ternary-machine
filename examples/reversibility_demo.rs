
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
