//! Symbolic assembler for BT-IS.
//!
//! Mnemonics are geometric verbs. Labels are resolved in a single pass
//! after parsing. Grammar: a program is a sequence of lines; a line is
//! either `label NAME` or a mnemonic optionally followed by an integer,
//! axis name, or jump label.
//!
//! Mnemonics that take an axis (e.g. `load_axis`) accept the named axes
//! `X XI Y YI Z ZI` directly; other instructions accept a small signed
//! integer in `{-1, 0, +1}` (or a jump label).
//!
//! Operand validation:
//! - Mnemonics that need an operand are checked at assembly time.
//!   Missing operand is an error.
//! - For trit mnemonics (`loadc`, `iadd`, `isub`, `imul`, `cmp`,
//!   `store`, `load`), the integer must be in `{-1, 0, +1}`.
//! - For register mnemonics, the index must be in `[0, count)`.
use crate::isa::{opcodes as op, DATA_REG_COUNT, ROTOR_COUNT};
use crate::vm::Instr;
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum OpKind {
    /// No operand (e.g., `nop`, `halt`, `rot_z_90`).
    None,
    /// Single small signed integer in {-1, 0, +1}.
    Trit,
    /// Axis name (X, XI, Y, YI, Z, ZI). Encoded as 0..5 in `arg`.
    Axis,
    /// Single rotor register index in [0, ROTOR_COUNT).
    RotorR,
    /// Single data register index in [0, DATA_REG_COUNT).
    DataR,
    /// Two rotor register indices: arg = dst, target = src.
    /// Both must be in [0, ROTOR_COUNT).
    TwoRegRotor,
    /// Branch target label.
    Label,
    /// Special: `br_axis AXIS LABEL`. Both arg and target set.
    AxisAndLabel,
}

#[derive(Debug, Clone)]
enum Token {
    Ident(String),
    IntLit(i16),
    Colon,
    Comma,
    LParen,
    RParen,
}

struct Mnemonic {
    opcode: u8,
    kind: OpKind,
}

fn tokenize(src: &str) -> Result<Vec<Token>, String> {
    let mut out = Vec::new();
    let bytes = src.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        let c = bytes[i] as char;
        match c {
            ' ' | '\t' | '\r' | '\n' => { i += 1; }
            ':' => { out.push(Token::Colon); i += 1; }
            ',' => { out.push(Token::Comma); i += 1; }
            '(' => { out.push(Token::LParen); i += 1; }
            ')' => { out.push(Token::RParen); i += 1; }
            ';' => {
                while i < bytes.len() && bytes[i] != b'\n' { i += 1; }
            }
            '0'..='9' => {
                let start = i;
                while i < bytes.len() && (bytes[i] as char).is_ascii_digit() { i += 1; }
                let s = std::str::from_utf8(&bytes[start..i]).unwrap();
                let n: i16 = s.parse().map_err(|_| format!("bad int: {s}"))?;
                out.push(Token::IntLit(n));
            }
            '-' => {
                // Negative literal: '-' followed by digits.
                let start = i;
                i += 1;
                let digit_start = i;
                while i < bytes.len() && (bytes[i] as char).is_ascii_digit() { i += 1; }
                if i == digit_start {
                    return Err(format!("stray '-' at byte {start}"));
                }
                let s = std::str::from_utf8(&bytes[start..i]).unwrap();
                let n: i16 = s.parse().map_err(|_| format!("bad int: {s}"))?;
                out.push(Token::IntLit(n));
            }
            c if c.is_alphabetic() || c == '_' => {
                let start = i;
                while i < bytes.len() {
                    let cc = bytes[i] as char;
                    if cc.is_alphanumeric() || cc == '_' || cc == '.' { i += 1; } else { break; }
                }
                let id = std::str::from_utf8(&bytes[start..i]).unwrap().to_string();
                out.push(Token::Ident(id));
            }
            other => return Err(format!("unexpected char: {other}")),
        }
    }
    Ok(out)
}

fn lookup(name: &str) -> Result<Mnemonic, String> {
    let m = match name {
        // No-operand mnemonics
        "nop"       => Mnemonic { opcode: op::NOP,       kind: OpKind::None },
        "halt"      => Mnemonic { opcode: op::HALT,      kind: OpKind::None },
        "outc"      => Mnemonic { opcode: op::OUTV,      kind: OpKind::None },
        "outi"      => Mnemonic { opcode: op::OUTI,      kind: OpKind::None },
        "rot_z_90"  => Mnemonic { opcode: op::ROT_Z_90,  kind: OpKind::None },
        "rot_z_180" => Mnemonic { opcode: op::ROT_Z_180, kind: OpKind::None },
        "rot_z_270" => Mnemonic { opcode: op::ROT_Z_270, kind: OpKind::None },
        "rot_x_90"  => Mnemonic { opcode: op::ROT_X_90,  kind: OpKind::None },
        "rot_x_180" => Mnemonic { opcode: op::ROT_X_180, kind: OpKind::None },
        "rot_x_270" => Mnemonic { opcode: op::ROT_X_270, kind: OpKind::None },
        "rot_y_90"  => Mnemonic { opcode: op::ROT_Y_90,  kind: OpKind::None },
        "rot_y_180" => Mnemonic { opcode: op::ROT_Y_180, kind: OpKind::None },
        "rot_y_270" => Mnemonic { opcode: op::ROT_Y_270, kind: OpKind::None },
        "reflect_x" => Mnemonic { opcode: op::REFLECT_X, kind: OpKind::None },
        "reflect_y" => Mnemonic { opcode: op::REFLECT_Y, kind: OpKind::None },
        "reflect_z" => Mnemonic { opcode: op::REFLECT_Z, kind: OpKind::None },
        "neg"       => Mnemonic { opcode: op::NEG,       kind: OpKind::None },
        "cycle_x"   => Mnemonic { opcode: op::CYCLE_X,   kind: OpKind::None },
        "cycle_y"   => Mnemonic { opcode: op::CYCLE_Y,   kind: OpKind::None },
        "cycle_z"   => Mnemonic { opcode: op::CYCLE_Z,   kind: OpKind::None },
        "cube_add"  => Mnemonic { opcode: op::CUBE_ADD,  kind: OpKind::None },
        "store_c"   => Mnemonic { opcode: op::STORE_C,   kind: OpKind::None },
        "load_c"    => Mnemonic { opcode: op::LOAD_C,    kind: OpKind::None },
        "ret"       => Mnemonic { opcode: op::RET,       kind: OpKind::None },
        // Trit operands
        "loadc"     => Mnemonic { opcode: op::LOADC,     kind: OpKind::Trit },
        "iadd"      => Mnemonic { opcode: op::IADD,      kind: OpKind::Trit },
        "isub"      => Mnemonic { opcode: op::ISUB,      kind: OpKind::Trit },
        "imul"      => Mnemonic { opcode: op::IMUL,      kind: OpKind::Trit },
        "cmp"       => Mnemonic { opcode: op::CMP,       kind: OpKind::Trit },
        "store"     => Mnemonic { opcode: op::STORE,     kind: OpKind::Trit },
        "load"      => Mnemonic { opcode: op::LOAD,      kind: OpKind::Trit },
        // Axis
        "load_axis" => Mnemonic { opcode: op::LOAD_AXIS, kind: OpKind::Axis },
        // Rotor registers (single index)
        "apply_r"      => Mnemonic { opcode: op::APPLY_R,      kind: OpKind::RotorR },
        "rot_z_90_r"   => Mnemonic { opcode: op::ROT_Z_90_R,   kind: OpKind::RotorR },
        "rot_z_180_r"  => Mnemonic { opcode: op::ROT_Z_180_R,  kind: OpKind::RotorR },
        "rot_z_270_r"  => Mnemonic { opcode: op::ROT_Z_270_R,  kind: OpKind::RotorR },
        "rot_x_90_r"   => Mnemonic { opcode: op::ROT_X_90_R,   kind: OpKind::RotorR },
        "rot_x_180_r"  => Mnemonic { opcode: op::ROT_X_180_R,  kind: OpKind::RotorR },
        "rot_x_270_r"  => Mnemonic { opcode: op::ROT_X_270_R,  kind: OpKind::RotorR },
        "rot_y_90_r"   => Mnemonic { opcode: op::ROT_Y_90_R,   kind: OpKind::RotorR },
        "rot_y_180_r"  => Mnemonic { opcode: op::ROT_Y_180_R,  kind: OpKind::RotorR },
        "rot_y_270_r"  => Mnemonic { opcode: op::ROT_Y_270_R,  kind: OpKind::RotorR },
        "reflect_x_r"  => Mnemonic { opcode: op::REFLECT_X_R,  kind: OpKind::RotorR },
        "reflect_y_r"  => Mnemonic { opcode: op::REFLECT_Y_R,  kind: OpKind::RotorR },
        "reflect_z_r"  => Mnemonic { opcode: op::REFLECT_Z_R,  kind: OpKind::RotorR },
        "neg_r"        => Mnemonic { opcode: op::NEG_R,        kind: OpKind::RotorR },
        "inverse_r"    => Mnemonic { opcode: op::INVERSE_R,    kind: OpKind::RotorR },
        "load_r"       => Mnemonic { opcode: op::LOAD_R,       kind: OpKind::RotorR },
        // Two rotor registers (dst, src)
        "compose_r"    => Mnemonic { opcode: op::COMPOSE_R,    kind: OpKind::TwoRegRotor },
        "mov_r"        => Mnemonic { opcode: op::MOV_R,        kind: OpKind::TwoRegRotor },
        // Data registers (single index)
        "mov_cd"       => Mnemonic { opcode: op::MOV_CD,       kind: OpKind::DataR },
        "mov_dc"       => Mnemonic { opcode: op::MOV_DC,       kind: OpKind::DataR },
        "store_d"      => Mnemonic { opcode: op::STORE_D,      kind: OpKind::DataR },
        "load_d"       => Mnemonic { opcode: op::LOAD_D,       kind: OpKind::DataR },
        // Branches and control
        "br_neg"       => Mnemonic { opcode: op::BR_NEG,       kind: OpKind::Label },
        "br_zero"      => Mnemonic { opcode: op::BR_ZERO,      kind: OpKind::Label },
        "br_pos"       => Mnemonic { opcode: op::BR_POS,       kind: OpKind::Label },
        "br_axis"      => Mnemonic { opcode: op::BR_AXIS,      kind: OpKind::AxisAndLabel },
        "jmp"          => Mnemonic { opcode: op::JMP,          kind: OpKind::Label },
        "call"         => Mnemonic { opcode: op::CALL,         kind: OpKind::Label },
        other => return Err(format!("unknown mnemonic: {other}")),
    };
    Ok(m)
}

fn parse_axis(name: &str) -> Result<i8, String> {
    Ok(match name {
        "X"  => 0, "XI" => 1,
        "Y"  => 2, "YI" => 3,
        "Z"  => 4, "ZI" => 5,
        other => return Err(format!("unknown axis: {other}")),
    })
}

fn validate_trit(n: i16) -> Result<i8, String> {
    if n < -1 || n > 1 {
        return Err(format!(
            "trit operand out of range: {} (must be in {{-1, 0, +1}})",
            n
        ));
    }
    Ok(n as i8)
}

fn validate_reg(n: i16, kind: &str, max: usize) -> Result<usize, String> {
    if n < 0 || n as usize >= max {
        return Err(format!(
            "{} register index out of range: {} (must be in [0, {}))",
            kind, n, max
        ));
    }
    Ok(n as usize)
}

/// Assemble a `.btis` source string into a flat list of instructions.
pub fn assemble(src: &str) -> Result<Vec<Instr>, String> {
    let toks = tokenize(src)?;
    let mut labels: HashMap<String, usize> = HashMap::new();
    let mut jumps: Vec<(usize, String)> = Vec::new();
    let mut out: Vec<Instr> = Vec::new();
    let mut i = 0;
    while i < toks.len() {
        let name = match &toks[i] {
            Token::Ident(n) => n.clone(),
            t => return Err(format!("unexpected token at {i}: {:?}", t)),
        };
        i += 1;

        if name == "label" {
            if let Some(Token::Ident(nm)) = toks.get(i) {
                if labels.contains_key(nm) {
                    return Err(format!("duplicate label: {nm}"));
                }
                labels.insert(nm.clone(), out.len());
                i += 1;
                continue;
            } else {
                return Err("label: missing name".into());
            }
        }

        let mn = lookup(&name)?;
        let mut arg: i8 = 0;
        let mut target: usize = 0;

        match mn.kind {
            OpKind::None => {
                if let Some(t) = toks.get(i) {
                    if matches!(t, Token::IntLit(_)) {
                        return Err(format!("{name}: unexpected integer operand"));
                    }
                }
            }
            OpKind::Trit => {
                let n = match toks.get(i) {
                    Some(Token::IntLit(n)) => *n,
                    _ => return Err(format!("{name}: missing integer operand")),
                };
                i += 1;
                arg = validate_trit(n)?;
            }
            OpKind::Axis => {
                let ax = match toks.get(i) {
                    Some(Token::Ident(s)) => s.clone(),
                    _ => return Err(format!("{name}: missing axis name")),
                };
                i += 1;
                arg = parse_axis(&ax)?;
            }
            OpKind::RotorR => {
                let n = match toks.get(i) {
                    Some(Token::IntLit(n)) => *n,
                    _ => return Err(format!("{name}: missing rotor register index")),
                };
                i += 1;
                arg = validate_reg(n, "rotor", ROTOR_COUNT)? as i8;
            }
            OpKind::DataR => {
                let n = match toks.get(i) {
                    Some(Token::IntLit(n)) => *n,
                    _ => return Err(format!("{name}: missing data register index")),
                };
                i += 1;
                arg = validate_reg(n, "data", DATA_REG_COUNT)? as i8;
            }
            OpKind::TwoRegRotor => {
                let a = match toks.get(i) {
                    Some(Token::IntLit(n)) => *n,
                    _ => return Err(format!("{name}: missing first integer operand")),
                };
                i += 1;
                let b = match toks.get(i) {
                    Some(Token::IntLit(n)) => *n,
                    _ => return Err(format!("{name}: missing second integer operand")),
                };
                i += 1;
                arg = validate_reg(a, "rotor", ROTOR_COUNT)? as i8;
                target = validate_reg(b, "rotor", ROTOR_COUNT)?;
            }
            OpKind::Label => {
                let lbl = match toks.get(i) {
                    Some(Token::Ident(s)) => s.clone(),
                    _ => return Err(format!("{name}: missing branch label")),
                };
                i += 1;
                jumps.push((out.len(), lbl));
            }
            OpKind::AxisAndLabel => {
                let ax = match toks.get(i) {
                    Some(Token::Ident(s)) => s.clone(),
                    _ => return Err("br_axis: missing axis name".into()),
                };
                i += 1;
                arg = parse_axis(&ax)?;
                let lbl = match toks.get(i) {
                    Some(Token::Ident(s)) => s.clone(),
                    _ => return Err("br_axis: missing branch label".into()),
                };
                i += 1;
                jumps.push((out.len(), lbl));
            }
        }

        out.push(Instr { opcode: mn.opcode, arg, target });
    }

    for (idx, lbl) in jumps.iter() {
        match labels.get(lbl) {
            Some(&t) => out[*idx].target = t,
            None => return Err(format!("unresolved label: {lbl}")),
        }
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_assembles_to_empty() {
        let p = assemble("").unwrap();
        assert!(p.is_empty());
    }

    #[test]
    fn loadc_halt() {
        let p = assemble("loadc 1\nhalt").unwrap();
        assert_eq!(p.len(), 2);
        assert_eq!(p[0].opcode, op::LOADC);
        assert_eq!(p[0].arg, 1);
        assert_eq!(p[1].opcode, op::HALT);
    }

    #[test]
    fn labels_resolve_jumps() {
        let src = "
            loadc 1
            jmp done
            loadc -1
            label done
            halt
        ";
        let p = assemble(src).unwrap();
        assert_eq!(p[1].target, 3);
    }

    #[test]
    fn unknown_mnemonic_errors() {
        assert!(assemble("frobnicate").is_err());
    }

    #[test]
    fn unresolved_label_errors() {
        assert!(assemble("jmp nowhere").is_err());
    }

    #[test]
    fn load_axis_resolves_named() {
        let p = assemble("load_axis X\nhalt").unwrap();
        assert_eq!(p[0].opcode, op::LOAD_AXIS);
        assert_eq!(p[0].arg, 0);
    }

    #[test]
    fn load_axis_resolves_negated() {
        let p = assemble("load_axis YI\nhalt").unwrap();
        assert_eq!(p[0].opcode, op::LOAD_AXIS);
        assert_eq!(p[0].arg, 3);
    }

    // --- v0.3.1 validation tests (formerly silent bugs) ---

    #[test]
    fn loadc_missing_operand_errors() {
        assert!(assemble("loadc\nhalt").is_err());
    }

    #[test]
    fn loadc_out_of_range_errors() {
        assert!(assemble("loadc 2\nhalt").is_err());
        assert!(assemble("loadc -2\nhalt").is_err());
        assert!(assemble("loadc 100\nhalt").is_err());
    }

    #[test]
    fn load_r_out_of_range_errors() {
        assert!(assemble("load_r 8\nhalt").is_err());
        assert!(assemble("load_r -1\nhalt").is_err());
    }

    #[test]
    fn mov_dc_out_of_range_errors() {
        assert!(assemble("mov_dc 4\nhalt").is_err());
        assert!(assemble("mov_dc -1\nhalt").is_err());
    }

    #[test]
    fn compose_r_negative_dst_rejected() {
        assert!(assemble("compose_r 0 -1\nhalt").is_err());
    }

    #[test]
    fn compose_r_out_of_range_src_rejected() {
        assert!(assemble("compose_r 0 8\nhalt").is_err());
    }

    #[test]
    fn br_axis_assembles_with_axis_and_label() {
        let src = "
            loadc 0
            br_axis X done
            loadc 1
            label done
            halt
        ";
        let p = assemble(src).unwrap();
        assert_eq!(p[1].opcode, op::BR_AXIS);
        assert_eq!(p[1].arg, 0);  // X
        assert_eq!(p[1].target, 3);  // jumps to halt
    }

    #[test]
    fn br_axis_missing_axis_errors() {
        assert!(assemble("br_axis done\nhalt").is_err());
    }

    #[test]
    fn br_axis_missing_label_errors() {
        assert!(assemble("br_axis X\nhalt").is_err());
    }

    #[test]
    fn duplicate_label_errors() {
        let src = "
            label x
            loadc 0
            label x
            halt
        ";
        assert!(assemble(src).is_err());
    }

    #[test]
    fn stray_dash_errors() {
        assert!(assemble("halt -").is_err());
    }

    #[test]
    fn outc_rejects_trailing_operand() {
        assert!(assemble("outc 1\nhalt").is_err());
    }

    #[test]
    fn rot_z_90_rejects_operands() {
        assert!(assemble("rot_z_90 1\nhalt").is_err());
    }

    #[test]
    fn load_r_just_below_max_ok() {
        let p = assemble("load_r 7\nhalt").unwrap();
        assert_eq!(p[0].arg, 7);
    }

    #[test]
    fn mov_dc_3_ok() {
        let p = assemble("mov_dc 3\nhalt").unwrap();
        assert_eq!(p[0].arg, 3);
    }
}
