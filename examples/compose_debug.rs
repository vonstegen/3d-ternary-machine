use btis::asm::assemble;
use btis::vm::VM;
use btis::cube::Cube;

fn main() {
    // Step 1: just R[0] = ROT_Z_90
    let src = r#"
load_r 0
rot_z_90_r 0
halt
"#;
    let p = assemble(src).unwrap();
    let mut vm = VM::new(p);
    vm.run().unwrap();
    println!("Step 1: load_r 0; rot_z_90_r 0");
    println!("  R[0][1] = {} (expect 5: (0,-1,-1) -> (1,0,-1))", vm.R[0].0[1]);
    println!("  R[0].apply((0,-1,-1)) = {:?}", vm.R[0].apply(Cube::new(0, -1, -1)));

    // Step 2: also load R[1] = ROT_X_90
    let src = r#"
load_r 0
rot_z_90_r 0
load_r 1
rot_x_90_r 1
halt
"#;
    let p = assemble(src).unwrap();
    let mut vm = VM::new(p);
    vm.run().unwrap();
    println!("\nStep 2: + load_r 1; rot_x_90_r 1");
    println!("  R[0][1] = {} (still expect 5)", vm.R[0].0[1]);
    println!("  R[1][1] = {} (expect 7: (0,-1,-1) -> (0,1,-1))", vm.R[1].0[1]);
    println!("  R[0].apply((0,-1,-1)) = {:?}", vm.R[0].apply(Cube::new(0, -1, -1)));

    // Step 3: now compose_r 0 1
    let src = r#"
load_r 0
rot_z_90_r 0
load_r 1
rot_x_90_r 1
compose_r 0 1
halt
"#;
    let p = assemble(src).unwrap();
    let mut vm = VM::new(p);
    vm.run().unwrap();
    println!("\nStep 3: + compose_r 0 1");
    println!("  R[0][1] = {} (expect 8: ROT_X_90 then ROT_Z_90? no, ROT_Z_90.then(ROT_X_90))", vm.R[0].0[1]);
    // R[0].then(R[1]) at i=1: out[1] = R[1][R[0][1]] = R[1][5] = ROT_X_90[5]
    // ROT_X_90 = (x,-z,y). decode(5) = (1,0,-1). Apply: (1,1,0). encode = 2+6+0 = 8.
    println!("  R[0].apply((0,-1,-1)) = {:?}", vm.R[0].apply(Cube::new(0, -1, -1)));
    println!("  Expected (1, 1, 0) = idx 8");
}
