---
title: "Catalogue"
description: "All twenty-nine first-party libraries, grouped by what they do. Twenty-eight are folders in the fpl repository, a manifest line each; Polyp ships with the compiler instead."
isPublished: true
tags: "library"
---
All twenty-eight first-party libraries, grouped by what they do. Each is a folder in the
[fpl repository](https://homelabone.xenoo.dev/gittea/Lilly/fpl), a single manifest line each.

## Data formats

| Library | What it does |
| --- | --- |
| [`json`](/libraries/json) | JSON (RFC 8259) parser, writer, JSON-Pointer lookup, tree transforms, closure traversal |
| [`config`](/libraries/config) | TOML/INI-ish reader: pairs, `[section]` tables, string arrays, comments |
| [`csv`](/libraries/csv) | RFC-4180-ish CSV parse/write: quoting, escaped quotes, embedded newlines |
| [`encoding`](/libraries/encoding) | Base64 (RFC 4648), base32 (RFC 4648 §6), base58 (Bitcoin), hex, percent (RFC 3986) and form (`application/x-www-form-urlencoded`) encode/decode, plus a hexdump |
| [`url`](/libraries/url) | RFC 3986 URI parsing, building, `remove_dot_segments` and relative-reference resolution |

## Numbers and mathematics

| Library | What it does |
| --- | --- |
| [`bigint`](/libraries/bigint) | Arbitrary-precision integers over base-2³² limbs |
| [`decimal`](/libraries/decimal) | Fixed-point decimals over `i64` with an explicit scale |
| [`complex`](/libraries/complex) | Complex numbers over `f64` |
| [`mathx`](/libraries/mathx) | gcd/lcm, primality, factorial, hypot, checked and saturating `i64` |
| [`stats`](/libraries/stats) | mean/median/variance/stddev/percentile/histogram, linear regression |
| [`prng`](/libraries/prng) | Seeded, reproducible xorshift64* PRNG |
| [`bits`](/libraries/bits) | `BitSet` over `Bytes`, MSB-first `BitWriter`/`BitReader` |
| [`hash`](/libraries/hash) | CRC-32 and FNV-1a (32- and 64-bit) checksums |

## Text and time

| Library | What it does |
| --- | --- |
| [`glob`](/libraries/glob) | `*`/`?` glob matching and list filtering |
| [`datetime`](/libraries/datetime) | Civil date/time from unix seconds, ISO-8601, day-of-week |

## Collections and ergonomics

| Library | What it does |
| --- | --- |
| [`listx`](/libraries/listx) | `fold`, `zip`, `chunks`, `sort_by`, `sum`/`min`/`max`, `unique`, `position` |
| [`set`](/libraries/set) | `Set<T>` and `StrSet`, with union/intersect/difference |

## System, files and networks

| Library | What it does | Needs |
| --- | --- | --- |
| [`fsx`](/libraries/fsx) | Atomic writes, recursive `copy_dir`, `tail`, `files_equal`, a depth-capped `survey` | `fs` |
| [`dedup`](/libraries/dedup) | Duplicate-file grouping and tree snapshot/drift over `List<Entry>` | - |
| [`httpx`](/libraries/httpx) | Query strings, Basic Auth, PUT/DELETE/PATCH, `Set-Cookie` | - |
| [`lineproto`](/libraries/lineproto) | CRLF line protocols over a socket | `net` |
| [`discord`](/libraries/discord) | Discord bots and webhooks over `std/http` and `std/ws`: payload builders, a gateway loop, webhooks, and every opcode and close code the raw path needs | `net`, `rand`, `time` |

## Programs: arguments, output, testing, timing

| Library | What it does | Needs |
| --- | --- | --- |
| [`argparse`](/libraries/argparse) | Flags, `--name[=value]` options, positionals, `--help` text | - |
| [`term`](/libraries/term) | ANSI SGR colors, cursor control, `NO_COLOR` handling | `env` |
| [`log`](/libraries/log) | Leveled log records to stderr with a timestamp | `time` |
| [`table`](/libraries/table) | Column layout with auto-sized widths | - |
| [`testkit`](/libraries/testkit) | `check()`/`check_eq_*` helpers with a pass/fail `Report` | - |
| [`benchkit`](/libraries/benchkit) | Warmup + repeat timing, median/percentile over the runs | `time` |

## Adding one

See [Writing a library](/libraries/writing-a-library). A new library is a folder, a row in
the repository's table and a page in this chapter: there is no release step,
because there is no version.
