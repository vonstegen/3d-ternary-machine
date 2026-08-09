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
use crate::vm::Instr;
 use crate::isa::opcodes as op;
 use std::collections::HashMap;
 #[derive(Debug, Clone, Copy)]
enum OpKind { None, Int, Axis, TwoReg }

#[derive(Debug, Clone)]
enum Token {
    Ident(String),
    IntLit(i8),
    Colon,
    Comma,
    LParen,
    RParen,
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
            '0'..='9' | '-' => {
                let start = i;
                if c == '-' { i += 1; }
                while i < bytes.len() && (bytes[i] as char).is_ascii_digit() { i += 1; }
                let s = std::str::from_utf8(&bytes[start..i]).unwrap();
                let n: i8 = s.parse().map_err(|_| format!("bad int: {s}"))?;
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
                labels.insert(nm.clone(), out.len());
                i += 1;
                continue;
            } else {
                return Err("label: missing name".into());
            }
        }

         let (opcode, has_jump_label, kind) = match name.as_str() {
             "nop"       => (op::NOP,       false, OpKind::None),
             "halt"      => (op::HALT,      false, OpKind::None),
             "loadc"     => (op::LOADC,     false, OpKind::Int),
             "load_axis" => (op::LOAD_AXIS, false, OpKind::Axis),
             "outc"      => (op::OUTV,      false, OpKind::None),
             "outi"      => (op::OUTI,      false, OpKind::None),
             "rot_z_90"  => (op::ROT_Z_90,  false, OpKind::None),
             "rot_z_180" => (op::ROT_Z_180, false, OpKind::None),
             "rot_z_270" => (op::ROT_Z_270, false, OpKind::None),
             "rot_x_90"  => (op::ROT_X_90,  false, OpKind::None),
             "rot_x_180" => (op::ROT_X_180, false, OpKind::None),
             "rot_x_270" => (op::ROT_X_270, false, OpKind::None),
             "rot_y_90"  => (op::ROT_Y_90,  false, OpKind::None),
             "rot_y_180" => (op::ROT_Y_180, false, OpKind::None),
             "rot_y_270" => (op::ROT_Y_270, false, OpKind::None),
             "apply_r"   => (op::APPLY_R,   false, OpKind::Int),
             "reflect_x" => (op::REFLECT_X, false, OpKind::None),
             "reflect_y" => (op::REFLECT_Y, false, OpKind::None),
             "reflect_z" => (op::REFLECT_Z, false, OpKind::None),
             "neg"       => (op::NEG,       false, OpKind::None),
             "compose_r" => (op::COMPOSE_R, false, OpKind::TwoReg),
             "inverse_r" => (op::INVERSE_R, false, OpKind::Int),
             "mov_r"     => (op::MOV_R,     false, OpKind::TwoReg),
             "load_r"    => (op::LOAD_R,    false, OpKind::Int),
             "iadd"      => (op::IADD,      false, OpKind::Int),
             "isub"      => (op::ISUB,      false, OpKind::Int),
             "imul"      => (op::IMUL,      false, OpKind::Int),
             "cmp"       => (op::CMP,       false, OpKind::Int),
             "store"     => (op::STORE,     false, OpKind::Int),
             "load"      => (op::LOAD,      false, OpKind::Int),
             "store_c"   => (op::STORE_C,   false, OpKind::None),
             "load_c"    => (op::LOAD_C,    false, OpKind::None),
             "br_neg"    => (op::BR_NEG,    true,  OpKind::None),
             "br_zero"   => (op::BR_ZERO,   true,  OpKind::None),
             "br_pos"    => (op::BR_POS,    true,  OpKind::None),
             "br_axis"   => (op::BR_AXIS,   true,  OpKind::Int),
             "jmp"       => (op::JMP,       true,  OpKind::None),
             "call"      => (op::CALL,      true,  OpKind::None),
             "ret"       => (op::RET,       false, OpKind::None),
             other => return Err(format!("unknown mnemonic: {other}")),
         };
        let mut arg: i8 = 0;
        let mut target: usize = 0;
         let mut jump_label: Option<String> = None;
         if i < toks.len() {
             match &toks[i] {
                 Token::IntLit(n) => {
                     if has_jump_label { return Err("expected label, got int".into()); }
                     if matches!(kind, OpKind::None) {
                         return Err("unexpected integer operand".into());
                     }
                     if matches!(kind, OpKind::TwoReg) {
                         // First int is dst (arg); expect second int for src (target).
                         arg = *n;
                         i += 1;
                         if let Some(Token::IntLit(m)) = toks.get(i) {
                             target = (*m).max(0) as usize;
                             i += 1;
                         } else {
                             return Err("TwoReg needs two integer operands".into());
                         }
                     } else {
                         arg = *n;
                         i += 1;
                     }
                 }
                 Token::Ident(nm) if has_jump_label => {
                     jump_label = Some(nm.clone());
                     i += 1;
                 }
                 Token::Ident(nm) if matches!(kind, OpKind::Axis) => {
                     arg = match nm.as_str() {
                         "X"  => 0, "XI" => 1,
                         "Y"  => 2, "YI" => 3,
                         "Z"  => 4, "ZI" => 5,
                         other => return Err(format!("unknown axis: {other}")),
                     };
                     i += 1;
                 }
                 _ => {}
             }
         }

        let idx = out.len();
        out.push(Instr { opcode, arg, target });
        if let Some(lbl) = jump_label {
            jumps.push((idx, lbl));
        }
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
}
