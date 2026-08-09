//! BT-IS virtual machine.
//!
//! # State
//!
//! - `C`        : cube (the program's cursor / data)
//! - `F`        : flag cube (`(gt, eq, lt)` from the last `CMP`)
//! - `R[0..7]`  : 8 rotor registers holding `Perm` permutations
//! - `IP`       : instruction pointer
//! - `stack`    : return IPs for `CALL`/`RET`
//! - `mem`      : `HashMap<Cube, Cube>` keyed by *full* cube coordinate
//! - `undo_log` : per-step undo entries, applied in reverse by
//!                [`VM::undo_all`]. A BT-IS program is a trajectory
//!                through the 27-cube, and trajectories are invertible.
//!
//! # Reversibility
//!
//! Each step records the prior value(s) it overwrites. `undo_all()`
//! pops those entries in reverse, recovering `(C, F, R[*], mem)` to
//! their pre-run state. `output` is *not* undone (it's a side effect).

use crate::cube::Cube;
use crate::isa::{opcodes, ROTOR_COUNT, DATA_REG_COUNT};
use crate::symmetry::Perm;
use std::collections::HashMap;

#[derive(Clone, Debug)]
pub struct Instr {
    pub opcode: u8,
    pub arg: i8,
    pub target: usize,
}

#[derive(Debug, Clone, PartialEq)]
pub enum Emit {
    Int(i8),
    Cube(Cube),
}

 #[derive(Clone, Debug)]
#[allow(non_snake_case)]
 pub struct TraceStep {
    pub ip: usize,
    pub opcode: u8,
    pub arg: i8,
    pub C: Cube,
    pub F: Cube,
}
 #[derive(Clone, Debug)]
#[allow(non_snake_case)]
 pub struct Snapshot {
    pub C: Cube,
    pub F: Cube,
    pub R: [Perm; ROTOR_COUNT],
    pub D: [Cube; DATA_REG_COUNT],
    pub IP: usize,
    pub stack: Vec<usize>,
    pub mem: HashMap<Cube, Cube>,
    pub output_len: usize,
    pub steps: usize,
}

#[derive(Debug)]
pub enum VMError {
    StepLimit(usize),
    BadOp(u8),
    BadAxis(i8),
    BadRegister(u8),
    EmptyStack,
}

impl std::fmt::Display for VMError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            VMError::StepLimit(n)    => write!(f, "step limit {n} exceeded"),
            VMError::BadOp(o)        => write!(f, "unknown opcode {o}"),
            VMError::BadAxis(a)      => write!(f, "bad axis code {a}"),
            VMError::BadRegister(r)  => write!(f, "bad register index {r}"),
            VMError::EmptyStack      => write!(f, "RET with empty stack"),
        }
    }
}

impl std::error::Error for VMError {}

/// One reversible mutation: describes how to undo one step.
#[derive(Debug, Clone)]
enum Undo {
    /// Snapshot of control-flow state at the start of a step.
    /// Pushed at the start of every step so that `undo_all()`
    /// can restore the VM to a fully-pre-run state, including
    /// `IP`, `steps`, and `halted`.
    BeginStep {
        halted: bool,
        ip: usize,
        steps: usize,
    },
    RestoreC(Cube),
    RestoreF(Cube),
    RestoreR(usize, Perm),
    RestoreD(usize, Cube),
    MemInsert { addr: Cube, prev: Option<Cube> },
    RestoreStackLen(usize),
}

 #[derive(Debug)]
#[allow(non_snake_case)]
 pub struct VM {
    pub program: Vec<Instr>,
    pub C: Cube,
    pub F: Cube,
    pub R: [Perm; ROTOR_COUNT],
    pub D: [Cube; DATA_REG_COUNT],
    pub IP: usize,
    pub stack: Vec<usize>,
    pub mem: HashMap<Cube, Cube>,
    pub output: Vec<Emit>,
    pub steps: usize,
    pub max_steps: usize,
    pub halted: bool,
    pub trace_enabled: bool,
    pub trace: Vec<TraceStep>,
    undo_log: Vec<Undo>,
}

impl Default for VM {
    fn default() -> Self { Self::new(Vec::new()) }
}

impl VM {
    pub fn new(program: Vec<Instr>) -> Self {
        VM {
            program,
            C: Cube::CENTER,
            F: Cube::CENTER,
            R: [Perm::identity(); ROTOR_COUNT],
            D: [Cube::CENTER; DATA_REG_COUNT],
            IP: 0,
            stack: vec![],
            mem: HashMap::new(),
            output: vec![],
            steps: 0,
            max_steps: 10_000_000,
            halted: false,
            trace_enabled: false,
            trace: vec![],
            undo_log: vec![],
        }
    }

    pub fn snapshot(&self) -> Snapshot {
        Snapshot {
            C: self.C,
            F: self.F,
            R: self.R,
            D: self.D,
            IP: self.IP,
            stack: self.stack.clone(),
            mem: self.mem.clone(),
            output_len: self.output.len(),
            steps: self.steps,
        }
    }

    /// Undo every recorded step. Returns the number undone.
    ///
    /// After `undo_all`, the VM is restored to the pre-run
    /// state, including `IP`, `steps`, and `halted`. The
    /// `output` vector is intentionally *not* cleared (it is
    /// a side-effect log; clearing it would hide prior runs).
    ///
    /// Note: this is a *complete* revert, not the older
    /// "data-only" restore. To re-run a program after
    /// `undo_all`, just call `run()` again; the VM starts
    /// at `IP=0` with `steps=0` and `halted=false`.
    pub fn undo_all(&mut self) -> usize {
        let n = self.undo_log.len();
        while let Some(u) = self.undo_log.pop() {
            self.apply_undo(u);
        }
        n
    }

    fn apply_undo(&mut self, u: Undo) {
        match u {
            Undo::BeginStep { halted, ip, steps } => {
                self.halted = halted;
                self.IP = ip;
                self.steps = steps;
            }
            Undo::RestoreC(c)    => self.C = c,
            Undo::RestoreF(f)    => self.F = f,
            Undo::RestoreD(i, c) => self.D[i] = c,
            Undo::RestoreR(i, p) => self.R[i] = p,
            Undo::MemInsert { addr, prev } => match prev {
                Some(p) => { self.mem.insert(addr, p); }
                None    => { self.mem.remove(&addr); }
            },
            Undo::RestoreStackLen(n) => self.stack.truncate(n),
        }
    }

    pub fn step(&mut self) -> Result<(), VMError> {
        if self.halted { return Ok(()); }
        if self.IP >= self.program.len() { self.halted = true; return Ok(()); }
        if self.steps >= self.max_steps {
            return Err(VMError::StepLimit(self.max_steps));
        }
        // Record pre-step control state so undo_all() can
        // restore IP, steps, and halted.
        self.push_undo(Undo::BeginStep {
            halted: self.halted,
            ip: self.IP,
            steps: self.steps,
        });
        self.steps += 1;
        let instr = self.program[self.IP].clone();
        if self.trace_enabled {
            self.trace.push(TraceStep {
                ip: self.IP,
                opcode: instr.opcode,
                arg: instr.arg,
                C: self.C,
                F: self.F,
            });
        }
        let mut next_ip = self.IP + 1;
        self.exec(instr, &mut next_ip)?;
        self.IP = next_ip;
        Ok(())
    }

    pub fn run(&mut self) -> Result<(), VMError> {
        while !self.halted { self.step()?; }
        Ok(())
    }

    fn push_undo(&mut self, u: Undo) { self.undo_log.push(u); }

    fn exec(&mut self, instr: Instr, next_ip: &mut usize) -> Result<(), VMError> {
        use opcodes::*;
        match instr.opcode {
            NOP => {}

            HALT => { self.halted = true; }

            LOADC => {
                debug_assert!(instr.arg >= -1 && instr.arg <= 1);
                self.push_undo(Undo::RestoreC(self.C));
                self.C = Cube::new(instr.arg, instr.arg, instr.arg);
            }

            LOAD_AXIS => {
                self.push_undo(Undo::RestoreC(self.C));
                self.C = match instr.arg {
                    0 => Cube::new( 1, 0, 0),
                    1 => Cube::new(-1, 0, 0),
                    2 => Cube::new( 0, 1, 0),
                    3 => Cube::new( 0,-1, 0),
                    4 => Cube::new( 0, 0, 1),
                    5 => Cube::new( 0, 0,-1),
                    _ => return Err(VMError::BadAxis(instr.arg)),
                };
            }

            OUTI => { self.output.push(Emit::Int(self.C.x())); }
            OUTV => { self.output.push(Emit::Cube(self.C)); }

            MOV_R => {
                let dst = (instr.arg as usize) & 0x7;
                let src = (instr.target as usize) & 0x7;
                if dst >= ROTOR_COUNT || src >= ROTOR_COUNT {
                    return Err(VMError::BadRegister(dst as u8));
                }
                self.push_undo(Undo::RestoreR(dst, self.R[dst]));
                self.R[dst] = self.R[src];
            }

            LOAD_R => {
                let idx = (instr.arg as usize) & 0x7;
                if idx >= ROTOR_COUNT {
                    return Err(VMError::BadRegister(idx as u8));
                }
                self.push_undo(Undo::RestoreR(idx, self.R[idx]));
                self.R[idx] = Perm::identity();
            }
            MOV_CD => {
                let idx = (instr.arg as usize) & 0x3;
                if idx >= DATA_REG_COUNT {
                    return Err(VMError::BadRegister(idx as u8));
                }
                self.push_undo(Undo::RestoreD(idx, self.D[idx]));
                self.D[idx] = self.C;
            }
            MOV_DC => {
                let idx = (instr.arg as usize) & 0x3;
                if idx >= DATA_REG_COUNT {
                    return Err(VMError::BadRegister(idx as u8));
                }
                self.push_undo(Undo::RestoreC(self.C));
                self.C = self.D[idx];
            }
            STORE_D => {
                let idx = (instr.arg as usize) & 0x3;
                if idx >= DATA_REG_COUNT {
                    return Err(VMError::BadRegister(idx as u8));
                }
                let addr = self.C;
                let prev = self.mem.get(&addr).copied();
                let val = self.D[idx];
                self.push_undo(Undo::MemInsert { addr, prev });
                self.mem.insert(addr, val);
            }
            LOAD_D => {
                let idx = (instr.arg as usize) & 0x3;
                if idx >= DATA_REG_COUNT {
                    return Err(VMError::BadRegister(idx as u8));
                }
                let addr = self.C;
                self.push_undo(Undo::RestoreD(idx, self.D[idx]));
                self.D[idx] = self.mem.get(&addr).copied().unwrap_or(Cube::CENTER);
            }

            op if rotation_for(op).is_some() => {
                self.push_undo(Undo::RestoreC(self.C));
                let p = rotation_for(op).unwrap();
                self.C = p.apply(self.C);
            }

            APPLY_R => {
                let idx = (instr.arg as usize) & 0x7;
                if idx >= ROTOR_COUNT {
                    return Err(VMError::BadRegister(idx as u8));
                }
                self.push_undo(Undo::RestoreC(self.C));
                self.C = self.R[idx].apply(self.C);
            }
            // ROT_*_R: R[target] := named_rotation.then(R[target])
            // arg is unused; target selects the rotor register.
            // We post-compose onto R[target] (i.e., apply rotation
            // AFTER the existing permutation).
            op if matches_rotor_op(op) => {
                let idx = (instr.arg as usize) & 0x7;
                if idx >= ROTOR_COUNT {
                    return Err(VMError::BadRegister(idx as u8));
                }
                let perm = rotation_for_rotor_op(op).unwrap();
                self.push_undo(Undo::RestoreR(idx, self.R[idx]));
                // R[idx] := perm.then(R[idx])  (apply perm first, then existing)
                self.R[idx] = perm.then(self.R[idx]);
            }

            REFLECT_X | REFLECT_Y | REFLECT_Z | NEG => {
                use crate::symmetry::{
                    NEG as NEG_P, REFLECT_X as REFL_X,
                    REFLECT_Y as REFL_Y, REFLECT_Z as REFL_Z,
                };
                self.push_undo(Undo::RestoreC(self.C));
                self.C = match instr.opcode {
                    REFLECT_X => REFL_X.apply(self.C),
                    REFLECT_Y => REFL_Y.apply(self.C),
                    REFLECT_Z => REFL_Z.apply(self.C),
                    NEG       => NEG_P.apply(self.C),
                    _ => unreachable!(),
                };
            }

            COMPOSE_R => {
                let dst = (instr.arg as usize) & 0x7;
                let src = (instr.target as usize) & 0x7;
                if dst >= ROTOR_COUNT || src >= ROTOR_COUNT {
                    return Err(VMError::BadRegister(dst as u8));
                }
                self.push_undo(Undo::RestoreR(dst, self.R[dst]));
                self.R[dst] = self.R[dst].then(self.R[src]);
            }

            INVERSE_R => {
                let idx = (instr.arg as usize) & 0x7;
                if idx >= ROTOR_COUNT {
                    return Err(VMError::BadRegister(idx as u8));
                }
                self.push_undo(Undo::RestoreR(idx, self.R[idx]));
                self.R[idx] = self.R[idx].inverse();
            }

            IADD => {
                self.push_undo(Undo::RestoreC(self.C));
                let s = self.C.x() as i16 + instr.arg as i16;
                self.C = Cube::new(clamp3(s as i8), self.C.y(), self.C.z());
            }
            ISUB => {
                self.push_undo(Undo::RestoreC(self.C));
                let s = self.C.x() as i16 - instr.arg as i16;
                self.C = Cube::new(clamp3(s as i8), self.C.y(), self.C.z());
            }
            IMUL => {
                self.push_undo(Undo::RestoreC(self.C));
                let s = self.C.x() as i16 * instr.arg as i16;
                self.C = Cube::new(clamp3(s as i8), self.C.y(), self.C.z());
            }
            CYCLE_X => {
                self.push_undo(Undo::RestoreC(self.C));
                let nx = cycle3(self.C.x());
                self.C = Cube::new(nx, self.C.y(), self.C.z());
            }
            CYCLE_Y => {
                self.push_undo(Undo::RestoreC(self.C));
                let ny = cycle3(self.C.y());
                self.C = Cube::new(self.C.x(), ny, self.C.z());
            }
            CYCLE_Z => {
                self.push_undo(Undo::RestoreC(self.C));
                let nz = cycle3(self.C.z());
                self.C = Cube::new(self.C.x(), self.C.y(), nz);
            }
            CUBE_ADD => {
                // C := C + mem[C]  (full 27-state balanced-ternary addition
                // with carry through x, y, z). If mem[C] is empty, treat
                // as adding 0 (no-op).
                self.push_undo(Undo::RestoreC(self.C));
                let other = self.mem.get(&self.C).copied().unwrap_or(Cube::CENTER);
                self.C = cube_add(self.C, other);
            }

            CMP => {
                self.push_undo(Undo::RestoreF(self.F));
                let d = self.C.x() as i16 - instr.arg as i16;
                let f = if d > 0 { 1 } else if d < 0 { -1 } else { 0 };
                self.F = Cube::new(f, 0, 0);
            }

            BR_NEG  => { if self.F.x() <  0 { *next_ip = instr.target; } }
            BR_ZERO => { if self.F.x() == 0 { *next_ip = instr.target; } }
            BR_POS  => { if self.F.x() >  0 { *next_ip = instr.target; } }
            JMP     => { *next_ip = instr.target; }
            BR_AXIS => {
                let v = match instr.arg {
                    0 => self.C.x(),
                    1 => self.C.y(),
                    2 => self.C.z(),
                    _ => return Err(VMError::BadAxis(instr.arg)),
                };
                if v > 0 { *next_ip = instr.target; }
            }
            CALL => {
                let prev_ip = self.IP + 1;
                let prev_stack_len = self.stack.len();
                self.stack.push(prev_ip);
                self.push_undo(Undo::RestoreStackLen(prev_stack_len));
                *next_ip = instr.target;
            }
            RET => {
                if let Some(ret_ip) = self.stack.pop() {
                    let prev_stack_len = self.stack.len() + 1;  // before pop
                    self.push_undo(Undo::RestoreStackLen(prev_stack_len));
                    *next_ip = ret_ip;
                } else {
                    return Err(VMError::EmptyStack);
                }
            }

            STORE => {
                let addr = Cube::new(instr.arg, instr.arg, instr.arg);
                let prev = self.mem.get(&addr).copied();
                let val = self.C;
                self.push_undo(Undo::MemInsert { addr, prev });
                self.mem.insert(addr, val);
            }
            LOAD => {
                let addr = Cube::new(instr.arg, instr.arg, instr.arg);
                self.push_undo(Undo::RestoreC(self.C));
                let v = self.mem.get(&addr).copied().unwrap_or(Cube::CENTER);
                self.C = v;
            }
            STORE_C => {
                let addr = self.C;
                let prev = self.mem.get(&addr).copied();
                let val = self.C;
                self.push_undo(Undo::MemInsert { addr, prev });
                self.mem.insert(addr, val);
            }
            LOAD_C => {
                let prev_c = self.C;
                let addr = self.C;
                self.push_undo(Undo::RestoreC(prev_c));
                let v = self.mem.get(&addr).copied().unwrap_or(Cube::CENTER);
                self.C = v;
            }

            o => return Err(VMError::BadOp(o)),
        }
        Ok(())
    }
}

#[inline]
fn clamp3(v: i8) -> i8 {
    if v < -1 { -1 } else if v > 1 { 1 } else { v }
}

/// Cycle a coordinate in {-1, 0, +1} forward by one: -1->0->1->-1.
#[inline]
fn cycle3(v: i8) -> i8 {
    match v {
        -1 => 0,
         0 => 1,
         1 => -1,
         _ => v,
    }
}

/// Full 27-state addition: C := a + b coordinate-wise with carry
/// through (x, y, z). Each coordinate lives in {-1, 0, +1} and carries
/// overflow to the next.
fn cube_add(a: Cube, b: Cube) -> Cube {
    // Sum x + b.x in balanced ternary, producing (digit, carry).
    let sx = (a.x() as i16) + (b.x() as i16);
    let (nx, cx) = balanced_trit(sx);
    // y += b.y + carry from x
    let sy = (a.y() as i16) + (b.y() as i16) + (cx as i16);
    let (ny, cy) = balanced_trit(sy);
    // z += b.z + carry from y
    let sz = (a.z() as i16) + (b.z() as i16) + (cy as i16);
    let (nz, cz) = balanced_trit(sz);
    // Overflow past z is dropped (27-state arithmetic).
    let _ = cz;
    Cube::new(nx, ny, nz)
}

/// Decompose an integer sum in {-3, ..., 3} into a balanced ternary
/// digit (in {-1, 0, +1}) and a carry (in {-1, 0, +1}).
///
/// Truth table for sum -> (digit, carry):
///   3 -> (0, 1)
///   2 -> (-1, 1)
///   1 -> (1, 0)
///   0 -> (0, 0)
///  -1 -> (-1, 0)
///  -2 -> (1, -1)
///  -3 -> (0, -1)
fn balanced_trit(sum: i16) -> (i8, i8) {
    match sum {
        3  => ( 0,  1),
        2  => (-1,  1),
        1  => ( 1,  0),
        0  => ( 0,  0),
        -1 => (-1,  0),
        -2 => ( 1, -1),
        -3 => ( 0, -1),
        _  => panic!("balanced_trit: out-of-range sum {}", sum),
    }
}

fn matches_rotor_op(op: u8) -> bool {
    matches!(op,
        opcodes::ROT_Z_90_R  | opcodes::ROT_Z_180_R |
        opcodes::ROT_Z_270_R | opcodes::ROT_X_90_R  |
        opcodes::ROT_X_180_R | opcodes::ROT_X_270_R |
        opcodes::ROT_Y_90_R  | opcodes::ROT_Y_180_R |
        opcodes::ROT_Y_270_R | opcodes::REFLECT_X_R |
        opcodes::REFLECT_Y_R | opcodes::REFLECT_Z_R |
        opcodes::NEG_R
    )
}

fn rotation_for_rotor_op(op: u8) -> Option<Perm> {
    use opcodes::*;
    use crate::symmetry::{
        NEG as NEG_P, REFLECT_X as REFL_X, REFLECT_Y as REFL_Y, REFLECT_Z as REFL_Z,
        ROT_X_90 as RX90, ROT_X_180 as RX180, ROT_X_270 as RX270,
        ROT_Y_90 as RY90, ROT_Y_180 as RY180, ROT_Y_270 as RY270,
        ROT_Z_90 as RZ90, ROT_Z_180 as RZ180, ROT_Z_270 as RZ270,
    };
    match op {
        ROT_Z_90_R  => Some(*RZ90),
        ROT_Z_180_R => Some(*RZ180),
        ROT_Z_270_R => Some(*RZ270),
        ROT_X_90_R  => Some(*RX90),
        ROT_X_180_R => Some(*RX180),
        ROT_X_270_R => Some(*RX270),
        ROT_Y_90_R  => Some(*RY90),
        ROT_Y_180_R => Some(*RY180),
        ROT_Y_270_R => Some(*RY270),
        REFLECT_X_R => Some(*REFL_X),
        REFLECT_Y_R => Some(*REFL_Y),
        REFLECT_Z_R => Some(*REFL_Z),
        NEG_R       => Some(*NEG_P),
        _ => None,
    }
}

fn rotation_for(op: u8) -> Option<Perm> {
    use opcodes::*;
    use crate::symmetry::{
        ROT_X_90 as RX90, ROT_X_180 as RX180, ROT_X_270 as RX270,
        ROT_Y_90 as RY90, ROT_Y_180 as RY180, ROT_Y_270 as RY270,
        ROT_Z_90 as RZ90, ROT_Z_180 as RZ180, ROT_Z_270 as RZ270,
    };
    match op {
        ROT_Z_90  => Some(*RZ90),
        ROT_Z_180 => Some(*RZ180),
        ROT_Z_270 => Some(*RZ270),
        ROT_X_90  => Some(*RX90),
        ROT_X_180 => Some(*RX180),
        ROT_X_270 => Some(*RX270),
        ROT_Y_90  => Some(*RY90),
        ROT_Y_180 => Some(*RY180),
        ROT_Y_270 => Some(*RY270),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn prog(p: Vec<Instr>) -> VM { VM::new(p) }

    #[test]
    fn loadc_and_outi() {
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
            Instr { opcode: opcodes::OUTI,  arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT,  arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Int(1)]);
    }

    #[test]
    fn rotation_through_z_axis() {
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOAD_AXIS, arg: 0, target: 0 },
            Instr { opcode: opcodes::ROT_Z_90, arg: 0, target: 0 },
            Instr { opcode: opcodes::OUTV, arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT,  arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Cube(Cube::new(0, 1, 0))]);
    }

    #[test]
    fn four_rotations_idempotent() {
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
            Instr { opcode: opcodes::ROT_Z_90, arg: 0, target: 0 },
            Instr { opcode: opcodes::ROT_Z_90, arg: 0, target: 0 },
            Instr { opcode: opcodes::ROT_Z_90, arg: 0, target: 0 },
            Instr { opcode: opcodes::ROT_Z_90, arg: 0, target: 0 },
            Instr { opcode: opcodes::OUTV, arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT,  arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Cube(Cube::new(1, 1, 1))]);
    }

    #[test]
    fn cmp_branch_zero() {
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOADC, arg: 0,  target: 0 },
            Instr { opcode: opcodes::CMP,    arg: 0,  target: 0 },
            Instr { opcode: opcodes::BR_ZERO, arg: 0, target: 6 },
            Instr { opcode: opcodes::LOADC, arg: -1, target: 0 },
            Instr { opcode: opcodes::OUTV,   arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT,   arg: 0, target: 0 },
            Instr { opcode: opcodes::LOADC, arg: 1,  target: 0 },
            Instr { opcode: opcodes::OUTV,   arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT,   arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Cube(Cube::new(1, 1, 1))]);
    }

    #[test]
    fn iadd_balanced() {
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
            Instr { opcode: opcodes::IADD, arg: 1, target: 0 },
            Instr { opcode: opcodes::OUTI, arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT, arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Int(1)]);
    }

    #[test]
    fn store_load() {
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOADC, arg: -1, target: 0 },
            Instr { opcode: opcodes::STORE, arg: 0,  target: 0 },
            Instr { opcode: opcodes::LOADC, arg: 1,  target: 0 },
            Instr { opcode: opcodes::LOAD,  arg: 0,  target: 0 },
            Instr { opcode: opcodes::OUTI,  arg: 0,  target: 0 },
            Instr { opcode: opcodes::HALT,  arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Int(-1)]);
    }

    #[test]
    fn undo_restores_initial_state() {
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
            Instr { opcode: opcodes::ROT_Z_90, arg: 0, target: 0 },
            Instr { opcode: opcodes::ROT_X_90, arg: 0, target: 0 },
            Instr { opcode: opcodes::NEG, arg: 0, target: 0 },
            Instr { opcode: opcodes::IADD, arg: 1, target: 0 },
            Instr { opcode: opcodes::STORE, arg: 0, target: 0 },
        ]);
        let snap = vm.snapshot();
        vm.run().unwrap();
        assert_ne!(vm.C, snap.C);
        let n_undo = vm.undo_all();
        // 6 instructions, each pushes 1 BeginStep + 1-2 data entries
        // (the data mutation can be absent for ops like NOP or rotations
        // that touch R, not C). For this program, the 6 ops push
        assert_eq!(n_undo, 12, "6 BeginStep + 6 data-mutation undo entries");
        assert_eq!(vm.C, snap.C, "C must be restored");
        assert!(vm.mem.is_empty(), "STORE undone");
        // Verify the new behavior: IP, steps, halted are all restored.
        assert_eq!(vm.IP, snap.IP, "IP must be restored to 0");
        assert_eq!(vm.steps, snap.steps, "steps must be restored to 0");
    }

    #[test]
    fn undo_all_allows_rerun() {
        // After undo_all, run() should restart from IP=0 with
        // steps=0 and halted=false, producing the same output
        // as the first run.
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
            Instr { opcode: opcodes::OUTV,  arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT,   arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Cube(Cube::new(1, 1, 1))]);
        // undo_all() to make run() restart from IP=0.
        let n = vm.undo_all();
        assert!(n > 0);
        assert_eq!(vm.IP, 0, "IP restored to 0");
        assert_eq!(vm.steps, 0, "steps restored to 0");
        assert!(!vm.halted, "halted restored to false");
        // Re-run: same output, but the log accumulates.
        vm.run().unwrap();
        assert_eq!(vm.output, vec![
            Emit::Cube(Cube::new(1, 1, 1)),
            Emit::Cube(Cube::new(1, 1, 1)),
        ]);
    }

    #[test]
    fn store_load_c_uses_c_as_address() {
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
            Instr { opcode: opcodes::STORE_C, arg: 0, target: 0 },
            Instr { opcode: opcodes::LOADC, arg: -1, target: 0 },
            Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
            Instr { opcode: opcodes::LOAD_C, arg: 0, target: 0 },
            Instr { opcode: opcodes::OUTV, arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT, arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Cube(Cube::new(1, 1, 1))]);
    }

    #[test]
    fn call_ret_round_trip() {
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
            Instr { opcode: opcodes::CALL,   arg: 0, target: 3 },
            Instr { opcode: opcodes::HALT,   arg: 0, target: 0 },
            Instr { opcode: opcodes::OUTV,   arg: 0, target: 0 },
            Instr { opcode: opcodes::RET,    arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Cube(Cube::new(1, 1, 1))]);
        assert!(vm.halted);
    }

    #[test]
    fn rotor_register_file() {
        // Build R0 = ROT_Z_90 (apply R0 to C and verify), then
        // compose R1 = R0 * R0 = ROT_Z_180 via COMPOSE_R. Use
        // LOAD_R to reset both slots first.
        let mut vm = prog(vec![
            // We can't directly assign a Perm to a rotor; only compose
            // from existing identity. Verify the file by applying R0
            // (identity) to C, then setting R0 via apply, but APPLY_R
            // doesn't mutate R0. So the test exercises:
            //  - LOAD_R resets to identity
            //  - COMPOSE_R composes identity * identity = identity
            //  - apply_r on identity leaves C unchanged
            Instr { opcode: opcodes::LOAD_R, arg: 0, target: 0 },
            Instr { opcode: opcodes::LOAD_R, arg: 1, target: 0 },
            Instr { opcode: opcodes::COMPOSE_R, arg: 0, target: 1 }, // R0 := R0 * R1 = id
            Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
            Instr { opcode: opcodes::APPLY_R, arg: 0, target: 0 },    // C := R0(C) = C
            Instr { opcode: opcodes::OUTV, arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT, arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Cube(Cube::new(1, 1, 1))]);
    }

    #[test]
    fn cycle_x_three_steps_returns_to_start() {
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
            Instr { opcode: opcodes::CYCLE_X, arg: 0, target: 0 },  // 1 -> -1
            Instr { opcode: opcodes::CYCLE_X, arg: 0, target: 0 },  // -1 -> 0
            Instr { opcode: opcodes::CYCLE_X, arg: 0, target: 0 },  // 0 -> 1
            Instr { opcode: opcodes::OUTV, arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT, arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Cube(Cube::new(1, 1, 1))]);
    }

    #[test]
    fn cube_add_basic() {
        // Set mem[(1,0,0)] = (1,0,0), then C := (1,0,0); CUBE_ADD gives
        // (1,0,0) + (1,0,0) = (2,0,0) in arithmetic, which is balanced-
        // ternary (-1, +1, 0) with carry. Cube arithmetic drops the
        // top carry, so the result is (-1, +1, 0).
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOAD_AXIS, arg: 0, target: 0 },   // C = (1,0,0)
            Instr { opcode: opcodes::STORE_C, arg: 0, target: 0 },     // mem[(1,0,0)] := (1,0,0)
            Instr { opcode: opcodes::LOAD_AXIS, arg: 0, target: 0 },   // C = (1,0,0)
            Instr { opcode: opcodes::CUBE_ADD, arg: 0, target: 0 },    // (1,0,0)+(1,0,0)
            Instr { opcode: opcodes::OUTV, arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT, arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Cube(Cube::new(-1, 1, 0))]);
    }

    #[test]
    fn cube_add_zero_is_identity() {
        // C = (1,1,1); mem[(1,1,1)] empty (no add); CUBE_ADD should add
        // (0,0,0) which is identity.
        let mut vm = prog(vec![
            Instr { opcode: opcodes::LOADC, arg: 1, target: 0 },
            Instr { opcode: opcodes::STORE_C, arg: 0, target: 0 },   // sets mem[(1,1,1)]
            Instr { opcode: opcodes::LOADC, arg: 0, target: 0 },     // C := (0,0,0)
            Instr { opcode: opcodes::CUBE_ADD, arg: 0, target: 0 },   // 0 + 0 = 0
            Instr { opcode: opcodes::OUTV, arg: 0, target: 0 },
            Instr { opcode: opcodes::HALT, arg: 0, target: 0 },
        ]);
        vm.run().unwrap();
        assert_eq!(vm.output, vec![Emit::Cube(Cube::new(0, 0, 0))]);
    }
}
