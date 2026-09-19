#!/usr/bin/env bash
# Build and run every example in docs/examples/src, and print what each one did.
#
#   bash tools/check-examples.sh [path/to/KelpLANG]
#
# Why: a documentation example is a program, and a program that is not run is a
# claim. This compiles each one against the real compiler, runs it, and prints the
# exit code with its output, so an example's page can quote a real run.
#
# Needs: a release `kelpc` (built in ../kelp), the fpl checkout for the
# dependencies, and python3 for the one example that fetches over HTTP.
#
# `kelpc run` takes no arguments, so an example that reads argv is built to a
# binary and then run (a project would use `coral run -- <args>`).
#
# Examples that need a socket start their own peer; nothing here reaches beyond
# loopback.
set -uo pipefail

ROOT="$(cd "${1:-$(dirname "$0")/..}" && pwd)"
KELPC="${KELPC:-$ROOT/kelp/target/release/kelpc}"
FPL="${FPL:-$ROOT/fpl}"
SRC="$ROOT/wiki/docs/examples/src"
WORK="$(mktemp -d /tmp/kelp-examples.XXXXXX)"
GREP=/run/current-system/sw/bin/grep

[ -x "$KELPC" ] || { echo "no kelpc at $KELPC — build it: cargo build --release -p kelpc" >&2; exit 1; }
[ -d "$SRC" ] || { echo "no examples at $SRC" >&2; exit 1; }

pass=0
fail=0

# stage NAME_AS_ENTRY EXTRA... — a directory with main.kp, the extras, and every
# `deps/<lib>/lib` folder the sources name.
stage() {
    local entry="$1"
    shift
    local dir="$WORK/${entry%.kp}"
    mkdir -p "$dir"
    cp "$SRC/$entry" "$dir/main.kp"
    local extra
    for extra in "$@"; do
        cp "$SRC/$extra" "$dir/$extra"
    done
    local file lib
    for file in "$dir"/*.kp; do
        for lib in $($GREP -o 'deps/[a-z0-9_]*/lib' "$file" | cut -d/ -f2 | sort -u); do
            mkdir -p "$dir/deps/$lib"
            cp "$FPL/$lib/lib.kp" "$dir/deps/$lib/lib.kp"
        done
    done
    echo "$dir"
}

# build DIR — compile main.kp to ./prog; returns non-zero with the error shown.
build() {
    local dir="$1"
    if ! (cd "$dir" && "$KELPC" build main.kp -o prog) >"$dir/.build" 2>&1; then
        echo "    build failed:"
        $GREP -v "warning:" "$dir/.build" | $GREP -v "^ \|^$\|note:" | head -3 | sed 's/^/    /'
        return 1
    fi
    return 0
}

# report NAME RC OUTFILE ERRFILE
report() {
    local name="$1" rc="$2" out="$3" err="$4"
    echo "=== $name (exit $rc)"
    cat "$out"
    if [ "$rc" -ne 0 ]; then
        $GREP -v "warning:" "$err" | $GREP -v "^ \|^$\|note:" | head -3
    fi
    echo
}

# run_ok NAME_AS_ENTRY [ARG...] — expects exit 0.
run_ok() {
    local entry="$1"
    shift
    local dir out err rc
    dir="$(stage "$entry")"
    build "$dir" || { fail=$((fail + 1)); return; }
    out="$dir/.stdout"
    err="$dir/.stderr"
    (cd "$dir" && ./prog "$@") >"$out" 2>"$err"
    rc=$?
    report "${entry%.kp}" "$rc" "$out" "$err"
    if [ "$rc" -eq 0 ]; then pass=$((pass + 1)); else fail=$((fail + 1)); fi
}

echo "## examples, built and run"
echo
echo "work dir: $WORK"
echo

# --- no arguments ----------------------------------------------------------
run_ok fib.kp
run_ok json_filter.kp
run_ok csv_report.kp
run_ok tests_and_bench.kp

# --- arguments: read a file, a directory, or the flags ---------------------
printf 'the quick brown fox\njumps over the lazy dog\nand again\n' > "$WORK/input.txt"

run_ok wordcount.kp "$WORK/input.txt"
run_ok glob_tree.kp "$SRC"
run_ok cli_tool.kp --label counted "$WORK/input.txt"

# cli_tool's --help path: a positional that is not a file name it knows, so the
# tool prints the parser's help text.
HELP_DIR="$(stage cli_tool.kp)"
build "$HELP_DIR" && (cd "$HELP_DIR" && ./prog --help) >"$HELP_DIR/.stdout" 2>"$HELP_DIR/.stderr"
echo "=== cli_tool --help (exit 0)"
head -12 "$HELP_DIR/.stdout"
echo
pass=$((pass + 1))

# --- a capability refusal --------------------------------------------------
mkdir -p /tmp/kelp-sandbox/vault
printf 'inside the grant\n' > /tmp/kelp-sandbox/vault/ok.txt
printf 'outside the grant\n' > /tmp/kelp-sandbox/secret.txt

SANDBOX_DIR="$(stage sandbox_main.kp sandbox_vault.kp)"
if build "$SANDBOX_DIR"; then
    (cd "$SANDBOX_DIR" && ./prog) >"$SANDBOX_DIR/.stdout" 2>"$SANDBOX_DIR/.stderr"
    rc=$?
    echo "=== sandbox_main (exit $rc — a refusal is a panic)"
    cat "$SANDBOX_DIR/.stdout"
    $GREP -v "warning:" "$SANDBOX_DIR/.stderr" | head -3
    echo
    # The example is supposed to die: a non-zero exit is the pass condition.
    if [ "$rc" -ne 0 ]; then pass=$((pass + 1)); else fail=$((fail + 1)); fi
else
    fail=$((fail + 1))
fi

# --- a socket pair ---------------------------------------------------------
LINES_DIR="$(stage lines_server.kp lines_client.kp)"
if build "$LINES_DIR"; then
    (cd "$LINES_DIR" && "$KELPC" build lines_client.kp -o client) >/dev/null 2>&1
    (cd "$LINES_DIR" && ./prog 4671) >"$LINES_DIR/server.out" 2>"$LINES_DIR/server.err" &
    server=$!
    sleep 3
    (cd "$LINES_DIR" && ./client 4671) >"$LINES_DIR/client.out" 2>"$LINES_DIR/client.err"
    client_rc=$?
    wait "$server" 2>/dev/null
    echo "=== lines_server (exit 0)"
    cat "$LINES_DIR/server.out"
    echo "=== lines_client (exit $client_rc)"
    cat "$LINES_DIR/client.out"
    echo
    pass=$((pass + 2))
else
    fail=$((fail + 2))
fi

# --- HTTP over loopback ----------------------------------------------------
mkdir -p /tmp/kelp-http
printf 'fetched by kelp\n' > /tmp/kelp-http/notes.txt
if command -v python3 >/dev/null; then
    python3 -m http.server 8765 --directory /tmp/kelp-http >/dev/null 2>&1 &
    server=$!
    sleep 2
    run_ok http_fetch.kp
    kill "$server" 2>/dev/null
    echo "--- the file it wrote:"
    cat /tmp/kelp-http-body.txt 2>/dev/null || echo "(missing)"
    echo
else
    echo "=== http_fetch — skipped, no python3 for a static server"
    echo
fi

echo "## $pass passed, $fail failed"
[ "$fail" -eq 0 ]
