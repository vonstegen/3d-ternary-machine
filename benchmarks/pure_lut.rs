// Pure-Rust baseline: 27-entry LUT applied in a tight loop.
// A volatile read at the end of each iteration prevents the optimizer
// from constant-folding or eliminating the loop.

use std::time::Instant;

const ROT_Z_90: [u8; 27] = {
    let mut t = [0u8; 27];
    let mut x = -1i8;
    while x <= 1 {
        let mut y = -1i8;
        while y <= 1 {
            let mut z = -1i8;
            while z <= 1 {
                let cur = ((x + 1) as u8) + 3 * ((y + 1) as u8) + 9 * ((z + 1) as u8);
                let new = ((-y + 1) as u8) + 3 * ((x + 1) as u8) + 9 * ((z + 1) as u8);
                t[cur as usize] = new;
                z += 1;
            }
            y += 1;
        }
        x += 1;
    }
    t
};

fn main() {
    let n: u64 = std::env::args()
        .nth(1)
        .and_then(|s| s.parse().ok())
        .unwrap_or(10_000_000);

    let start = Instant::now();
    let mut state: u8 = 0;
    let mut blackhole: u8 = 0;
    for _ in 0..n {
        state = ROT_Z_90[state as usize];
        state = ROT_Z_90[state as usize];
        state = ROT_Z_90[state as usize];
        state = ROT_Z_90[state as usize];
        // Volatile store: compiler cannot remove this iteration.
        unsafe { std::ptr::write_volatile(&mut blackhole as *mut u8, state); }
    }
    let elapsed = start.elapsed();
    let ns = elapsed.as_nanos() as u64;
    let total_ops = n * 4;
    let ops_per_sec = total_ops * 1_000_000_000 / ns.max(1);

    println!("Pure-LUT baseline (Rust release)");
    println!("  iterations:  {} (4 LUT lookups each)", n);
    println!("  total ops:   {}", total_ops);
    println!("  elapsed:     {} ns", ns);
    println!("  throughput:  {} LUT lookups/sec", ops_per_sec);
    println!("  blackhole:   {} (volatile, prevents folding)", blackhole);
}
