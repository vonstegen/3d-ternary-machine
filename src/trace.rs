//! Execution trace: per-step snapshot for debugging and visualization.

use crate::cube::Cube;
use crate::vm::VM;

#[derive(Debug, Clone)]
#[allow(non_snake_case)]
pub struct Step {
    pub ip: usize,
    pub opcode: u8,
    pub arg: i8,
    pub C: Cube,
    pub F: Cube,
}

pub struct Tracer<'a> {
    vm: &'a mut VM,
    pub trace: Vec<Step>,
}

impl<'a> Tracer<'a> {
    pub fn new(vm: &'a mut VM) -> Self {
        Tracer { vm, trace: vec![] }
    }

    /// Run the VM to completion, recording one Step per executed
    /// instruction. The trace length equals the number of
    /// instructions executed (HALT counts as one step).
    pub fn run(&mut self) -> Result<(), crate::vm::VMError> {
        loop {
            // Stop BEFORE recording if the VM is already halted
            // (avoids a post-HALT sentinel entry with opcode=0).
            if self.vm.halted { return Ok(()); }
            if self.vm.IP >= self.vm.program.len() { return Ok(()); }

            let ip = self.vm.IP;
            let instr = self.vm.program[ip].clone();
            self.trace.push(Step {
                ip,
                opcode: instr.opcode,
                arg: instr.arg,
                C: self.vm.C,
                F: self.vm.F,
            });
            self.vm.step()?;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::isa::opcodes;
    use crate::vm::{Instr, VM};

    #[test]
    fn trace_length_matches_instructions() {
        // A program of 3 instructions (LOADC, OUTV, HALT) should
        // produce exactly 3 trace steps, not 4. The pre-fix
        // Tracer pushed a post-HALT sentinel.
        let mut vm = VM::new(vec![
            Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
            Instr { opcode: opcodes::OUTV,  arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT,   arg: 0, target: 0 },
        ]);
        let mut tr = Tracer::new(&mut vm);
        tr.run().unwrap();
        assert_eq!(tr.trace.len(), 3, "trace should have one step per instruction");
        assert_eq!(tr.trace[0].ip, 0);
        assert_eq!(tr.trace[0].opcode, opcodes::LOADC);
        assert_eq!(tr.trace[1].ip, 1);
        assert_eq!(tr.trace[1].opcode, opcodes::OUTV);
        assert_eq!(tr.trace[2].ip, 2);
        assert_eq!(tr.trace[2].opcode, opcodes::HALT);
    }
}
