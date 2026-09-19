# Examples

Eleven programs in twelve files, every one built and run against the real
compiler. They are not snippets: each is a file in this repository, and each page
shows the whole source, the command that produced the output below it, and that
output verbatim.

That last part is the point. An example that has not been run is a claim, so the
programs are compiled and executed by
[`tools/check-examples.sh`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki/src/branch/main/tools/check-examples.sh),
which builds and runs eleven programs in twelve processes (the line-protocol pair
is two) and prints each one's exit code with its output. Run it yourself:

```sh
bash tools/check-examples.sh /path/to/KelpLANG
```

## The programs

| Program | Needs | Shows |
| --- | --- | --- |
| [wordcount](wordcount.md) | — | the `fs` capability, a byte loop over `str`, building output with `fmt`/`str` |
| [fib](fib.md) | — | recursion, `while`, `print` against `print!` |
| [json_filter](json_filter.md) | `fpl/json` | parsing into an owned tree, walking an array, rebuilding one bottom-up |
| [csv_report](csv_report.md) | `fpl/csv`, `fpl/table` | rows of fields, a `Map` accumulator, rendering a table |
| [glob_tree](glob_tree.md) | `fpl/glob` | `fs.walk` over a tree, `*` globs, a running total |
| [cli_tool](cli_tool.md) | `fpl/argparse` | flags, options with defaults, positionals, `--help`, exit codes |
| [tests_and_bench](tests_and_bench.md) | `fpl/testkit`, `fpl/benchkit` | a self-test report and a timing line in one program |
| [sandbox_main](sandbox_main.md) + [sandbox_vault](sandbox_main.md) | — | a grant the consumer narrows, and what a refusal looks like |
| [lines_server](lines_server.md) + [lines_client](lines_server.md) | `fpl/lineproto` | a TCP line protocol, two processes, `net` on both sides |
| [http_fetch](http_fetch.md) | `fpl/fsx` | an HTTP GET over a granted host, written to disk atomically |

A `sandbox_vault` is a module rather than a program, and the line-protocol pair is
two programs talking to each other, which is why twelve files are eleven programs
and twelve runs.

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
  in a small function: [json_filter](json_filter.md) and [csv_report](csv_report.md);
- **`process.args()` includes `argv[0]`**, so a tool drops the first entry before
  parsing: [cli_tool](cli_tool.md);
- **`.as_str()` on a temporary is refused**, so the path is bound to a `val`
  first: [sandbox_vault](sandbox_main.md);
- **a gated call takes an absolute path** and v1 has no `cwd` accessor to make one,
  so the tools check with `p.is_absolute` and explain instead of panicking:
  [glob_tree](glob_tree.md).

All four are documented in [Pitfalls](../language/pitfalls.md) and
[Known issues](../meta/known-issues.md).
