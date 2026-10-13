---
title: "Performance of the 26.10.5 hosted build"
description: "Recorded wall time and peak memory of the 26.10.5 hosted Kelp build (manual memory, -O2) against gcc -O2 C on four benchmarks, with spreads, load conditions, and what the numbers do and do not show."
isPublished: true
tags: "performance, memory, benchmarks"
---
These are the recorded numbers for Kelp's 26.10.5 hosted build, which had manual
memory: no collector, every value freed by its owner. Current `main` links the
collector into every hosted build, and that build has not been measured on this
page. The C programs were removed from the tree, so the C figures cannot be rerun.
Tidepool steps 1 and 2 are on `main`. Its design is on [Tidepool](/memory/tidepool).

## Conditions

- **Build.** `kelpc build -O2` on the default LLVM backend, hosted mode. The C
  reference is the gcc -O2 build of each benchmark's C program, which was in the tree
  when these runs were made. Both sides run the full default size of each benchmark.
- **Compiler.** The 26.10.5 release asset, for the baseline table. The second table
  uses the 26.09.5 compiler from the run recorded in `bench/RESULTS.md`, so the two
  tables are not the same build.
- **Method.** One discarded warm-up, then 7 timed runs. The reported figure is the
  median wall time, with the minimum, the maximum, and the spread
  `(max - min) / median`. Peak RSS is the GNU `time` maximum resident size.
- **Machine.** A 4-logical-CPU Intel i5-6500T with 7.6 GB of memory, shared with
  other work. The 1-minute load average was between 0.85 and 0.98 for the baseline
  run and between 2.2 and 3.1 for the older run. Nothing was stopped or throttled
  to quiet the host.
- **Bounds checks.** Kelp checks array and list bounds in both its builds. The C
  reference does not. That favours C by construction.

## Baseline: 26.10.5 hosted, depth 16 (recorded)

Source: `bench/managed/baseline-hosted-d16.md`, produced by `bench/managed/gate.sh`
with `BT_DEPTH=16`, 7 runs and 1 warm-up. Times in seconds.

| benchmark | variant | median | min | max | spread % | peak RSS MiB | ratio to C |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| binary-trees | hosted | 0.3600 | 0.3581 | 0.3730 | 4.1 | 18.3 | 1.13 |
| binary-trees | C (gcc -O2) | 0.3189 | 0.3171 | 0.3241 | 2.2 | 10.1 | 1.00 |
| strings | hosted | 0.2101 | 0.2080 | 0.2119 | 1.9 | 63.1 | 1.91 |
| strings | C (gcc -O2) | 0.1098 | 0.1090 | 0.1131 | 3.7 | 47.7 | 1.00 |
| hashmap | hosted | 0.3385 | 0.3292 | 0.3406 | 3.4 | 80.1 | 1.86 |
| hashmap | C (gcc -O2) | 0.1821 | 0.1770 | 0.1892 | 6.7 | 66.1 | 1.00 |
| json-tokenizer | hosted | 0.0963 | 0.0949 | 0.1037 | 9.1 | 21.3 | 1.26 |
| json-tokenizer | C (gcc -O2) | 0.0765 | 0.0755 | 0.0797 | 5.5 | 21.2 | 1.00 |

The ratio is the hosted median divided by the C median. The checksum of every
hosted run matched the C output.

## Older run: 26.09.5, the full suite (recorded)

Source: `bench/RESULTS.md`, the second run, kelp-llvm column, 7 runs each, on the
same machine under heavier load. Times in seconds.

| benchmark | kelp-llvm median | min | max | C (gcc -O2) median | ratio | kelp-llvm peak RSS MiB | C peak RSS MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| binary-trees | 0.404 | 0.402 | 0.406 | 0.383 | 1.06 | 18.2 | 10.1 |
| strings | 0.224 | 0.219 | 0.227 | 0.122 | 1.84 | 62.9 | 47.7 |
| hashmap | 0.322 | 0.319 | 0.323 | 0.171 | 1.88 | 80.0 | 66.0 |
| json-tokenizer | 0.098 | 0.097 | 0.099 | 0.077 | 1.27 | 21.2 | 21.2 |

The C medians in this table are lower or higher than the baseline's by up to 20%.
The Kelp medians differ by at most about 12% between the two runs. Treat the
ratios as the stable part, and the absolute times as the part that moves with load.

## What the numbers show

- **binary-trees is close to C.** It is the benchmark closest to the cost of the
  ownership model: it allocates and frees a tree of `Box` nodes many times. Its
  time is 1.06 to 1.13 times C's, and its peak memory is about 1.8 times C's
  (18 MiB against 10 MiB). The cause of the extra memory was not investigated.
- **strings is about 1.9 times C.** The analysis section of `bench/RESULTS.md` found the
  cost in the byte-by-byte scan, where `str.byte` does a search over the bytes up
  to its index on each call. Reading the same pieces through a `View` brings the
  program to about 1.4 times C. Building the text and splitting it into owned
  `String`s account for the rest. See [Text](/language/text).
- **hashmap is about 1.9 times C.** `Map` keeps a hash index and a dense entry
  array, so a lookup touches two arrays, and a map that is not sized up front grows
  by rehashing. `Map.with_capacity` removes part of the growth cost. The remaining
  gap is the extra indirection, and it is the largest ratio in the table.
- **json-tokenizer is about 1.3 times C.** The analysis attributes part of the gap to
  the generation half of the benchmark, and it was not profiled.

These benchmarks measure whole programs. They do not isolate the cost of
ownership itself, and no row here is a measurement of a drop, a move or a borrow
by itself. What they do show is that a program built on single ownership, with
`Box` trees, owned strings and maps, runs within about 2 times C on this suite, and
that its peak memory is between 1.0 and 1.8 times C's.

## Limits of these numbers

- Each figure is one machine, and the machine was shared with other work.
- The baseline is one compiler release, and the older table is another. They are
  not compared against each other as a regression.
- The sizes are the ones the suite fixes, so the runs are short (0.1 to 0.4 s), and
  the measurement wrapper adds about 8 ms to each.
- No figure here is for a freestanding build or for a `-O0` build.
