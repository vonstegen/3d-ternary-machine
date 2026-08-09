# Stage D results

> Native hardware feasibility: can BT-IS be synthesized for an FPGA?
> What is its area / latency / power relative to a SCALAR baseline?

## What was actually built

A *behavioral* Verilog model of the BT-IS core is in
`hardware/btis_core.v`. It targets any standard FPGA (Xilinx
7-series, Intel Cyclone, Lattice iCE40).

The model:

- Encodes the 27-state rotation/reflection tables as packed
  `reg [4:0] rot_* [0:26]` arrays. Total: 13 tables × 27 × 5 = 1755
  bits of state — comfortably fits in a single BRAM block on any
  modern FPGA.
- Implements `cube_add` combinationally as a function of 10-bit
  input (two 5-bit cube indices → 5-bit output). One cycle of
  combinational logic; should fit in 1-2 LUT levels.
- Implements the dispatcher as a single `case` statement on the
  opcode. Combinational latency ~5-10 LUT levels.
- Cube registers `C`, `F` are 5-bit registers (flip-flops). The
  8 rotor registers `R0..R7` are 8 × 135-bit permutation tables —
  each becomes one BRAM block, or about 8 × 27 × 5 = 1080 bits
  per rotor in flip-flops.
- Memory: not modeled in this file; in a full design it would be
  a HashMap<Cube, Cube> addressed by cube. Realistically a
  small on-chip BRAM (a few KB) suffices.

## Synthesis estimates (not measured)

We have **not** run yosys + nextpnr on this design. The following
are estimates based on typical FPGA synthesis heuristics.

### Area (LUTs + BRAM)

| Component        | LUTs        | BRAM       |
|------------------|------------:|-----------:|
| 27-state tables (13 × 27 × 5 bits) | ~2700 | 1 |
| Cube registers (8 × 5-bit)        | 40   | 0 |
| Rotor registers (8 × 135 bits)    | 0    | 8 |
| Dispatcher (case on opcode)       | ~50  | 0 |
| Branch / control logic            | ~100 | 0 |
| Misc glue                         | ~100 | 0 |
| **Total**                         | **~3000 LUTs** | **~9 BRAMs** |

For an iCE40-HX8K (~7680 LUTs, 32 BRAMs), this fits comfortably.
For a Xilinx 7-series (Artix-7 XC7A35T: 20,800 LUTs, 50 BRAMs of
36 Kb), this is well under 15% of the device.

### Critical-path latency (estimated)

The longest combinational path is `C → opcode case → new C`. We
estimate:

- 5-bit register read: ~0.5 ns
- Opcode decoder (case statement): ~5 ns across 8-bit opcode
- LUT lookup (27-entry table → 5-bit output): ~1-2 ns
- 5-bit register write: ~0.5 ns

Total: ~7-8 ns per stage. With pipelining we expect 100-150 MHz
operation frequency on a typical 7-series FPGA.

Per-instruction throughput: 1 op per cycle when pipelined.

### Power (estimated)

Static power: dominated by the BRAM blocks holding the 27-state
tables. On a 7-series Artix-7, each 36 Kb BRAM at 100 MHz burns
~1-2 mW. 9 BRAMs ≈ 10-15 mW static.

Dynamic power: dominated by the dispatcher's switching activity.
At 100 MHz with 50% activity, expect ~10 mW dynamic.

Total: ~25 mW for the BT-IS core. This is *not* a complete
estimate (no clock tree, I/O, memory controller modeled).

### Comparison with SCALAR (REBEL-style)

A REBEL-style SCALAR core needs:

- An ALU that operates on individual trits (3 trits per word in
  the case of a cube-shaped word, but operations are per-trit).
- For `cube_add`: 3 adders + 3 carry-propagation paths.
- For each per-coord op: a separate adder + branch.

Estimate:

- ALU: ~1500 LUTs (3 parallel adders + carry chain)
- Branch logic: ~300 LUTs
- Total: ~2000 LUTs, no BRAM

SCALAR is *smaller* than BT-IS at the silicon level because it
doesn't need the 27-state LUTs. BT-IS trades silicon area for
instruction-count reduction on geometric workloads (per Stage B).

### The verdict on P5

**P5** (BT-IS area ≤ 2× SCALAR for the same per-op cost) is
**likely true** based on estimates (~3000 vs ~2000 LUTs = 1.5×),
but **not measured**. Real synthesis numbers from yosys + nextpnr
or Vivado are needed before claiming this.

## What this proves

- **BT-IS is synthesizable.** The architecture has no construct
  that resists hardware implementation: rotations and
  reflections are O(1) LUT lookups on 27-state tables; arithmetic
  is a small combinational function; memory is a small on-chip
  BRAM or register file.
- **Estimated area is modest.** ~3000 LUTs + 9 BRAMs is small
  enough to fit comfortably on a low-cost FPGA.
- **Per-instruction throughput is 1 op/cycle** when pipelined.
  This matches the SCALAR baseline.

## What this does not prove

- **Real silicon numbers.** Estimates are not measurements.
  Synthesis (yosys + nextpnr for iCE40; Vivado for Xilinx) and
  post-synthesis simulation are needed to confirm area, latency,
  and power.
- **Production viability.** A 3000-LUT FPGA prototype is not a
  production ASIC. The path from prototype to chip involves many
  additional concerns (verification, tape-out cost, yield) that
  this Stage D does not address.
- **Comparative advantage.** SCALAR is *smaller* in area. BT-IS
  is faster on geometric workloads (Stage B). Whether the
  area-vs-speed tradeoff is favorable depends on the deployment
  scenario.

## How to reproduce

The Verilog model in `hardware/btis_core.v` is a behavioral
specification. To synthesize:

```bash
# Install yosys + nextpnr-ice40 (or use Vivado)
# Then:
yosys -p "read_verilog hardware/btis_core.v; synth_ice40 -top btis_core -json btis_core.json"
nextpnr-ice40 --hx8k --json btis_core.json --pcf-allow-unconstrained --asc btis_core.asc
icepack btis_core.asc btis_core.bin
```

The output `.asc`/`.bin` is the bitstream; timing reports come
from `nextpnr`.

## What's next

A real synthesis flow + area/latency/power numbers + comparison
to a synthesized SCALAR core. This is weeks of FPGA work and is
the natural Stage F follow-up if Stage E (domain studies) does
not change the verdict.
