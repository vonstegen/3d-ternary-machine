# Stage D results — synthesis status

## What was estimated

`docs/STAGE_D_RESULTS.md` (committed earlier) contains the
behavioral Verilog model and area *estimates*:

- ~3000 LUTs + 9 BRAMs on a low-cost FPGA
- ~1.5× the SCALAR baseline's area

## What is missing: real synthesis numbers

Step 5 of Claude's 6-step plan called for running the
synthesis flow to convert estimates into measurements. That step
is blocked:

- yosys is not installed on this machine.
- nextpnr-ice40 (or nextpnr-ecp5) is not installed.
- Installation requires root privileges (sudo apt-get install
  yosys); the environment does not grant sudo.

When synthesis tools become available, the expected workflow is:

```bash
# Install (needs sudo):
#   sudo apt-get install yosys
#   # nextpnr-ice40 or nextpnr-ecp5 from source or pip

yosys -p 'read_verilog hardware/btis_core.v;
          synth_ice40 -top btis_core -json btis_core.json'
nextpnr-ice40 --hx8k --json btis_core.json \
              --pcf-allow-unconstrained --asc btis_core.asc
icepack btis_core.asc btis_core.bin
```

The post-synthesis report will give actual LUT / BRAM / timing
numbers. Until then, Stage D's numbers are estimates.

## Status

- Stage D: estimates only (committed earlier).
- Step 5: blocked on environment.

This is an *environmental* blocker, not a research blocker.
When tools are available, the workflow is one afternoon of work.
