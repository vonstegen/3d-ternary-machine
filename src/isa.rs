//! BT-IS instruction set.
//!
//! Every opcode is a geometric verb acting on cube state. Opcodes are
//! encoded as small integers (`u8`) and dispatched in O(1).
//!
//! ## Opcode map
//!
//! ```text
//!   0..32   : data movement, I/O, register ops
//!  32..56   : rotations applied to C
//!  56..64   : reflections / inversion / rotor composition
//!  64..96   : arithmetic on the ternary scalar encoded in C.x
//!  96..128  : comparison, three-way branching
//! 128..160  : memory (cube-addressed)
//! 192..     : meta (HALT = 192)
//! ```
//!
//! ## Register file
//!
//! - `C`       : cube (the program's cursor / data)
//! - `F`       : cube (last comparison sign, as `(gt, eq, lt)`)
//! - `R0..R7`  : rotor registers (composable permutations)
//! - `IP`      : instruction pointer
//! - `stack`   : return IPs for CALL
//! - `mem`     : `HashMap<Cube, Cube>` keyed by full cube coordinate

pub mod opcodes {
    // 0..32 : data / I/O / register ops
    pub const NOP: u8 = 0;
    pub const LOADC: u8 = 1;        // C := Cube(arg, arg, arg)
    pub const LOAD_AXIS: u8 = 2;    // C := unit_axis(arg)
    pub const OUTI: u8 = 3;         // emit C.x
    pub const OUTV: u8 = 4;         // emit C
    pub const MOV_R: u8 = 5;        // R[dst] := R[src]  (arg = dst, target = src)
    pub const LOAD_R: u8 = 6;       // R[arg] := Perm::identity()

    // 32..56 : rotations applied to C
    pub const ROT_Z_90:  u8 = 32;
    pub const ROT_Z_180: u8 = 33;
    pub const ROT_Z_270: u8 = 34;
    pub const ROT_X_90:  u8 = 35;
    pub const ROT_X_180: u8 = 36;
    pub const ROT_X_270: u8 = 37;
    pub const ROT_Y_90:  u8 = 38;
    pub const ROT_Y_180: u8 = 39;
    pub const ROT_Y_270: u8 = 40;
    pub const APPLY_R:   u8 = 41;   // C := R[arg].apply(C)

    // 56..64 : reflections / inversion / rotor composition
    pub const REFLECT_X:  u8 = 56;
    pub const REFLECT_Y:  u8 = 57;
    pub const REFLECT_Z:  u8 = 58;
    pub const NEG:        u8 = 59;
    pub const COMPOSE_R:  u8 = 60;  // R[arg] := R[arg] * R[target]
    pub const INVERSE_R:  u8 = 61;  // R[arg] := R[arg].inverse()

    // 64..96 : arithmetic (saturating balanced-ternary on C.x)
    pub const IADD: u8 = 64;
    pub const ISUB: u8 = 65;
    pub const IMUL: u8 = 66;

    // 96..128 : comparison, three-way branching
    pub const CMP:     u8 = 96;
    pub const BR_NEG:  u8 = 97;
    pub const BR_ZERO: u8 = 98;
    pub const BR_POS:  u8 = 99;
    pub const JMP:     u8 = 100;
    pub const CALL:    u8 = 101;
    pub const RET:     u8 = 102;
    pub const BR_AXIS: u8 = 103;

    // 128..160 : memory (cube-addressed)
    pub const STORE:    u8 = 128;   // mem[Cube(arg,arg,arg)] := C    (axial shortcut)
    pub const LOAD:     u8 = 129;   // C := mem[Cube(arg,arg,arg)]
    pub const STORE_C:  u8 = 130;   // mem[C] := C                    (full-cube address)
    pub const LOAD_C:   u8 = 131;   // C := mem[C]

    // 192.. : meta
    pub const HALT: u8 = 192;
}

/// Number of rotor registers available to programs.
pub const ROTOR_COUNT: usize = 8;
