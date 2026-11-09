#!/usr/bin/env bash
# Poora benchmark: build -> data -> har variant 3 runs (CPU 2 par pinned) -> analyze.
# Throw-away benchmark. Koi network/broker connection nahi.
set -euo pipefail
cd "$(dirname "$0")"
RUNS=${RUNS:-3}
PIN=${PIN:-"taskset -c 2"}
command -v taskset >/dev/null || PIN=""

echo "== build =="
(cd rust && RUSTFLAGS="-C target-cpu=native" cargo build --release -q)
mkdir -p cpp/build && g++ -O2 -march=native -ffp-contract=off -o cpp/build/tickbench cpp/main.cpp
if command -v go >/dev/null; then (cd go && mkdir -p bin && go build -o bin/tickbench .); fi

echo "== data =="
[ -f data/ticks.bin ] && [ -f data/ticks.ndjson ] || python3 gen.py

rm -rf out && mkdir -p out
run() {   # run <variant-name> <command...>   (command ko last arg ke roop mein out dir milta hai via {OUT})
  local name=$1; shift
  for r in $(seq 1 "$RUNS"); do
    local o="out/$name/run$r"; mkdir -p "$o"
    echo "-- $name run$r"
    eval "$PIN ${*//\{OUT\}/$o}" > /dev/null
  done
}
run py_plain_bin_gc-on            python3 py_plain.py --data data --out {OUT} --gc on
run py_plain_bin_gc-freeze        python3 py_plain.py --data data --out {OUT} --gc freeze
run py_plain_bin_hist_gc-on       python3 py_plain.py --data data --out {OUT} --gc on --keep-history
run py_plain_bin_hist_gc-freeze   python3 py_plain.py --data data --out {OUT} --gc freeze --keep-history
run py_plain_json_stdlib          python3 py_plain.py --data data --out {OUT} --format json --json-lib json
run py_plain_json_orjson          python3 py_plain.py --data data --out {OUT} --format json --json-lib orjson
run py_numpy_bin                  python3 py_numpy.py --data data --out {OUT} --engine numpy
run py_numba_bin                  python3 py_numpy.py --data data --out {OUT} --engine numba
run rust_bin                      rust/target/release/tickbench data {OUT} bin
run rust_json                     rust/target/release/tickbench data {OUT} json
run cpp_bin                       cpp/build/tickbench data {OUT}
if [ -x go/bin/tickbench ]; then
  run go_bin                      go/bin/tickbench data {OUT} bin
  run go_json                     go/bin/tickbench data {OUT} json
fi

echo "== analyze =="
python3 analyze.py out data | tee out/report.md
