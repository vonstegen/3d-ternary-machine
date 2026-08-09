// Dump the BT-IS rotation tables to JSON for cross-verification
// with the Python cube module.

use std::fs;
use std::fmt::Write;

fn perm_array(p: &btis::symmetry::Perm) -> &[u8; 27] { &p.0 }

fn main() {
    use btis::cube::Cube;
    use btis::symmetry::*;

    let perms: Vec<(&str, &[u8; 27])> = vec![
        ("ROT_Z_90",  perm_array(&ROT_Z_90)),
        ("ROT_Z_180", perm_array(&ROT_Z_180)),
        ("ROT_Z_270", perm_array(&ROT_Z_270)),
        ("ROT_X_90",  perm_array(&ROT_X_90)),
        ("ROT_X_180", perm_array(&ROT_X_180)),
        ("ROT_X_270", perm_array(&ROT_X_270)),
        ("ROT_Y_90",  perm_array(&ROT_Y_90)),
        ("ROT_Y_180", perm_array(&ROT_Y_180)),
        ("ROT_Y_270", perm_array(&ROT_Y_270)),
        ("REFLECT_X", perm_array(&REFLECT_X)),
        ("REFLECT_Y", perm_array(&REFLECT_Y)),
        ("REFLECT_Z", perm_array(&REFLECT_Z)),
        ("NEG",       perm_array(&NEG)),
    ];

    let mut s = String::new();
    writeln!(s, "{{").unwrap();
    writeln!(s, "  \"states\": [").unwrap();
    let mut first_state = true;
    for x in -1i8..=1 {
        for y in -1i8..=1 {
            for z in -1i8..=1 {
                let cube = Cube::new(x, y, z);
                if !first_state { writeln!(s, ",").unwrap(); }
                first_state = false;
                write!(s, "    {{\"idx\": {}, \"x\": {}, \"y\": {}, \"z\": {}}}", cube.idx(), cube.x(), cube.y(), cube.z()).unwrap();
            }
        }
    }
    writeln!(s, "\n  ],").unwrap();
    writeln!(s, "  \"perms\": {{").unwrap();
    let mut first_perm = true;
    for (name, p) in &perms {
        if !first_perm { writeln!(s, ",").unwrap(); }
        first_perm = false;
        write!(s, "    \"{}\": [", name).unwrap();
        for (i, j) in p.iter().enumerate() {
            if i > 0 { write!(s, ", ").unwrap(); }
            write!(s, "{}", j).unwrap();
        }
        write!(s, "]").unwrap();
    }
    writeln!(s, "\n  }}").unwrap();
    writeln!(s, "}}").unwrap();
    let n = s.len();
     fs::write("benchmarks/rust_tables.json", s).expect("write");
     eprintln!("wrote benchmarks/rust_tables.json ({} bytes)", n);
}
