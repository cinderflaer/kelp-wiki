# Catalogue

All twenty-five first-party libraries, grouped by what they do. Every one is a
folder in the [fpl repository](https://homelabone.xenoo.dev/gittea/Juniper/fpl)
and every one is a single manifest line.

## Data formats

| Library | What it does |
| --- | --- |
| [`json`](json.md) | JSON (RFC 8259) parser, writer, JSON-Pointer lookup, tree transforms |
| [`config`](config.md) | TOML/INI-ish reader: pairs, `[section]` tables, string arrays, comments |
| [`csv`](csv.md) | RFC-4180-ish CSV parse/write: quoting, escaped quotes, embedded newlines |
| [`encoding`](encoding.md) | Base64 (RFC 4648) and percent (RFC 3986) encode/decode |
| [`lineproto`](lineproto.md) | Buffered `send_line`/`read_line` over a socket — gated on `net` |

## Numbers and mathematics

| Library | What it does |
| --- | --- |
| [`bigint`](bigint.md) | Arbitrary-precision integers over base-2³² limbs |
| [`decimal`](decimal.md) | Fixed-point decimals over `i64` with an explicit scale |
| [`complex`](complex.md) | Complex numbers over `f64` |
| [`mathx`](mathx.md) | gcd/lcm, primality, factorial, hypot, checked and saturating `i64` |
| [`stats`](stats.md) | mean/median/variance/stddev/percentile/histogram, linear regression |
| [`prng`](prng.md) | Seeded, reproducible xorshift64* PRNG |
| [`bits`](bits.md) | `BitSet` over `Bytes`, MSB-first `BitWriter`/`BitReader` |
| [`hash`](hash.md) | CRC-32 and FNV-1a (32- and 64-bit) checksums |

## Text and time

| Library | What it does |
| --- | --- |
| [`glob`](glob.md) | `*`/`?` glob matching and list filtering |
| [`datetime`](datetime.md) | Civil date/time from unix seconds, ISO-8601, day-of-week |

## Collections and ergonomics

| Library | What it does |
| --- | --- |
| [`listx`](listx.md) | `fold`, `zip`, `chunks`, `sort_by`, `sum`/`min`/`max`, `unique`, `position` |
| [`set`](set.md) | `Set<T>` and `StrSet`, with union/intersect/difference |

## System, files and networks

| Library | What it does | Needs |
| --- | --- | --- |
| [`fsx`](fsx.md) | Atomic writes, recursive `copy_dir`, `tail`, `files_equal` | `fs` |
| [`httpx`](httpx.md) | Query strings, Basic Auth, PUT/DELETE/PATCH, `Set-Cookie` | — |
| [`lineproto`](lineproto.md) | CRLF line protocols over a socket | `net` |

## Programs: arguments, output, testing, timing

| Library | What it does | Needs |
| --- | --- | --- |
| [`argparse`](argparse.md) | Flags, `--name[=value]` options, positionals, `--help` text | — |
| [`term`](term.md) | ANSI SGR colors, cursor control, `NO_COLOR` handling | `env` |
| [`log`](log.md) | Leveled log records to stderr with a timestamp | `time` |
| [`table`](table.md) | Column layout with auto-sized widths | — |
| [`testkit`](testkit.md) | `check()`/`check_eq_*` helpers with a pass/fail `Report` | — |
| [`benchkit`](benchkit.md) | Warmup + repeat timing, median/percentile over the runs | `time` |

## Adding one

See [Writing a library](writing-a-library.md). A new library is a folder, a row in
the repository's table and a page in this chapter — there is no release step,
because there is no version.
