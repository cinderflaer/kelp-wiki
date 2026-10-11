---
title: "Managed comparison (placeholder)"
description: "Placeholder for the managed build's numbers against the hosted build with manual memory. Not measured: the managed build is not finished. The gate command that will produce the table is given."
isPublished: true
tags: "performance, memory, benchmarks"
---
> **Not measured: the managed build is not finished.** This page holds the table
> headings only. No managed number exists yet, and none should be read into the
> hosted numbers on [Performance](/memory/performance) until the table below is
> filled from a gate run.

The comparison is the managed build (garbage collected) against the hosted build
(manual memory, [Performance](/memory/performance)), on the same four benchmarks,
with the same wrapper and the same load reporting.

## Gate

The gate is `bench/managed/gate.sh` in the `kelp` repository. It lives on the
`gc-verify` branch, not yet on `unreleased`. It runs the hosted build always, and
the managed build only when a managed-capable compiler is named. Gate G-A passes
when the managed median is at most 1.00 times the hosted median, falls back at
1.10 with the owner's acceptance, and fails above that.

```sh
KELPC_MANAGED=/path/to/managed-kelpc MANAGED_FLAGS=<flags once WP2/WP3 define them> \
BT_DEPTH=20 RUNS=7 WARMUP=1 OUT_DIR=/path/outside/the/repo sh bench/managed/gate.sh
```

Run it from the root of the `kelp` repository. `BT_DEPTH=20` is the binary-trees
depth the design paper uses for managed runs; the hosted baseline on
[Performance](/memory/performance) used depth 16. `OUT_DIR` must be outside the
repository. The gate writes `results.csv` and `gate.md` there.

## Table

Columns follow `gate.md`. Rows are filled from a gate run only.

| benchmark | variant | median s | min s | max s | spread % | peak RSS MiB | checksum | G-A |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| binary-trees | managed | not measured | | | | | | |
| strings | managed | not measured | | | | | | |
| hashmap | managed | not measured | | | | | | |
| json-tokenizer | managed | not measured | | | | | | |

## See also

- [Performance](/memory/performance): the hosted numbers this table is compared with
- [Benchmarks](/tooling/benchmarks): the suite and the harness
