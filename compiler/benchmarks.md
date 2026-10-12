---
title: "Benchmarks: what they say about the compiler"
description: "What the benchmark suite says about the compiler: the default llvm backend against Rust, the recorded C and oracle columns, and the compiler-side defects the suite found."
isPublished: true
tags: "compiler"
---
The benchmark suite times thirteen programs in Rust and Kelp. Earlier runs also
timed a C version, which is no longer in the tree. This page covers what those
numbers say about the compiler. The full table, the method and the
analysis are on [the tooling page](/tooling/benchmarks) and in `bench/RESULTS.md`
and `bench/notes.md` on Kelp's `main` branch.

## What the compiler is measured as

The suite builds each Kelp program with the LLVM backend. Older runs also
have a column for the C oracle, which has since been removed:

| Column | Backend | What the number tells you |
| --- | --- | --- |
| `kelp-llvm` | `llvm`, the one backend `kelpc` uses for every program | the speed of the code a user gets |
| `kelp-c` | the C oracle, removed on 2026-10-10 and refused by name since then | the speed of the reference backend in older runs, which was never a user surface |

For the `llvm` column, the recorded 26.10.5 run is close to the C column. Four of the
thirteen programs are at or faster than C (`nbody`, `spectral-norm`, `mandelbrot` and `sort-builtin`). Five
more are within 1.3 of C (`binary-trees`, `sieve`, `matmul`, `fannkuch-redux` and
`json-tokenizer`). Three are slower: `fib` (1.33), `sort` (1.32) and `strings`
(1.86). The `hashmap` row reads 1.11 in the latest run, but that row depends on a C
baseline that did not reproduce, so it is not counted here. See
[the tooling page](/tooling/benchmarks#changes-since-the-previous-recorded-run).

## Where the compiler is the cause

The suite has pointed at three compiler-side problems so far:

- **The oracle gives every function external linkage (recorded runs).** On `spectral-norm`, that
  keeps a small helper out of line, and the `kelp-c` ratio is 1.65 against 0.96
  for `kelp-llvm`. Making the helper `static` in the emitted C fixes it. The
  `llvm` backend is not affected.
- **No alias information reaches LLVM for `List` accesses.** This is the likely
  cause of the 1.3 ratio on `sort` and `fannkuch-redux`. It is a hypothesis from
  the emitted IR, and the change needed is not a cheap one.
- **Bounds checks on each `List` access.** Kelp checks every index, as Rust does,
  and the reloads of the list header around stores add cost that Rust does not
  pay.

## What the suite has changed

The suite found two real defects in the standard string module, and both are
fixed. `str.split` was quadratic, and `str.from_i64` allocated a scratch string
for every number. On the `strings` benchmark the split defect meant the program
did not finish in 300 seconds, and it now takes about 0.21 seconds on the
`llvm` backend and 0.22 seconds on the oracle.
The details are on [the tooling page](/tooling/benchmarks#what-the-suite-found-and-fixed).

## See also

- [Benchmarks](/tooling/benchmarks): the suite, the current table and the method
- [Backends](/compiler/backends): the `llvm` backend, the only code generator
- [Incremental builds](/compiler/incremental): how the compile itself is sped up
