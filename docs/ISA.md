# BT-IS ISA Reference

## 1. The cube: the fundamental primitive

A single machine symbol in BT-IS is a point in

```
{-1, 0, +1}^3
```

which has exactly **27** elements. We call this the *cube*. Each point is a
triple `(x, y, z)` where each coordinate is balanced-ternary.

The 27 states decompose geometrically:

| class          | count | example                    |
|----------------|------:|----------------------------|
| center         | 1     | `(0,0,0)`                  |
| axial          | 6     | `(±1,0,0)`, `(0,±1,0)`, `(0,0,±1)` |
| face-diagonal  | 12    | `(±1,±1,0)` + permutations |
| corner         | 8     | `(±1,±1,±1)`               |
| **total**      | **27**|                            |

This decomposition is *the* source of instruction semantics: axial
states are primitive operations, face-diagonals are coupled operations,
corners are three-way combined operations, the center is identity / halt.

A cube packs into a single `u8`: index `i = (x+1) + 3*(y+1) + 9*(z+1)`.
The center is `i = 13`.

## 2. Register file

| reg | type     | role                                            |
|-----|----------|-------------------------------------------------|
| `C` | `Cube`   | the *cursor* — the program's current cube state |
| `F` | `Cube`   | flag vector: `(gt, eq, lt)` from last `CMP`     |
| `IP`| `usize`  | instruction pointer                             |
| `mem` | `HashMap<Cube, Cube>` | memory addressed by cube coordinates |

There are no integer registers. Integer values are encoded in `C.x` as a
balanced-ternary digit in `{-1, 0, +1}`. Saturating arithmetic.

## 3. Instruction encoding

Each instruction is `(opcode: u8, arg: i8, target: usize)`.

Opcode ranges:

| range       | purpose                              |
|-------------|--------------------------------------|
| 0..32       | data movement / I/O                  |
| 32..56      | rotations (apply rotation to C)      |
| 56..64      | reflections / inversion              |
| 64..96      | arithmetic                           |
| 96..128     | comparison, branching                |
| 128..160    | memory                               |
| 192..       | control (HALT = 192)                 |

The `arg` field carries the immediate operand (for `LOADC`, `IADD`,
`CMP`, `STORE`, `LOAD`, `LOAD_AXIS`). The `target` field carries the
jump target for branch instructions.

## 4. Instruction set

| mnemonic      | opcode  | effect                                                   |
|---------------|---------|----------------------------------------------------------|
| `nop`         | 0       | no-op                                                    |
| `loadc n`     | 1       | `C := Cube(n,n,n)`, `n ∈ {-1,0,+1}`                     |
| `load_axis k` | 2       | `C := unit_axis(k)` for `k ∈ {X,XI,Y,YI,Z,ZI}`          |
| `outc`        | 4       | emit `C` as a cube                                       |
| `outi`        | 3       | emit `C.x` as a signed integer                           |
| `rot_x_90`    | 35      | `C := R_x_90(C)`                                         |
| `rot_x_180`   | 36      | `C := R_x_180(C)`                                        |
| `rot_x_270`   | 37      | `C := R_x_270(C)`                                        |
| `rot_y_90`    | 38      | `C := R_y_90(C)`                                         |
| `rot_y_180`   | 39      | `C := R_y_180(C)`                                        |
| `rot_y_270`   | 40      | `C := R_y_270(C)`                                        |
| `rot_z_90`    | 32      | `C := R_z_90(C)`                                         |
| `rot_z_180`   | 33      | `C := R_z_180(C)`                                        |
| `rot_z_270`   | 34      | `C := R_z_270(C)`                                        |
| `reflect_x`   | 56      | `C := (-C.x, C.y, C.z)`                                  |
| `reflect_y`   | 57      | `C := (C.x, -C.y, C.z)`                                  |
| `reflect_z`   | 58      | `C := (C.x, C.y, -C.z)`                                  |
| `neg`         | 59      | `C := -C`                                                |
| `iadd n`      | 64      | `C.x := clamp(C.x + n, -1, +1)`                          |
| `isub n`      | 65      | `C.x := clamp(C.x - n, -1, +1)`                          |
| `imul n`      | 66      | `C.x := clamp(C.x * n, -1, +1)`                          |
| `cmp n`       | 96      | `F := sign(C.x - n)` ∈ `{(1,0,0),(0,1,0),(0,0,1)}`      |
| `br_neg L`    | 97      | if `F.x < 0`: jump to label `L`                          |
| `br_zero L`   | 98      | if `F.x == 0`: jump to label `L`                         |
| `br_pos L`    | 99      | if `F.x > 0`: jump to label `L`                          |
| `jmp L`       | 100     | unconditional jump to label `L`                           |
| `store n`     | 128     | `mem[Cube(n,n,n)] := C`                                  |
| `load n`      | 129     | `C := mem[Cube(n,n,n)]` (default `Cube::CENTER` if unset)|
| `halt`        | 192     | stop execution                                           |

## 5. Symbolic assembler

A `.btis` source file is a sequence of lines:

```
line      := label | instr
label     := "label" IDENT
instr     := MNEMONIC OPERAND?
OPERAND   := INT | IDENT
IDENT     := [A-Za-z_][A-Za-z0-9_.]*
```

`INT` is a small signed integer in `{-1, 0, +1}`.
For `load_axis`, the `IDENT` is one of `X XI Y YI Z ZI`.
For branch / jump instructions, the `IDENT` is a label.

Comments start with `;` and run to end of line.

### Example: countdown

```btis
loadc 1
label loop
outi
cmp -1
br_zero done
isub 1
jmp loop
label done
halt
```

Emits `1`, `0`, `-1`, then halts.

### Example: rotation trajectory

```btis
load_axis X
rot_z_90
rot_x_90
reflect_x
neg
outc
halt
```

Starts at `(1,0,0)`. The trajectory is:

```
(1,0,0) ── rot_z_90 ──▶ (0,1,0) ── rot_x_90 ──▶ (0,0,1)
   ── reflect_x ──▶ (0,0,1) ── neg ──▶ (0,0,-1)
```

Emits `CUBE (0,0,-1)`. The program is a path in the 27-cube.

## 6. CLI

```
btis <source.btis> [--trace]
```

* assembles the source,
* executes the program,
* prints emitted values (`INT n` or `CUBE (x,y,z)`) one per line.

`--trace` prints a per-step snapshot to stderr before execution runs.

## 7. Execution semantics

* The VM is a stack/register hybrid.
* `IP` advances by 1 each step unless a branch overwrites it.
* `HALT` sets `halted = true` and the VM stops.
* Memory addresses are cube coordinates; two memory writes to different
  cube coordinates are independent. There is no aliasing by construction.

## 8. Numerical model

* Integer arithmetic saturates at `{-1, +1}` (balanced ternary overflow).
* `CMP` produces a 3-valued sign: `(-1, 0, +1)`. This is the
  architectural realization of *three-way branching* — a property of the
  cube's natural balanced-ternary geometry.
* No floating-point types. This is intentional: the cube's coordinates
  are discrete by design.

## 9. Implementation notes

* Each cube rotation is a 27-entry lookup table. Applying a rotation is
  `O(1)` — a single array index.
* The 24 orientation-preserving rotations of the cube (octahedral group
  `O`) are all available; the 24 reflection-rotations (full octahedral
  group `O_h`, size 48) can be derived as compositions of the existing
  reflections.
* The Python prototype at `vrml_proto/python/` provides a continuous
  geometric-algebra relaxation of the cube (rotors over reals). It is
  not the machine — it is a sanity reference. The real machine is the
  27-state discrete cube.
