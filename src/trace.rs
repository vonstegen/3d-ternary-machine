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

    pub fn run(&mut self) -> Result<(), crate::vm::VMError> {
        loop {
            let ip = self.vm.IP;
            let instr = self.vm.program.get(ip).cloned();
            let step = Step {
                ip,
                opcode: instr.as_ref().map(|i| i.opcode).unwrap_or(0),
                arg:    instr.as_ref().map(|i| i.arg).unwrap_or(0),
                C: self.vm.C,
                F: self.vm.F,
            };
            self.trace.push(step);
            if self.vm.halted { return Ok(()); }
            self.vm.step()?;
            if self.vm.IP >= self.vm.program.len() { return Ok(()); }
        }
    }
}
