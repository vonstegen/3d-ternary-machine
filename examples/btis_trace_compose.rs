use btis::asm::assemble;
use btis::vm::VM;
use btis::isa::opcodes;

fn main() {
    let src = r#"
load_r 0
rot_z_90_r 0
load_r 1
rot_x_90_r 1
compose_r 0 1
halt
"#;
    let program = assemble(src).unwrap();
    let mut vm = VM::new(program);
    vm.run().unwrap();
    println!("After compose_r 0 1:");
    println!("  R[0] = {:?}", vm.R[0].0);
    println!("  R[1] = {:?}", vm.R[1].0);
    // Expected: R[0][i] = R[1][R_a[i]]
    // R_a[0] = 2 (encode(1,-1,-1)). R_b[2] = encode(R_b(1,-1,-1)).
    // R_b(1,-1,-1) = (x,-z,y) = (1,1,-1). encode(1,1,-1) = 2 + 6 + 0 = 8.
    println!("  Expected R[0][0] = 8");
}
