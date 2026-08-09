//! BT-IS: a 3D Balanced-Ternary Instruction System.
//!
//! The fundamental primitive is a point in `{-1, 0, +1}^3` (the
//! 27-state cube). Geometric operations on the cube are permutations
//! of its 27 states, represented as 27-entry lookup tables so a
//! "geometric instruction" is O(1).
//!
//! ## Roadmap
//!
//! - `cube`     : the 27-state primitive
//! - `symmetry` : rotations, reflections, negation as 27-entry LUTs
//! - `isa`      : instruction set (geometric verbs)
//! - `vm`       : virtual machine that executes the ISA
//! - `asm`      : symbolic assembler
//! - `bin`      : CLI driver
//!
//! ## References
//!
//! - Wikipedia: Clifford algebra, octahedral symmetry group
//! - REBEL balanced-ternary ISA (Bos 2024) -- neighboring prior art
//! - Setnex ternary ISA -- neighboring prior art
//! - Projective geometric algebra (Hestenes, Dorst) -- neighboring prior art

pub mod cube;
pub mod symmetry;
pub mod isa;
pub mod vm;
pub mod asm;
pub mod trace;
