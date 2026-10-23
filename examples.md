---
title: "Examples"
description: "Eighteen programs in nineteen files, each built and run against the real compiler. Find one by what it shows, then read its whole source and its output."
isPublished: true
tags: "example"
---
The example programs are real files in this repository, not snippets.
Each page shows the whole source, the command that builds or runs it, and the output it prints.
The programs that need no dependency or second file are built and run by `scripts/check-examples.sh`, so an example that stops working shows up as a failure. The others are only parsed by it.

New to Kelp? Start with the [Tutorial](/tutorial), which teaches the language one idea at a time.
Its last chapter builds a small tool the same way the programs here are built.

## Find an example by what you want to do

| I want to see how to ... | Example | Needs |
| --- | --- | --- |
| write a function, a loop and output | [recursive-fibonacci](/examples/recursive-fibonacci) | nothing |
| count lines, words or bytes in a file | [count-lines-words-bytes](/examples/count-lines-words-bytes) | nothing |
| walk a directory tree and filter files | [count-lines-in-kelp-tree](/examples/count-lines-in-kelp-tree) | `fpl/glob` |
| checksum, encode and format dates | [checksums-encodings-dates](/examples/checksums-encodings-dates) | `fpl/hash`, `fpl/encoding`, `fpl/datetime` |
| build a command-line tool with flags | [word-count-with-flags](/examples/word-count-with-flags) | `fpl/argparse` |
| read settings from a manifest | [read-manifest-settings](/examples/read-manifest-settings) | `fpl/config` |
| filter JSON records | [filter-json-by-score](/examples/filter-json-by-score) | `fpl/json` |
| total a CSV column as a table | [total-csv-column](/examples/total-csv-column) | `fpl/csv`, `fpl/table` |
| use list and set helpers | [list-and-set-helpers](/examples/list-and-set-helpers) | `fpl/listx`, `fpl/set` |
| use exact and numeric libraries | [exact-numeric-libraries](/examples/exact-numeric-libraries) | `fpl/bigint`, `fpl/decimal`, `fpl/complex`, `fpl/mathx`, `fpl/stats`, `fpl/prng` |
| pack bit fields and seeded bytes | [pack-bit-fields](/examples/pack-bit-fields) | `fpl/bits`, `fpl/prng` |
| download a URL to a file | [download-url-to-file](/examples/download-url-to-file) | `fpl/fsx` |
| build HTTP request parts | [build-http-request-parts](/examples/build-http-request-parts) | `fpl/httpx` |
| talk over TCP with a line protocol | [ping-pong-server](/examples/ping-pong-server) and [ping-pong-client](/examples/ping-pong-server) | `fpl/lineproto` |
| grant a module one directory | [sandbox-directory-grant](/examples/sandbox-directory-grant) | nothing |
| print colour and log records | [terminal-table-and-logs](/examples/terminal-table-and-logs) | `fpl/term`, `fpl/log`, `fpl/table` |
| test and time a program | [self-test-and-timing](/examples/self-test-and-timing) | `fpl/testkit`, `fpl/benchkit` |

The `ping-pong-client` program has no page of its own.
It is covered on the [ping-pong-server](/examples/ping-pong-server) page with the server.
The `vault` file is a module rather than a program, and the [sandbox-directory-grant](/examples/sandbox-directory-grant) page shows it.
That is why the table has eighteen programs in nineteen files.

## Running one

A single file is a program:

```sh
kelpc run recursive-fibonacci.kp
```

An example that reads `argv` is built and then run, because `kelpc run` takes no arguments.
In a project, Coral forwards them: `coral run -- <args>`.

```sh
kelpc build count-lines-words-bytes.kp -o count-lines-words-bytes && ./count-lines-words-bytes README.md
```

An example that imports a library needs that folder beside it, because a dependency is a folder in a git repo:

```toml
# coral.toml
[dependencies]
json = "Lilly/fpl/json"
```

```sh
coral sync      # lands the contents of fpl/json at src/deps/json/
kelpc build src/main.kp -o app
```

Every source file is downloadable: the page's Source link points at the `.kp` file as it is served next to the page.

## What the examples deliberately do not hide

Four traps caught the examples' own code while it was written.
The programs keep the fixes visible in comments rather than hiding them:

- An **owned local inside an `if let` arm** does not build yet, so the work lives in a small function.
  [filter-json-by-score](/examples/filter-json-by-score), [total-csv-column](/examples/total-csv-column), [exact-numeric-libraries](/examples/exact-numeric-libraries) and [read-manifest-settings](/examples/read-manifest-settings) all say so.
- **`process.args()` includes `argv[0]`**, so a tool drops the first entry before it parses.
  See [word-count-with-flags](/examples/word-count-with-flags).
- **`.as_str()` on a temporary is refused**, so the path is bound to a `val` first.
  See [sandbox-directory-grant](/examples/sandbox-directory-grant).
- **A gated call takes an absolute path**, so a relative argument is resolved through `path.absolute(fs.cwd(), arg)` before it is used.
  See [count-lines-in-kelp-tree](/examples/count-lines-in-kelp-tree).

Three smaller ones are each a single error message: `is_none` belongs to `option` and not to `result`; `when` is a keyword and cannot be a binding; and `str.concat` takes `&str`, so a `String` argument needs `.as_str()`.

All of them are documented in [Pitfalls](/language/pitfalls).
