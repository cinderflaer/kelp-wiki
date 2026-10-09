---
title: "Libraries (fpl)"
description: "fpl is the first-party Kelp library catalogue - one folder per library in a single repository, twenty-eight of them at the time of writing."
isPublished: true
tags: "library"
---
The first-party library catalogue: one folder per library in a single repository, twenty-eight of them.

Unlike the standard library, which is compiled into `kelpc` and imported as
`std/…`, every fpl library is a **dependency you fetch**: a folder from a git
remote, landed in your project's `src/deps/`.

```toml
# coral.toml
[dependencies]
json = "Juniper/fpl/json"
hash = "Juniper/fpl/hash"
```

```kelp
impl "deps/json/lib"
impl "deps/hash/lib"
```

## The four rules that shape the catalogue

1. **A dependency is a folder.** A consumer depends on `json`, not on `fpl`, so it
   gets `json` and nothing else. Two libraries are two manifest lines, and neither
   fetches the other.
2. **There is no version and no lockfile.** A dependency is a git remote and
   `coral sync` takes its tip. What makes a build reproducible is that
   `src/deps/<name>/` *is* the tree it built with, and `coral build` never touches
   a dependency that is already there.
3. **A folder must stand alone.** Only the named folder is fetched, so a library
   here cannot `impl` another one: the sibling was never downloaded and there is
   no `deps/fpl/...` in the consumer's tree to name. When two libraries need the
   same helper, they either carry their own copy (`httpx` holds a base64 encoder,
   and `url` a percent codec, because neither may import `encoding`) or they stop
   being two libraries.
4. **Publishing is pushing.** A library has no version, so there is nothing to
   tag: the next `coral sync` on any consumer takes the branch tip. A change that
   needs an *unreleased* compiler is the one exception: it waits on `fpl`'s
   `unreleased` branch, because `main` has to keep building against the released
   one. [Writing a library](/libraries/writing-a-library) has the rule in full.

Every library targets `kelpc 0.1.5` or newer. `json` uses `str.less` and a
closure over its own `Json` type; `decimal`, `encoding`, `httpx` and `url` use
`str.is_digit`. Both helpers and the closure codegen landed in that release, so
an older compiler refuses those files at codegen rather than at the manifest.

Some libraries are **gated** exactly like a `std/*` module, because they wrap one:
the consumer delegates the capability at the `impl` line.

```kelp
impl "deps/fsx/lib" caps(fs = ["/var/lib/myapp/**"])
impl "deps/log/lib" caps(time = [])
impl "deps/lineproto/lib" caps(net = ["127.0.0.1:*"])
```

| Library | Needs |
| --- | --- |
| `fsx` | `fs` |
| `log`, `benchkit` | `time` |
| `term` | `env` (`NO_COLOR`) |
| `lineproto` | `net` |
| `discord` | `net`, `rand` and `time` |
| everything else | nothing |

## Reading a library page

Each page in this chapter is written to the same shape: what it is, the dependency
line and capability grant, the whole API with argument and panic behaviour, an
example whose output was checked against `kelpc`, and what it deliberately does
**not** do. The library's own source is one file, `lib.kp`, in the
[fpl repository](https://homelabone.xenoo.dev/gittea/Juniper/fpl).

## Pages

- [Catalogue](/libraries/catalogue): every library, grouped by what it does, with what it needs.
- [Writing a library](/libraries/writing-a-library): what a library has to be.
- [`argparse`](/libraries/argparse): flags, options, positionals, defaults and rendered `--help` text.
- [`benchkit`](/libraries/benchkit): warmup and repeat timing over a closure (gated on `time`).
- [`bigint`](/libraries/bigint): arbitrary-precision integers over base-2^32 limbs.
- [`bits`](/libraries/bits): `BitSet` over `Bytes`, and MSB-first `BitWriter` and `BitReader`.
- [`complex`](/libraries/complex): complex numbers with arithmetic, `conj`, `abs`, `arg` and `from_polar`.
- [`config`](/libraries/config): a TOML/INI-style reader: `key = value`, `[section]` tables and string arrays.
- [`csv`](/libraries/csv): RFC 4180-style CSV parsing and writing.
- [`datetime`](/libraries/datetime): civil date and time from unix seconds, and ISO 8601 parse and format.
- [`decimal`](/libraries/decimal): fixed-point decimals over `i64` with an explicit scale.
- [`dedup`](/libraries/dedup): duplicate-file grouping, and tree snapshot and drift.
- [`discord`](/libraries/discord): Discord bots and webhooks over `std/http` and `std/ws` (needs `net`, `rand` and `time`).
- [`encoding`](/libraries/encoding): base64, base32, base58, hex, percent and form encoding, and a hexdump.
- [`fsx`](/libraries/fsx): `write_atomic`, `copy_dir`, `tail` and `files_equal` over `std/fs` (gated on `fs`).
- [`glob`](/libraries/glob): `glob_match` and `glob_filter` over `*` and `?` patterns.
- [`hash`](/libraries/hash): CRC-32 and FNV-1a checksums.
- [`httpx`](/libraries/httpx): HTTP helpers over `std/http`: query strings, Basic auth and PUT, DELETE and PATCH.
- [`json`](/libraries/json): JSON parser and writer, keyed accessors with defaults, JSON Pointer and tree transforms.
- [`lineproto`](/libraries/lineproto): buffered `send_line` and `read_line` over a `std/net` socket (gated on `net`).
- [`listx`](/libraries/listx): `List<T>` helpers `std/list` stops short of: `fold`, `zip`, `chunks`, `sort_by` and more.
- [`log`](/libraries/log): leveled log records to stderr with a timestamp (gated on `time`).
- [`mathx`](/libraries/mathx): `gcd`, `lcm`, primality, `factorial`, `hypot`, and checked and saturating `i64` arithmetic.
- [`prng`](/libraries/prng): a seeded, reproducible xorshift64* PRNG.
- [`set`](/libraries/set): `Set<T>` over `Map`, and `StrSet` for `String`.
- [`stats`](/libraries/stats): mean, median, variance, percentile, histogram and linear regression over `List<f64>`.
- [`table`](/libraries/table): column layout with auto-sized widths.
- [`term`](/libraries/term): ANSI colors and cursor control, honouring `NO_COLOR` (gated on `env`).
- [`testkit`](/libraries/testkit): assert-style `check` helpers with a pass/fail `Report`.
- [`url`](/libraries/url): RFC 3986 URI parsing, building and relative-reference resolution.

## See also

- [Projects and coral.toml](/getting-started/projects): the manifest side
- [Capabilities](/language/capabilities): what a grant means

[Back to the home page](/)
