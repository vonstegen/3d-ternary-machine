# Stage W5: permutation composition workload (the canonicalization flagship)

> The W5 workload tests whether BT-IS's first-class rotor
> registers and `COMPOSE_R` opcode give an instruction-count
> advantage on a *group-exercising* workload — applying a sequence
> of composed rotations to a cube state.

## The workload

Build R = R_a * R_b * R_a * R_c * R_a^-1 * R_b * R_c * R_a from
three base rotations and apply R to a cube state. The interesting
work is the *composition* (7 `COMPOSE_R` ops in BT-IS), not the
final application (1 op).

## ISA extension required

The v0.1.0 ISA had no way to load a literal permutation into a
rotor register. To make W5 expressible in BT-IS, the ISA was
extended with 13 new opcodes:

```
ROT_Z_90_R, ROT_Z_180_R, ROT_Z_270_R
ROT_X_90_R, ROT_X_180_R, ROT_X_270_R
ROT_Y_90_R, ROT_Y_180_R, ROT_Y_270_R
REFLECT_X_R, REFLECT_Y_R, REFLECT_Z_R
NEG_R
```

These apply a named cube-symmetry permutation *directly to a rotor
register* (`R[arg] := perm.then(R[arg])`), as opposed to applying
to `C`.

## Results

| implementation | mutating steps |
|----------------|---------------:|
| BT-IS (with COMPOSE_R, ROT_*_R, INVERSE_R) | 21 |
| SCALAR (with WCOMPOSE, WINVERT, WLOAD_PERM, WAPPLY) | 14 |
| SCALAR (manual composition via 27-step loop per compose) | 170 |

**Ratio BT-IS / SCALAR-fair: 1.50× (BT-IS is *slower*).**

## Interpretation

**BT-IS does *not* win on the composition workload.** With both
architectures given equivalent primitives (load-perm, invert,
compose, apply), SCALAR is *faster* by ~50%. The reason: BT-IS
pays setup overhead for each rotor register (5 `load_r` + 4
`ROT_*_R` ops = 9 ops), while SCALAR with a `wload_perm literal`
opcode can load a permutation in 1 op.

**The architectural claim "rotor registers give compositional
leverage" is *not* demonstrated by this workload.** Both
architectures have register-file rotors; both can compose them.
BT-IS has no first-mover advantage here.

## What this means for the verdict

This is an honest negative result on the canonicalization
flagship. The original hypothesis was that *group-exercising
workloads* would show BT-IS advantages over SCALAR. The W5
result: **no advantage when SCALAR is given equivalent
primitives**.

This shifts the verdict further toward "not worth pursuing":
the W4 (cube-add) and W5 (composition) workloads — the two
strongest natural cases for BT-IS — both show *no* advantage
when SCALAR is given fair primitives.

## What was tested

- BT-IS program: `programs/w5_compose.btis`
- Python reference: `benchmarks/w5_compose.py` (independent
  permutation composition)
- SCALAR counting: `benchmarks/w5_scalar.py` (instruction
  counts, since SCALAR doesn't have the primitives)

## How to reproduce

```bash
cargo run -- programs/w5_compose.btis
python3 benchmarks/w5_compose.py
python3 benchmarks/w5_scalar.py
```

The BT-IS program and Python reference both produce the cube
(0, -1, 0) for input (1, 0, 0). The instructions count is read
from `--trace` output.

## Conclusion

The canonicalization flagship (W5) **fails to confirm the
hypothesis**. BT-IS's rotor registers do not give an architectural
advantage on permutation-composition workloads when SCALAR is
given equivalent primitives.

This finding is *good* — it eliminates a false-positive
narrative that would have led to overclaiming. The verdict
shifts to: "BT-IS as specified is approximately equivalent to a
fair SCALAR baseline on cube-arithmetic and group-composition
workloads."

Further architectural advantages would need to come from a
*qualitatively different* primitive — not just an opcode
availability win.
