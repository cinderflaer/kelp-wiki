---
title: "Benchmarks"
description: "Thirteen categories, each one program in C++, Rust and Kelp, with byte-identical stdout checked before any timing: the current table, the method, and what the suite has found."
isPublished: true
tags: "compiler"
---
`kelp/benchmarks/` is a three-language timing suite: thirteen categories, each
one program written three times, in C++, in Rust and in Kelp, built with the
same optimizer level and timed with `hyperfine` (warmup plus a fixed number of
runs, mean, standard deviation and outliers, not a single `time` call). No
timing is reported until all three programs have printed **the same bytes** to
stdout, because a difference in the work done is not a difference in speed.

| Category | 1st | 2nd | 3rd |
| --- | --- | --- | --- |
| `arithmetic` | **Kelp 49.7ms (tied C++)** | C++ 50.3ms | Rust 62.4ms (1.26x) |
| `recursion` | **Rust 18.3ms (three-way tie)** | Kelp 18.3ms | C++ 18.6ms |
| `sorting` | **Rust 96.8ms** | Kelp 141.4ms (1.46x) | C++ 233.9ms (2.42x) |
| `sieve` | **Kelp 30.4ms (tied C++)** | C++ 31.0ms | Rust 39.9ms (1.31x) |
| `strings` | **Rust 8.0ms** | Kelp 9.3ms (1.16x) | C++ 10.0ms (1.25x) |
| `collections` | **Kelp 165.0ms** | Rust 264.3ms (1.60x) | C++ 505.7ms (3.06x) |
| `capabilities` | **Kelp 77.8ms** | C++ 223.5ms (2.87x) | Rust 258.5ms (3.32x) |
| `nbody` | **C++ 1.57s** | Kelp 1.66s (1.05x) | Rust 2.41s (1.53x) |
| `spectralnorm` | **C++ 1.18s** | Rust 1.25s (1.06x) | Kelp 1.27s (1.08x) |
| `mandelbrot` | **Rust 4.66s (tied Kelp)** | Kelp 4.69s | C++ 4.83s (1.04x) |
| `fasta` | **Kelp 626.0ms** | C++ 681.8ms (1.09x) | Rust 2.65s (4.23x) |
| `binarytrees` | **Kelp 6.55s** | Rust 8.54s (1.30x) | C++ 8.97s (1.37x) |
| `fannkuchredux` | **Kelp 20.25s** | C++ 22.27s (1.10x) | Rust 22.89s (1.13x) |

Measured on 2026-09-26 with `kelpc` 26.09.4, one `./run.sh` pass, on the machine
the compiler is developed on. Kelp is first in seven of the thirteen, two of them
tied with C++, and it is ahead of the C++ reference outright in `fasta` (633ms
against 679ms at 25,000,000 characters in a run of its own).

## Two kinds of category

Seven categories are the project's own programs, one primitive each: a tight
integer loop (`arithmetic`), call overhead (`recursion`), each language's own
standard sort over identical pseudo-random data (`sorting`), a hand-written
sieve (`sieve`), building and scanning a 13.2MB string (`strings`), three
million hash-map inserts and lookups (`collections`), and the capability system
against the same raw C call (`capabilities`).

Six are ports of the Computer Language Benchmarks Game problems: `nbody`,
`spectralnorm`, `mandelbrot`, `fasta`, `binarytrees` and `fannkuchredux`. For
those, the algorithm, the input size and the required output are that project's
fixed definition rather than ours: the `.cpp` file is the published submission
byte for byte, and so is the `.rs` file wherever an official unthreaded variant
exists. `spectralnorm`, `mandelbrot`, `binarytrees` and `fannkuchredux` have no
such variant (every official Rust submission is threaded, rayon or async), so
their Rust file is a plain single-threaded port written for this suite and
labelled as one in that directory's `NOTES.md`. Racing threads against a
single-threaded Kelp program would measure the thread count, not the language.
Each port's own performance argument lives in its `size` file and is passed to
all three binaries.

## Reading the numbers honestly

- **The flags are ours, not the shootout's.** Everything here is built with one
  uniform command per language (`c++ -O2`, `rustc -O`, `kelpc build` at its
  default `-O2`), while the Benchmarks Game builds each submission with its own
  tuned command line, for instance `-O3 -march=ivybridge` for the C++ and
  `-C opt-level=3 -C target-cpu=ivybridge -C codegen-units=1` for the Rust. A row
  here compares within this suite; it is not the published shootout table.
- **Two rows are layout-sensitive and should be read as plus or minus 10%.**
  `recursion` and `sorting` moved when the compiler's emission order changed for
  unrelated reasons, with the emitted IR of a program containing no `Map`
  otherwise byte-identical between the two builds. Both were re-measured at 30
  runs per compiler, so it is not run-to-run noise either.
- **`collections` uses LCG-distributed keys in all three programs.** The first
  version inserted the keys `0..n` and libstdc++'s `std::hash<int64_t>` is the
  identity, so `std::unordered_map` walked memory almost in order and finished in
  105ms; with keys an LCG produces, the same C++ code is 534ms. All three
  languages now see the same sequence, and what the row compares is the maps.
- **Numbers are one machine on one day.** `benchmarks/results.md` carries the
  full table with min, max and hyperfine's relative column from the same pass.

## Reproducing it

```sh
cd benchmarks
./run.sh                 # all thirteen categories, writing results.md
./run.sh strings nbody   # a subset
KELPC=/path/to/kelpc ./run.sh
```

The reference binaries come from `c++ -O2` and `rustc -O` on the same files, so
the C++ compiler and `rustc` have to be on `PATH`; `hyperfine` is the timer.

## What the suite has changed

It is not a scoreboard. Building and running it found, and the compiler fixed,
the LLVM backend's out-of-line runtime calls for the small builtins (a 13.2MB
string scan was twice as fast after), `Map`'s `i64` index slots and its missing
capacity constructor, and the three things that stopped LLVM from packing the
N-body pair loop. It also rewrote two benchmark programs whose output shape made
the three languages incomparable, and it is what showed that the `capabilities`
row, once the worst gap in the suite, is now 2.87x ahead of the C++ that calls
`getenv` in the same loop. Each of those is an entry in the [changelog](/changelog).

A second, newer suite compares Kelp with C and Rust (not C++) with bounds checks
stated per language and every ratio above 1.5 explained: see
[Benchmarks: Kelp against C and Rust](/tooling/benchmarks).
