#!/usr/bin/env bash
# benchmarks/bench.sh -- measure BT-IS VM throughput.
#
# Runs a small rotation program N times and reports total elapsed time.
# Each program run executes ~6 instructions (load + 4 rotations + halt).
set -e
cd "$(dirname "$0")/.."

N=${1:-10000}
PROG=programs/bench_rot.btis
BTIS_BIN=./target/release/btis

# Build release binary once.
cargo build --release --quiet

# Warmup.
"$BTIS_BIN" "$PROG" > /dev/null

start=$(date +%s%N)
for ((i=0; i<N; i++)); do
    "$BTIS_BIN" "$PROG" > /dev/null
done
end=$(date +%s%N)

elapsed_ns=$((end - start))
elapsed_ms=$((elapsed_ns / 1000000))
per_run_us=$((elapsed_ns / N / 1000))
total_instrs=$((N * 6))
ips=$((total_instrs * 1000000000 / elapsed_ns))

echo "BT-IS benchmark"
echo "  program:     $PROG"
echo "  iterations:  $N"
echo "  total time:  ${elapsed_ms} ms"
echo "  per run:     ${per_run_us} us"
echo "  total instr: $total_instrs"
echo "  throughput:  $ips instructions/sec"
