---
title: "Benchmarks: Kelp against C and Rust"
description: "A thirteen-program suite written three times in Kelp, C and Rust with checked checksums: the rules, the machine and its noise, the full tables, why every ratio above 1.5 is what it is, the str.split bug it found, and what is still open."
isPublished: true
tags: "tooling, benchmarks, performance"
---
`bench/` in the compiler repository is a suite that answers one question with
numbers: how fast is the code `kelpc` makes, next to C and Rust doing the same
work? Thirteen programs, each written three times (`bench/suite/<name>/<name>.kp`,
`.c` and `.rs`) with the same algorithm, each printing the same checksum line, and
`bench/run.sh` builds and times them and writes `bench/RESULTS.md`. This page is
the method, the numbers as recorded, and the honest account of every cell that
is not close to C. (A different, older three-language suite with a different
method is described under [Compiler benchmarks](/compiler/benchmarks).)

## Rules

- **Same algorithm, same output.** Each benchmark takes its size as the first
  command-line argument (the default is the full size) and prints one checksum
  line. A row's `checksum` column compares the program's stdout with the gcc C
  version's on every run; a program that prints different bytes is not timed as
  if it did the same work. In the tables below every row says `ok`.
- **Idiomatic, not heroic.** No SIMD intrinsics, no `unsafe` tricks in Rust beyond
  what plain code needs, no `-march=native`, no `-ffast-math`.
- **Bounds checks.** On in Kelp (both backends) and on in Rust (indexing), off in
  C. This is a stated asymmetry in C's favour: every ratio is against a C program
  that checks nothing.
- **Compilers and flags.** C: `cc -O2` (gcc 15.3.0). Rust: `rustc -C opt-level=3`
  (rustc 1.95.0, no cargo, no LTO). Kelp: `kelpc build -O2` on the default LLVM
  backend (`kelp-llvm`) and with `KELPC_ORACLE=c` (`kelp-c`, the C oracle backend,
  compiled by the same `cc -O2`). There is no clang on the machine, so there are
  no clang rows.
- **Measurement.** Each program is built 3 times (median build time), run once as
  a discarded warm-up, then 7 timed runs at the full default size, each under
  `( ulimit -v 4194304; ulimit -t 300; timeout 300 time nice -n 0 ... )`. Wall
  time is read around the whole wrapper (about 7.6 ms of `timeout`, `time` and
  `nice`, measured on `/bin/true` and included in every number, 7% of the
  fastest cells). Peak resident set size comes from GNU `time`.
- **The sizes.** `fib` is `fib(38)`, `nbody` 5,000,000 steps, `spectral-norm`
  n = 1000, `strings` 1,000,000 pieces; the others are fixed in their source
  headers. The runs are therefore short (0.08 s to 0.9 s).
- **Not a library comparison, except where said.** The C `hashmap` is a
  hand-written open-addressing table inside the benchmark file (C has no hash
  map); Kelp uses its builtin `Map<u64, u64>` and Rust its std `HashMap`
  (SipHash). `sort` is the same hand-written quicksort in all three languages;
  `sort-builtin` compares each language's own sort (Kelp `List.sort`, C `qsort`
  with a comparator callback, Rust `sort_unstable`).

## The machine and the noise

Intel Core i5-6500T at 2.50 GHz, 4 logical CPUs, 7.6 GB of memory and 10 GB of
swap, Linux 6.18.54 x86_64, `kelpc 26.09.5` (commit `cd7f4fd`). The run was made
on 2026-10-03.

**The host was never idle.** It is a shared machine: other builds and a game
server ran on it throughout, and none of it was stopped or throttled. The
1-minute load average was between 2.3 and 3.7 during both full runs. The load
average was read before and after each block of runs, and a row would be flagged
`NOISY` if it changed by more than 1.0; none was, but the absolute level means
every number is for a shared 4-core machine. Within one run the seven samples of
a cell agree to 1-3%. Between two runs, cells the library change could not touch
moved by up to 9% (`fib` on `kelp-llvm` from 0.154 s to 0.140 s, `sort` from
0.700 s to 0.661 s), so a difference of about 5% between two rows is inside what
this host does to a repeated measurement. Peak memory stayed small (the largest
cell in either run is 104 MB, Rust's `hashmap`), so no size was scaled down.

## Results

Two full runs were made with the same sources, machine and unchanged `run.sh`.
The **first run** was made before any compiler or library change and is the
baseline; the **second run** is the one below and was made after one library
change ([what was fixed](#what-the-suite-found-and-fixed)). Ratios are wall time
divided by the gcc -O2 C time, so `1.00` is C and below `1.00` is faster than C.

### Summary, second run

| benchmark | c-gcc | rust | kelp-llvm | kelp-c |
| --- | ---: | ---: | ---: | ---: |
| fib | 1.00 | 1.51 | 1.24 | 1.01 |
| nbody | 1.00 | 0.58 | 0.87 | 1.16 |
| spectral-norm | 1.00 | 0.97 | 0.98 | 1.71 |
| mandelbrot | 1.00 | 0.98 | 0.99 | 1.01 |
| binary-trees | 1.00 | 1.13 | 1.06 | 1.07 |
| fannkuch-redux | 1.00 | 1.04 | 1.28 | 1.03 |
| sieve | 1.00 | 1.09 | 1.14 | 1.13 |
| matmul | 1.00 | 1.28 | 1.08 | 1.06 |
| strings | 1.00 | 1.25 | 1.84 | 1.89 |
| hashmap | 1.00 | 2.66 | 1.88 | 2.29 |
| sort | 1.00 | 1.06 | 1.32 | 1.51 |
| sort-builtin | 1.00 | 0.18 | 0.35 | 0.42 |
| json-tokenizer | 1.00 | 0.87 | 1.27 | 1.41 |

### Baseline (first run), same table

| benchmark | c-gcc | rust | kelp-llvm | kelp-c |
| --- | ---: | ---: | ---: | ---: |
| fib | 1.00 | 1.51 | 1.37 | 1.03 |
| nbody | 1.00 | 0.58 | 0.89 | 1.14 |
| spectral-norm | 1.00 | 0.96 | 0.96 | 1.67 |
| mandelbrot | 1.00 | 0.98 | 1.00 | 1.02 |
| binary-trees | 1.00 | 1.15 | 1.07 | 1.09 |
| fannkuch-redux | 1.00 | 1.04 | 1.31 | 0.99 |
| sieve | 1.00 | 1.07 | 1.10 | 1.08 |
| matmul | 1.00 | 1.27 | 1.05 | 1.05 |
| strings | 1.00 | 1.25 | TIMEOUT(300s limit) | TIMEOUT(300s limit) |
| hashmap | 1.00 | 2.94 | 1.92 | 2.29 |
| sort | 1.00 | 1.06 | 1.33 | 1.51 |
| sort-builtin | 1.00 | 0.18 | 0.36 | 0.43 |
| json-tokenizer | 1.00 | 0.89 | 1.59 | 1.59 |

In the baseline `strings` did not finish: `str.split` was quadratic and both Kelp
backends hit the 300 s limit. `json-tokenizer` (1.59 to 1.27) also used the number-to-text function that was
fixed; the other cells differ by the host's run-to-run drift.

### Wall time, second run

The `load` column is the 1-minute load average before and after that block of runs.

| benchmark | variant | median (s) | min | max | ratio to C (gcc) | checksum | load |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| fib | c-gcc | 0.113 | 0.113 | 0.115 | 1.00 | ok | load 3.07 to 3.07 |
| fib | rust | 0.171 | 0.170 | 0.172 | 1.51 | ok | load 3.07 to 3.07 |
| fib | kelp-llvm | 0.140 | 0.140 | 0.145 | 1.24 | ok | load 2.99 to 2.99 |
| fib | kelp-c | 0.115 | 0.114 | 0.116 | 1.01 | ok | load 2.91 to 2.91 |
| nbody | c-gcc | 0.430 | 0.423 | 0.443 | 1.00 | ok | load 2.91 to 2.91 |
| nbody | rust | 0.249 | 0.247 | 0.256 | 0.58 | ok | load 2.91 to 2.84 |
| nbody | kelp-llvm | 0.374 | 0.373 | 0.380 | 0.87 | ok | load 2.77 to 2.77 |
| nbody | kelp-c | 0.497 | 0.486 | 0.506 | 1.16 | ok | load 2.79 to 2.73 |
| spectral-norm | c-gcc | 0.081 | 0.080 | 0.082 | 1.00 | ok | load 2.73 to 2.73 |
| spectral-norm | rust | 0.079 | 0.077 | 0.080 | 0.97 | ok | load 2.73 to 2.75 |
| spectral-norm | kelp-llvm | 0.079 | 0.079 | 0.080 | 0.98 | ok | load 2.75 to 2.75 |
| spectral-norm | kelp-c | 0.138 | 0.138 | 0.139 | 1.71 | ok | load 2.77 to 2.77 |
| mandelbrot | c-gcc | 0.115 | 0.115 | 0.116 | 1.00 | ok | load 2.79 to 2.79 |
| mandelbrot | rust | 0.113 | 0.113 | 0.114 | 0.98 | ok | load 2.79 to 2.79 |
| mandelbrot | kelp-llvm | 0.114 | 0.114 | 0.115 | 0.99 | ok | load 2.89 to 2.89 |
| mandelbrot | kelp-c | 0.116 | 0.115 | 0.116 | 1.01 | ok | load 2.82 to 2.82 |
| binary-trees | c-gcc | 0.383 | 0.371 | 0.444 | 1.00 | ok | load 2.82 to 2.91 |
| binary-trees | rust | 0.432 | 0.430 | 0.436 | 1.13 | ok | load 2.91 to 2.92 |
| binary-trees | kelp-llvm | 0.404 | 0.402 | 0.406 | 1.06 | ok | load 3.00 to 3.00 |
| binary-trees | kelp-c | 0.409 | 0.406 | 0.414 | 1.07 | ok | load 3.08 to 3.08 |
| fannkuch-redux | c-gcc | 0.258 | 0.258 | 0.259 | 1.00 | ok | load 3.08 to 3.08 |
| fannkuch-redux | rust | 0.268 | 0.267 | 0.271 | 1.04 | ok | load 2.99 to 2.99 |
| fannkuch-redux | kelp-llvm | 0.330 | 0.328 | 0.331 | 1.28 | ok | load 2.91 to 2.91 |
| fannkuch-redux | kelp-c | 0.265 | 0.264 | 0.266 | 1.03 | ok | load 2.84 to 2.77 |
| sieve | c-gcc | 0.432 | 0.431 | 0.439 | 1.00 | ok | load 2.77 to 2.71 |
| sieve | rust | 0.472 | 0.463 | 0.474 | 1.09 | ok | load 2.71 to 2.73 |
| sieve | kelp-llvm | 0.494 | 0.481 | 0.512 | 1.14 | ok | load 2.73 to 2.75 |
| sieve | kelp-c | 0.487 | 0.462 | 0.497 | 1.13 | ok | load 2.77 to 2.79 |
| matmul | c-gcc | 0.103 | 0.102 | 0.104 | 1.00 | ok | load 2.79 to 2.79 |
| matmul | rust | 0.131 | 0.129 | 0.132 | 1.28 | ok | load 2.79 to 2.79 |
| matmul | kelp-llvm | 0.111 | 0.108 | 0.113 | 1.08 | ok | load 2.81 to 2.81 |
| matmul | kelp-c | 0.109 | 0.106 | 0.113 | 1.06 | ok | load 2.83 to 2.83 |
| strings | c-gcc | 0.122 | 0.120 | 0.126 | 1.00 | ok | load 2.83 to 2.92 |
| strings | rust | 0.151 | 0.151 | 0.152 | 1.25 | ok | load 2.92 to 2.92 |
| strings | kelp-llvm | 0.224 | 0.219 | 0.227 | 1.84 | ok | load 2.93 to 2.93 |
| strings | kelp-c | 0.230 | 0.228 | 0.238 | 1.89 | ok | load 2.93 to 2.93 |
| hashmap | c-gcc | 0.171 | 0.169 | 0.174 | 1.00 | ok | load 2.86 to 2.86 |
| hashmap | rust | 0.454 | 0.450 | 0.460 | 2.66 | ok | load 2.86 to 2.79 |
| hashmap | kelp-llvm | 0.322 | 0.319 | 0.323 | 1.88 | ok | load 2.73 to 2.73 |
| hashmap | kelp-c | 0.391 | 0.388 | 0.394 | 2.29 | ok | load 2.67 to 2.61 |
| sort | c-gcc | 0.503 | 0.501 | 0.504 | 1.00 | ok | load 2.61 to 2.61 |
| sort | rust | 0.535 | 0.534 | 0.539 | 1.06 | ok | load 2.56 to 2.52 |
| sort | kelp-llvm | 0.661 | 0.658 | 0.664 | 1.32 | ok | load 2.52 to 2.48 |
| sort | kelp-c | 0.759 | 0.752 | 0.792 | 1.51 | ok | load 2.44 to 2.40 |
| sort-builtin | c-gcc | 0.876 | 0.859 | 0.901 | 1.00 | ok | load 2.40 to 2.34 |
| sort-builtin | rust | 0.154 | 0.152 | 0.160 | 0.18 | ok | load 2.34 to 2.34 |
| sort-builtin | kelp-llvm | 0.311 | 0.303 | 0.320 | 0.35 | ok | load 2.31 to 2.29 |
| sort-builtin | kelp-c | 0.365 | 0.363 | 0.367 | 0.42 | ok | load 2.29 to 2.26 |
| json-tokenizer | c-gcc | 0.077 | 0.076 | 0.079 | 1.00 | ok | load 2.26 to 2.26 |
| json-tokenizer | rust | 0.068 | 0.067 | 0.069 | 0.87 | ok | load 2.24 to 2.24 |
| json-tokenizer | kelp-llvm | 0.098 | 0.097 | 0.099 | 1.27 | ok | load 2.24 to 2.22 |
| json-tokenizer | kelp-c | 0.110 | 0.107 | 0.113 | 1.41 | ok | load 2.22 to 2.22 |

Peak resident set size, stripped binary size and build time are tables of their
own in `bench/RESULTS.md`. Two things worth knowing from them: Kelp's
`binary-trees` peaks at 18.2 MB against 10.1 MB for C (1.81x), and a Kelp build
takes 1.1 to 1.5 s against 0.2 to 0.4 s for gcc and 0.3 to 0.5 s for rustc
(median of 3, incremental cache off).

## Reading the table

**Level with C or ahead (0.87 to 1.14 on `kelp-llvm`):** `nbody`, `spectral-norm`,
`mandelbrot`, `binary-trees`, `sieve`, `matmul`. **Slower by 1.24 to 1.32:**
`fib`, `fannkuch-redux`, `sort`, `json-tokenizer`. **Slower by more than 1.5:**
`strings` (1.84) and `hashmap` (1.88). **Far ahead of C:** `sort-builtin` (0.35),
only because C's `qsort` calls its comparator through a function pointer; that
row measures `qsort`, not C. Against Rust, `kelp-llvm` is faster in `fib`,
`binary-trees`, `matmul` and `hashmap`, level in `spectral-norm` and `mandelbrot`,
and slower in `nbody`, `fannkuch-redux`, `sieve` (slightly), `strings`, `sort`,
`sort-builtin` and `json-tokenizer`.

### Every ratio above 1.5, with its cause

| cell (second run) | ratio | cause |
| --- | ---: | --- |
| `fib`, Rust | 1.51 | Not Kelp. Rust and Kelp both go through LLVM and both are about 1.2 to 1.5 times slower than gcc on this recursion; objdump shows each binary keeps one recursive call and turns the other into a loop, so the difference is loop code generation. `kelp-c` is 1.01 because it is gcc. Not investigated further. |
| `spectral-norm`, `kelp-c` | 1.71 | Found and verified: the C oracle backend emits every Kelp function with external linkage, so `eval_a` stays an out-of-line call per matrix element under gcc -O2. Making it `static` in the emitted C gives 0.07 s, the same as hand-written C; removing the bounds and `to_usize` checks changes nothing (0.13 s both). The default LLVM backend is at parity (0.98). Not fixed: the oracle is not the product backend, and `static` is not sound under `--incremental` (cross-unit calls). |
| `strings`, `kelp-llvm` / `kelp-c` | 1.84 / 1.89 | A timed split of the 0.22 s (experiments, not in the table): building the 7.9 MB text 0.07 s (C about 0.03 s; `str.from_i64` plus `push_str` per piece), `str.split` into 1M owned `String`s 0.09 s, the byte hash loop 0.06 s. The hash loop uses `str.byte(p, i)`, which does a `memchr` over `i + 1` bytes per call; reading the same pieces through a `View` makes that 0.01 s and the whole program 0.17 s (1.4x). The benchmark keeps the `str.byte` spelling because it is the first one a user reaches for. |
| `hashmap`, `kelp-llvm` / `kelp-c` | 1.88 / 2.29 | `Map` is two arrays (a hash index and dense insertion-ordered entries, so a lookup is two dependent cache misses) and `Map.new()` grows by rehashing; the C table is one array sized up front. Measured: `Map.with_capacity(2n)` takes the program from 0.32 s to 0.24 s (1.4x C, experiment only); the remaining gap is the double indirection. `kelp-c` is slower than `kelp-llvm` here too, probably for the external-linkage reason above (not checked). |
| `hashmap`, Rust | 2.66 | The default std hasher (SipHash-1-3) and a table grown from empty with `HashMap::new()`. Not measured separately. |
| `sort`, `kelp-c` | 1.51 | `kelp-llvm` is 1.32. Both pay for the per-access `List.get`/`set` bounds check and the `List` header (`len`, `data`) reloaded around stores to `data`; Rust pays the bounds checks too but is at 1.06, so the extra is Kelp's. Reasoned from the emitted code, not profiled. gcc on the oracle's emitted C does worse than LLVM on the same program for the external-linkage reason. |

Between 1.2 and 1.5 and not in that table: `fib` 1.24, `fannkuch-redux` 1.28,
`sort` 1.32 and `json-tokenizer` 1.27 on `kelp-llvm`; `matmul` 1.28 and `strings`
1.25 on Rust. The Kelp ones are the same `List.get`/`set` bounds checks that C
does not have (`fannkuch-redux`, `sort`) and, for `json-tokenizer`, the
generation half. None was profiled; there is no `perf` on the machine, so every
cause above comes from reading emitted C or IR, from objdump, or from a small
timed experiment, said where used.

## What the suite found and fixed

Two real defects in `std/str`, both fixed in one commit (`kelpc/std/str.kp`):

1. **`str.split` was quadratic.** It called `starts_with_at` and `copy_range`,
   each of which calls `s.view()` and so `strlen`s the whole subject once per
   position and once per piece. Splitting the 7.9 MB string of the `strings`
   benchmark did not finish in 300 s on either backend. It now takes each
   argument's length once and slices views.
2. **`str.from_i64` and `from_u64` allocated a scratch `String`** (and ran `strlen`
   on it) for every number, two allocations per call. They now collect the digits
   in a 20-byte stack array, so the result is the only allocation.

Before and after, median of 7 in seconds. `fib`, `mandelbrot` and `sort` are
controls the change cannot touch; they show the host's run-to-run drift.

| benchmark / variant | before (first run) | after (second run) |
| --- | ---: | ---: |
| `strings` kelp-llvm | timeout at 300 s | 0.224 |
| `strings` kelp-c | timeout at 300 s | 0.230 |
| `json-tokenizer` kelp-llvm | 0.126 | 0.098 |
| `json-tokenizer` kelp-c | 0.126 | 0.110 |
| `json-tokenizer` c-gcc (control for host drift) | 0.079 | 0.077 |
| `fib` kelp-llvm (control) | 0.154 | 0.140 |
| `mandelbrot` kelp-llvm (control) | 0.115 | 0.114 |
| `sort` kelp-llvm (control) | 0.700 | 0.661 |

The `json-tokenizer` gain is the generation half (about a fifth of its time was
`from_i64`); its tokenizing half already matched C at about 0.047 s. The output of
both functions was checked against the previous behaviour on 0, `i64::MIN`,
`i64::MAX`, negatives and `u64::MAX`, and on several splits (empty pieces, a
trailing separator, a multi-byte separator, an empty separator), on both
backends.

## Findings not fixed

- **`str.byte(s, i)` costs O(i).** The bounds check is a `memchr` over `i + 1`
  bytes because a `str` has no stored length, so a byte loop over a long `str` is
  quadratic (a 100 KB tokenizer loop took 0.10 s where the `View` version took
  under 5 ms). The `json-tokenizer` Kelp program reads through a `View` for that
  reason and says so in its header comment. For users: call `s.view()` once,
  outside the loop.
- **`Map` growth and its double indirection.** Without `Map.with_capacity` the
  table rehashes as it grows, and a lookup is two dependent loads.
- **The C oracle's external linkage.** Every function in the emitted C is
  external, which costs `spectral-norm` 1.7x on `kelp-c`. Only the oracle is
  affected.
- **`List` aliasing, a hypothesis.** No `noalias` or TBAA information reaches LLVM
  for `List` accesses, which is the likely reason `sort` and `fannkuch-redux` are
  about 1.3x C where Rust, with the same bounds checks, is at 1.0 to 1.06. This
  comes from reading the emitted IR; it was not tested, and adding that
  information is neither cheap nor obviously sound, so it was left alone.

## Verifying a checksum yourself

Each program takes its size first, so a quick check needs no timing. These were
run on 2026-10-04 with the `kelpc` built from main, for gcc C, the LLVM backend
and `KELPC_ORACLE=c`, and all three printed the same line each time:

```sh
cc -O2 -o fib_c bench/suite/fib/fib.c -lm
kelpc build -O2 bench/suite/fib/fib.kp -o fib_llvm
KELPC_ORACLE=c kelpc build -O2 bench/suite/fib/fib.kp -o fib_kc
( ulimit -v 1048576; ulimit -t 10; timeout 10 ./fib_llvm 30 )
```

```text
fib 30 832040
nbody 50000 -0.169075164 -0.169078071
strings 20000 128890 20000 108890 161601173558904754
```

At the default sizes the same three printed `fib 38 39088169` and `strings
1000000 7888890 1000000 6888890 1997288086343803970`, and the full-size `strings` run, which timed out at 300 s before the `str.split`
fix, finished at once (0.224 s median in the second run).

## Reproducing

```sh
nix-shell overnight/dev.nix --run 'sh bench/run.sh'     # all thirteen
BENCHES="fib nbody" RUNS=3 sh bench/run.sh              # a subset
SIZE_ARG=1000 sh bench/run.sh                           # a size override, not for RESULTS.md
```

`run.sh` needs `cc`, `rustc` and the LLVM half of `kelpc` (set `KELPC` to use a
prebuilt compiler). It writes `bench/RESULTS.md` and the raw `bench/results.csv`;
the first run is kept as `bench/baseline-results.csv`. Do not compare numbers
across machines: the point of the tables is the ratios, on one host, in one
sitting.

## See also

- [Compiler benchmarks](/compiler/benchmarks)
- [Backends](/compiler/backends): the LLVM backend and the C oracle
- [`kelpc` CLI](/tooling/kelpc-cli)
- [`std/str`](/stdlib/str)
