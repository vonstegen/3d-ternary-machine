//! The 27-state balanced-ternary cube: the machine's fundamental primitive.
//!
//! A single machine symbol is a point in `{-1, 0, +1}^3`. The geometry of
//! this set (1 center + 6 axial + 12 face-diagonal + 8 corner = 27) is the
//! source of instruction semantics, not decoration.


use std::fmt;

/// Number of distinct cube states. `3^3 = 27`.
pub const N: usize = 27;

/// All 27 states enumerated in lexicographic `(x, y, z)` order.
pub const ALL: [Cube; N] = {
    let mut out = [Cube::CENTER; N];
    let mut i = 0usize;
    let mut x = -1i8;
    while x <= 1 {
        let mut y = -1i8;
        while y <= 1 {
            let mut z = -1i8;
            while z <= 1 {
                out[i] = Cube::new(x, y, z);
                i += 1;
                z += 1;
            }
            y += 1;
        }
        x += 1;
    }
    out
};

/// A point in the 27-state cube, packed into a single `u8` (5 bits suffice).
#[derive(Clone, Copy, Default, PartialEq, Eq, Hash, PartialOrd, Ord)]
#[repr(transparent)]
pub struct Cube(u8);

impl Cube {
    /// The center of the cube `(0,0,0)`, packed index 13.
    pub const CENTER: Cube = Cube(13);

    #[inline]
    pub const fn new(x: i8, y: i8, z: i8) -> Self {
        debug_assert!(x >= -1 && x <= 1 && y >= -1 && y <= 1 && z >= -1 && z <= 1);
        Cube(encode(x, y, z))
    }

    #[inline]
    pub const fn from_idx(idx: u8) -> Self {
        debug_assert!((idx as usize) < N);
        Cube(idx)
    }

    #[inline]
    pub const fn idx(self) -> u8 { self.0 }

    #[inline]
    pub const fn x(self) -> i8 { decode_x(self.0) }

    #[inline]
    pub const fn y(self) -> i8 { decode_y(self.0) }

    #[inline]
    pub const fn z(self) -> i8 { decode_z(self.0) }

    /// `true` iff the state is the geometric center.
    #[inline]
    pub const fn is_center(self) -> bool { self.0 == 13 }

    /// `true` for the 6 axial states (exactly one nonzero axis).
    pub const fn is_axial(self) -> bool {
        let (x, y, z) = (self.x(), self.y(), self.z());
        let n = (x != 0) as u8 + (y != 0) as u8 + (z != 0) as u8;
        n == 1
    }

    /// `true` for the 12 face-diagonal states (exactly two nonzero axes).
    pub const fn is_face_diag(self) -> bool {
        let (x, y, z) = (self.x(), self.y(), self.z());
        let n = (x != 0) as u8 + (y != 0) as u8 + (z != 0) as u8;
        n == 2
    }

    /// `true` for the 8 corner states (all three axes nonzero).
    pub const fn is_corner(self) -> bool {
        let (x, y, z) = (self.x(), self.y(), self.z());
        let n = (x != 0) as u8 + (y != 0) as u8 + (z != 0) as u8;
        n == 3
    }

    /// Hamming-style distance on the cube: number of axes that differ.
    pub fn distance(self, other: Cube) -> u8 {
        let dx = (self.x() - other.x()).unsigned_abs();
        let dy = (self.y() - other.y()).unsigned_abs();
        let dz = (self.z() - other.z()).unsigned_abs();
        dx + dy + dz
    }
}

/// Encode `(x, y, z)` with each in `-1..=1` to a `u8` index.
#[inline]
pub const fn encode(x: i8, y: i8, z: i8) -> u8 {
    ((x + 1) as u8) + 3 * ((y + 1) as u8) + 9 * ((z + 1) as u8)
}

#[inline]
pub const fn decode(idx: u8) -> (i8, i8, i8) {
    (decode_x(idx), decode_y(idx), decode_z(idx))
}

#[inline]
pub const fn decode_x(idx: u8) -> i8 { (idx % 3) as i8 - 1 }

#[inline]
pub const fn decode_y(idx: u8) -> i8 { ((idx / 3) % 3) as i8 - 1 }

#[inline]
pub const fn decode_z(idx: u8) -> i8 { (idx / 9) as i8 - 1 }

impl fmt::Debug for Cube {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Cube({:?})", (self.x(), self.y(), self.z()))
    }
}

impl fmt::Display for Cube {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({},{},{})", self.x(), self.y(), self.z())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn encode_decode_roundtrip() {
        for x in -1i8..=1 {
            for y in -1i8..=1 {
                for z in -1i8..=1 {
                    let idx = encode(x, y, z);
                    assert!((idx as usize) < N);
                    let (dx, dy, dz) = decode(idx);
                    assert_eq!((x, y, z), (dx, dy, dz));
                }
            }
        }
    }

    #[test]
    fn there_are_27_states() {
        assert_eq!(ALL.len(), 27);
        let mut seen = [false; 27];
        for c in ALL.iter() {
            seen[c.idx() as usize] = true;
        }
        assert!(seen.iter().all(|&b| b));
    }

    #[test]
    fn shape_classification_counts() {
        let mut ce = 0; let mut ax = 0; let mut fd = 0; let mut co = 0;
        for c in ALL.iter() {
            if c.is_center()      { ce += 1; }
            else if c.is_axial()  { ax += 1; }
            else if c.is_face_diag() { fd += 1; }
            else if c.is_corner() { co += 1; }
        }
        assert_eq!((ce, ax, fd, co), (1, 6, 12, 8));
    }

    #[test]
    fn distance_metric() {
        let a = Cube::new(0, 0, 0);
        let b = Cube::new(1, 0, 0);
        let c = Cube::new(1, 1, 0);
        let d = Cube::new(-1, -1, -1);
        assert_eq!(a.distance(b), 1);
        assert_eq!(a.distance(c), 2);
        assert_eq!(a.distance(d), 3);
        assert_eq!(b.distance(b), 0);
    }

    #[test]
    fn center_is_13() {
        assert_eq!(encode(0, 0, 0), 13);
        assert_eq!(Cube::new(0, 0, 0).idx(), 13);
    }
}
