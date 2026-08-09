use btis::asm::assemble;
use btis::vm::VM;
use btis::cube::decode;

fn main() {
    let src = r#"
load_r 4
rot_z_90_r 4
load_r 0
rot_z_90_r 0
load_r 1
rot_x_90_r 1
load_r 2
rot_y_90_r 2
load_r 3
mov_r 3 0
inverse_r 3
compose_r 0 1
compose_r 0 4
compose_r 0 2
compose_r 0 3
compose_r 0 1
compose_r 0 2
compose_r 0 4
halt
"#;
    let p = assemble(src).unwrap();
    let mut vm = VM::new(p);
    vm.run().unwrap();
    for i in 0..27u8 {
        let r = vm.R[0].0[i as usize];
        let c = decode(i);
        let target = decode(r);
        println!("R[{:2}] = {:2}  ({},{},{}) -> ({},{},{})",
            i, r, c.0, c.1, c.2, target.0, target.1, target.2);
    }
}
