---
title: "Examples"
description: "Eighteen programs in nineteen files, every one built and run against the real compiler. They are not snippets - each is a file in this repository, and each page shows the whole source, the command..."
isPublished: true
tags: "example"
---
Eighteen programs in nineteen files, every one built and run against the real
compiler. They are not snippets: each is a file in this repository, and each page
shows the whole source, the command that produced the output below it, and that
output verbatim.

New to Kelp? The [Tutorial](/tutorial) teaches the language one idea at a time, and
its last chapter builds a small tool the same way these programs are built.

That last part is the point. An example that has not been run is a claim, so the
programs are compiled and executed by
[`tools/check-examples.sh`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki/src/branch/main/tools/check-examples.sh),
which builds and runs eighteen programs in nineteen processes (the line-protocol
pair is two) and prints each one's exit code with its output. Run it yourself:

```sh
bash tools/check-examples.sh /path/to/KelpLANG
```

## The programs

| Program | Needs | Shows |
| --- | --- | --- |
| [wordcount](/examples/wordcount) | none | the `fs` capability, a byte loop over `str`, building output with `fmt`/`str` |
| [fib](/examples/fib) | none | recursion, `while`, `print` against `print!` |
| [json_filter](/examples/json_filter) | `fpl/json` | parsing into an owned tree, walking an array, rebuilding one bottom-up |
| [csv_report](/examples/csv_report) | `fpl/csv`, `fpl/table` | rows of fields, a `Map` accumulator, rendering a table |
| [glob_tree](/examples/glob_tree) | `fpl/glob` | `fs.walk` over a tree, `*` globs, a running total |
| [cli_tool](/examples/cli_tool) | `fpl/argparse` | flags, options with defaults, positionals, `--help`, exit codes |
| [tests_and_bench](/examples/tests_and_bench) | `fpl/testkit`, `fpl/benchkit` | a self-test report and a timing line in one program |
| [sandbox_main](/examples/sandbox_main) + [sandbox_vault](/examples/sandbox_main) | none | a grant the consumer narrows, and what a refusal looks like |
| [lines_server](/examples/lines_server) + [lines_client](/examples/lines_server) | `fpl/lineproto` | a TCP line protocol, two processes, `net` on both sides |
| [http_fetch](/examples/http_fetch) | `fpl/fsx` | an HTTP GET over a granted host, written to disk atomically |
| [numbers](/examples/numbers) | `fpl/bigint`, `fpl/decimal`, `fpl/complex`, `fpl/mathx`, `fpl/stats`, `fpl/prng` | exact arithmetic where a float is wrong, statistics, a reproducible sequence |
| [text_tools](/examples/text_tools) | `fpl/hash`, `fpl/encoding`, `fpl/datetime` | checksums, two encodings and their round trips, a date from unix seconds |
| [collections](/examples/collections) | `fpl/listx`, `fpl/set` | fold, zip, chunks and sort_by, then union, intersect and difference |
| [config_load](/examples/config_load) | `fpl/config` | the manifest format, typed accessors, defaults, and why a float is text |
| [bits_pack](/examples/bits_pack) | `fpl/bits`, `fpl/prng` | MSB-first bit fields, a bit set, and a seeded byte stream |
| [terminal_report](/examples/terminal_report) | `fpl/term`, `fpl/log`, `fpl/table` | colour against NO_COLOR, stdout against stderr, two grants in one program |
| [http_headers](/examples/http_headers) | `fpl/httpx` | query strings, Basic auth, PUT and DELETE and PATCH, a cookie value |

A `sandbox_vault` is a module rather than a program, and the line-protocol pair is
two programs talking to each other, which is why nineteen files are eighteen
programs and nineteen runs.

## Running one

A single file is a program:

```sh
kelpc run fib.kp
```

An example that reads `argv` is built and then run, because `kelpc run` takes no
arguments (it compiles and executes one file). In a project, Coral forwards them:
`coral run -- <args>`.

```sh
kelpc build wordcount.kp -o wordcount && ./wordcount README.md
```

An example that imports a library needs that folder beside it, because a
dependency is a folder in a git repo:

```toml
# coral.toml
[dependencies]
json = "Juniper/fpl/json"
```

```sh
coral sync      # lands the contents of fpl/json at src/deps/json/
kelpc build src/main.kp -o app
```

Every source file in this chapter is downloadable: the page's "Source" link points
at the `.kp` file as it is served next to the page.

## What the examples deliberately do not hide

Four traps caught this chapter's own code while it was being written, and the
programs keep the fixes visible in comments rather than papering over them:

- an **owned local inside an `if let` arm** does not build yet, so the work lives
  in a small function: [json_filter](/examples/json_filter), [csv_report](/examples/csv_report),
  [numbers](/examples/numbers) and [config_load](/examples/config_load) all say so;
- **`process.args()` includes `argv[0]`**, so a tool drops the first entry before
  parsing: [cli_tool](/examples/cli_tool);
- **`.as_str()` on a temporary is refused**, so the path is bound to a `val`
  first: [sandbox_vault](/examples/sandbox_main);
- **a gated call takes an absolute path**, so a relative argument is resolved
  through `path.absolute(fs.cwd(), arg)` before it is used:
  [glob_tree](/examples/glob_tree).

Three smaller ones, each a single error message: `is_none` belongs to `option`
and not to `result`; `when` is a keyword and cannot be a binding, so the parsed
date is named `moment`; and `str.concat` takes `&str`, so a `String` argument
needs `.as_str()`.

All of them are documented in [Pitfalls](/language/pitfalls).
