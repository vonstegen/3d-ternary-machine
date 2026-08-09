//! Symmetry group of the 27-state cube.
//!
//! A geometric operation on the cube is a permutation of the 27 states.
//! Each operation is represented as a `[u8; 27]` lookup table; applying
//! the operation is a single array index. O(1) per step.
//!
//! Why this matters: in a conventional ISA, an operation like
//! "rotate-vector-90-about-z" is a numeric opcode. In BT-IS, it is a
//! permutation of cube states that happens to agree with a 90° rotation
//! about Z. The 27-entry LUT *is* the instruction.
//!
//! We implement the 24 orientation-preserving rotations of the cube (the
//! octahedral group O) plus the parity (reflection / inversion) operations.
//!
//! All permutations are built lazily on first use (`std::sync::LazyLock`).
//! That keeps the build simple on stable Rust (no `const fn` + `fn`-pointer
//! restrictions), and the table build is O(27) so cold cost is negligible.

use crate::cube::{encode, Cube, N};
use std::sync::LazyLock;

/// Permutation of the 27 cube states. `PERM[i]` is the image of state `i`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Perm(pub [u8; N]);

impl Perm {
    #[inline]
    pub const fn from_array(a: [u8; N]) -> Self { Perm(a) }

    #[inline]
    pub const fn apply(self, c: Cube) -> Cube {
        Cube::from_idx(self.0[c.idx() as usize])
    }

    /// Composition: `self.then(other)` means "apply `self`, then `other`".
    pub fn then(self, other: Perm) -> Perm {
        let mut out = [0u8; N];
        for i in 0..N {
            out[i] = other.0[self.0[i] as usize];
        }
        Perm(out)
    }

    pub fn identity() -> Perm {
        let mut a = [0u8; N];
        for i in 0..N { a[i] = i as u8; }
        Perm(a)
    }

    /// Build a permutation from a coordinate function.
    pub fn from_coord_fn<F: Fn(i8, i8, i8) -> (i8, i8, i8)>(f: F) -> Self {
        let mut a = [0u8; N];
        for x in -1i8..=1 {
            for y in -1i8..=1 {
                for z in -1i8..=1 {
                    let idx = encode(x, y, z);
                    let (nx, ny, nz) = f(x, y, z);
                    a[idx as usize] = encode(nx, ny, nz);
                }
            }
        }
        Perm(a)
    }
    pub fn as_array(&self) -> &[u8; N] { &self.0 }

    /// Inverse permutation: P.inv such that P.inv.apply(P.apply(c)) == c.
    pub fn inverse(&self) -> Perm {
        let mut inv = [0u8; N];
        for (i, &j) in self.0.iter().enumerate() {
            inv[j as usize] = i as u8;
        }
        Perm(inv)
    }

    /// Reverse permutation: same as `inverse` for these 27-state LUTs
    /// (every cube-symmetry permutation here is its own inverse or a
    /// 2/3/4-cycle; "reverse" is the operationally useful form when
    /// reasoning about reversibility of execution).
    pub fn reverse(&self) -> Perm { self.inverse() }
}
// ---- coordinate functions (named `fn` items for stable Rust) --------------

fn f_rot_z_90(x: i8, y: i8, z: i8) -> (i8, i8, i8)  { (-y, x, z) }
fn f_rot_z_180(x: i8, y: i8, z: i8) -> (i8, i8, i8) { (-x, -y, z) }
fn f_rot_z_270(x: i8, y: i8, z: i8) -> (i8, i8, i8) { (y, -x, z) }
fn f_rot_x_90(x: i8, y: i8, z: i8) -> (i8, i8, i8)  { (x, -z, y) }
fn f_rot_y_90(x: i8, y: i8, z: i8) -> (i8, i8, i8)  { (z, y, -x) }
fn f_neg(x: i8, y: i8, z: i8) -> (i8, i8, i8)       { (-x, -y, -z) }
fn f_reflect_z(x: i8, y: i8, z: i8) -> (i8, i8, i8) { (x, y, -z) }
fn f_reflect_y(x: i8, y: i8, z: i8) -> (i8, i8, i8) { (x, -y, z) }
fn f_reflect_x(x: i8, y: i8, z: i8) -> (i8, i8, i8) { (-x, y, z) }

fn build_perm(f: fn(i8, i8, i8) -> (i8, i8, i8)) -> Perm {
    let mut a = [0u8; N];
    for x in -1i8..=1 {
        for y in -1i8..=1 {
            for z in -1i8..=1 {
                let (nx, ny, nz) = f(x, y, z);
                let new_idx = ((nx + 1) as u8) + 3 * ((ny + 1) as u8) + 9 * ((nz + 1) as u8);
                let cur_idx = ((x + 1) as u8) + 3 * ((y + 1) as u8) + 9 * ((z + 1) as u8);
                a[cur_idx as usize] = new_idx;
            }
        }
    }
    Perm(a)
}

pub static ROT_Z_90:  LazyLock<Perm> = LazyLock::new(|| build_perm(f_rot_z_90));
pub static ROT_Z_180: LazyLock<Perm> = LazyLock::new(|| build_perm(f_rot_z_180));
pub static ROT_Z_270: LazyLock<Perm> = LazyLock::new(|| build_perm(f_rot_z_270));
pub static ROT_X_90:  LazyLock<Perm> = LazyLock::new(|| build_perm(f_rot_x_90));
pub static ROT_Y_90:  LazyLock<Perm> = LazyLock::new(|| build_perm(f_rot_y_90));

pub static ROT_X_180: LazyLock<Perm> = LazyLock::new(|| ROT_X_90.then(*ROT_X_90));
pub static ROT_X_270: LazyLock<Perm> = LazyLock::new(|| ROT_X_180.then(*ROT_X_90));
pub static ROT_Y_180: LazyLock<Perm> = LazyLock::new(|| ROT_Y_90.then(*ROT_Y_90));
pub static ROT_Y_270: LazyLock<Perm> = LazyLock::new(|| ROT_Y_180.then(*ROT_Y_90));

pub static NEG:       LazyLock<Perm> = LazyLock::new(|| build_perm(f_neg));
pub static REFLECT_X: LazyLock<Perm> = LazyLock::new(|| build_perm(f_reflect_x));
pub static REFLECT_Y: LazyLock<Perm> = LazyLock::new(|| build_perm(f_reflect_y));
pub static REFLECT_Z: LazyLock<Perm> = LazyLock::new(|| build_perm(f_reflect_z));

/// All 24 rotations of the cube (octahedral group O). Built lazily.
/// Used for exhaustive enumeration in tests.
pub static ALL_ROTATIONS: LazyLock<[Perm; 24]> = LazyLock::new(|| {
    let mut out: [Perm; 24] = [Perm::identity(); 24];
    out[0]  = Perm::identity();
    out[1]  = *ROT_X_90; out[2]  = *ROT_X_180; out[3]  = *ROT_X_270;
    out[4]  = *ROT_Y_90; out[5]  = *ROT_Y_180; out[6]  = *ROT_Y_270;
    out[7]  = *ROT_Z_90; out[8]  = *ROT_Z_180; out[9]  = *ROT_Z_270;
    // Six edge 180° rotations.
    out[10] = Perm::from_coord_fn(|x, y, z| (y, x, -z));   // axis (1,1,0)
    out[11] = Perm::from_coord_fn(|x, y, z| (-y, -x, -z)); // axis (-1,-1,0)
    out[12] = Perm::from_coord_fn(|x, y, z| (z, -y, x));   // axis (1,0,1)
    out[13] = Perm::from_coord_fn(|x, y, z| (-z, -y, -x)); // axis (-1,0,-1)
    out[14] = Perm::from_coord_fn(|x, y, z| (-x, z, y));   // axis (0,1,1)
    out[15] = Perm::from_coord_fn(|x, y, z| (x, -z, -y));  // axis (0,-1,-1)
    // Eight corner 120°/240° rotations.
    out[16] = Perm::from_coord_fn(|x, y, z| (z, x, y));     // 120° about (1,1,1)
    out[17] = Perm::from_coord_fn(|x, y, z| (y, z, x));     // 240° about (1,1,1)
    out[18] = Perm::from_coord_fn(|x, y, z| (-z, -x, y));   // 120° about (-1,-1,1)
    out[19] = Perm::from_coord_fn(|x, y, z| (z, x, -y));    // 240° about (-1,-1,1)
    out[20] = Perm::from_coord_fn(|x, y, z| (-y, z, -x));   // 120° about (-1,1,-1)
    out[21] = Perm::from_coord_fn(|x, y, z| (y, -z, x));    // 240° about (-1,1,-1)
    out[22] = Perm::from_coord_fn(|x, y, z| (-x, -z, y));   // 120° about (1,-1,-1)
    out[23] = Perm::from_coord_fn(|x, y, z| (x, z, -y));    // 240° about (1,-1,-1)
    out
});

#[cfg(test)]
mod tests {
    use super::*;

    fn roundtrip(p: Perm) {
        let mut hits = [0u32; N];
        for i in 0..N {
            let j = p.0[i] as usize;
            assert!(j < N, "perm maps to invalid index");
            hits[j] += 1;
        }
        for h in hits.iter() {
            assert_eq!(*h, 1, "perm is not a bijection");
        }
    }

    #[test]
    fn perms_are_bijections() {
        roundtrip(*ROT_Z_90);
        roundtrip(*ROT_Z_180);
        roundtrip(*ROT_Z_270);
        roundtrip(*ROT_X_90);
        roundtrip(*ROT_X_180);
        roundtrip(*ROT_X_270);
        roundtrip(*ROT_Y_90);
        roundtrip(*ROT_Y_180);
        roundtrip(*ROT_Y_270);
        roundtrip(*NEG);
        roundtrip(*REFLECT_X);
        roundtrip(*REFLECT_Y);
        roundtrip(*REFLECT_Z);
        for p in ALL_ROTATIONS.iter() { roundtrip(*p); }
    }

    #[test]
    fn rot_z_90_examples() {
        assert_eq!(ROT_Z_90.apply(Cube::new(1, 0, 0)), Cube::new(0, 1, 0));
        assert_eq!(ROT_Z_90.apply(Cube::new(0, 1, 0)), Cube::new(-1, 0, 0));
        assert_eq!(ROT_Z_90.apply(Cube::CENTER), Cube::CENTER);
    }

    #[test]
    fn rot_x_90_examples() {
        assert_eq!(ROT_X_90.apply(Cube::new(0, 1, 0)), Cube::new(0, 0, 1));
        assert_eq!(ROT_X_90.apply(Cube::new(0, 0, 1)), Cube::new(0, -1, 0));
    }

    #[test]
    fn rot_y_90_examples() {
        assert_eq!(ROT_Y_90.apply(Cube::new(1, 0, 0)), Cube::new(0, 0, -1));
        assert_eq!(ROT_Y_90.apply(Cube::new(0, 0, 1)), Cube::new(1, 0, 0));
    }

    #[test]
    fn neg_inverts_all_axes() {
        let c = Cube::new(1, -1, 0);
        let nc = NEG.apply(c);
        assert_eq!(nc, Cube::new(-1, 1, 0));
        assert_eq!(NEG.apply(nc), c);
    }

    #[test]
    fn four_z_rotations_are_identity() {
        let r4 = ROT_Z_90.then(*ROT_Z_90).then(*ROT_Z_90).then(*ROT_Z_90);
        assert_eq!(r4, Perm::identity());
    }

    #[test]
    fn rotation_180_inverts() {
        assert_eq!(ROT_Z_180.apply(Cube::new(1, 1, 1)), Cube::new(-1, -1, 1));
        assert_eq!(ROT_Y_180.apply(Cube::new(1, 1, 1)), Cube::new(-1, 1, -1));
    }

    #[test]
    fn reflect_z() {
        assert_eq!(REFLECT_Z.apply(Cube::new(1, 0, 1)), Cube::new(1, 0, -1));
        assert_eq!(REFLECT_Z.apply(Cube::new(1, 0, 0)), Cube::new(1, 0, 0));
    }

    #[test]
     fn rotations_partition_state_space() {
         let corner = Cube::new(1, 1, 1);
         let mut seen = [false; N];
         for r in ALL_ROTATIONS.iter() {
             seen[r.apply(corner).idx() as usize] = true;
         }
        // (1,1,1) is fixed by the 3 rotations about its body diagonal,
        // so its orbit under O has size |O| / 3 = 8.
         let n_seen: usize = seen.iter().map(|&b| b as usize).sum();
        assert_eq!(n_seen, 8, "corner orbit under O has size 8");

         let x_axis = Cube::new(1, 0, 0);
         let mut seen2 = [false; N];
         for r in ALL_ROTATIONS.iter() {
             seen2[r.apply(x_axis).idx() as usize] = true;
         }
         let n2: usize = seen2.iter().map(|&b| b as usize).sum();
         assert_eq!(n2, 6, "axial orbit under O has size 6");
     }
}
