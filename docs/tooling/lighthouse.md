# Lighthouse

Lighthouse is the editor support for Kelp: a language server, plus the VS Code and
IntelliJ integrations that talk to it. This page follows
[Lighthouse's README](https://homelabone.xenoo.dev/gittea/Juniper/lighthouse/src/branch/main/README.md).

| Piece | What it is |
| --- | --- |
| `server/` | the `lighthouse` language server: a Rust binary, no external crates (the same ethos as `kelpc` and Coral) |
| `vscode/` | a VS Code extension: syntax highlighting, `lighthouse` wired up as the language client, and `coral build`/`run`/`check`/`clean` as VS Code tasks |
| `intellij/` | an IntelliJ **Ultimate** plugin (the LSP client API is not in Community): `.kp` file type, everything `lighthouse` offers, a Kelp New Project entry (`coral init`), a Coral run configuration, a gutter run icon on `fun main()`, and the project's `[toolchain]` pin in Settings |

## Two sources of truth

The split explains everything else about what the server can and cannot do.

**`kelpc` is the authority on what compiles.** On open and on save, the server
builds the current file's project and turns whatever `kelpc` prints on **stderr**
into diagnostics (squiggles, the Problems panel), grouped by the file each error
actually points at. For the one error shape it can confidently repair — a
misspelled bare-call name, `println` → `print` — it offers quick fixes ranked by
edit distance against the file's own `fun` declarations plus the free-standing
builtins (`print`, `print!`, `panic`, `assert`).

**Everything else comes from an index the server builds itself.** `kelpc` has no
machine-readable output and no way to ask it about a symbol, so
`server/src/index.rs` reads the project's `.kp` files — and the standard library
the compiler ships, which is embedded in the server — and answers from the text.

## Features

| Feature | What it does |
| --- | --- |
| Completion | Names in scope, this file's declarations, imported namespaces, builtins, keywords — and members after a `.`: a `datac`'s fields, an `enum`'s variants, `fun Type.method` declarations, and the compiler's own methods on `List`/`Map`/`Box`/`String`/`Bytes` |
| Auto-import | `str.con` completes to `concat`, **and accepting it writes `impl "std/str"` at the top of the file** — for the stdlib and for the project's own modules alike. The same fix is a code action on a name that resolves nowhere (`Import "shapes/circle" and qualify as circle.Circle`), and `impl "` completes module paths |
| Hover | The declaration as written, its `///` documentation, and where it came from. A binding shows the type the index could infer |
| Go-to-definition | Into a project file, or into the stdlib: a vendored copy of the shipped sources is compiled into the server and written to `~/.cache/lighthouse/stdlib/` on first jump, because `kelpc` keeps its stdlib inside the binary |
| Signature help | Parameter names and types, with the active argument tracked, including named arguments |
| Symbols and folding | Document outline (with `datac` fields and `enum` variants as children), workspace symbol search, brace and comment folding |
| References and rename | Across the workspace, token-aware: a name in a comment or a string is not a reference, and a rename cannot touch one |
| Inlay hints | The inferred type of a `val`/`var` whose initializer is a call or a field access |
| Organize imports | Sort, de-duplicate and drop unused `impl` lines (`source.organizeImports`) |
| Its own warnings | An `impl` whose namespace is never used, which `kelpc` does not report (`alias %*x*%` substitution in a file suppresses it, where the answer is unknowable) |

Two consequences worth knowing before trusting it:

!!! note "The index guesses; the compiler decides"
    A wrong guess costs a missing or lower-ranked completion. It can never produce
    a wrong edit on its own: every auto-import is a literal `impl` line the
    programmer sees in the diff, and every rename re-reads the text it is about to
    change.

`server/stdlib/*.kp` is a **snapshot** of `kelp/kelpc/std/*.kp`
(`server/tools/sync-stdlib.sh` regenerates it), because the compiler embeds its
stdlib rather than shipping it as files. Set `$KELP_SRC` to a kelp checkout to read
the live sources instead — which is what developing the two together wants.

## Using it

Both integrations find `lighthouse` and `kelpc`/`coral` the same way: `PATH` first,
with an escape hatch for a dev build that is not installed anywhere yet — `$LIGHTHOUSE`
and `$KELPC` for the server, the `kelp.lighthousePath` and `kelp.kelpcPath` settings
for the VS Code extension. The IntelliJ plugin additionally reads and writes the
project's `[toolchain] kelp` pin in `coral.toml`, so the IDE uses the project's
compiler rather than its own (see [Coral](coral.md#pinning-the-compiler)).

```sh
cd server
cargo build --release -p lighthouse
# put target/release/lighthouse and kelp's target/release/kelpc on PATH
```

The IntelliJ plugin is published to a self-hosted update site; the VS Code
extension is installed from a `.vsix` built locally. Neither is on the Marketplace.

## Tests

```sh
cd server && cargo test
```

Unit tests cover the scanner, the index (run against the real vendored stdlib),
the JSON parser and the analysis layer. `server/tests/lsp.rs` is end-to-end: it
starts a real server, speaks JSON-RPC to it over stdio, and checks the features on
a temporary project — including that auto-import arrives as one visible edit, that
a definition lands in a file, that a message the parser cannot read is skipped
rather than fatal, and that a source file full of non-ASCII does not end the
session.

## What is not here yet

- **Real diagnostics from `kelpc`** — spans instead of a single point, categories,
  warnings. Blocked on a machine-readable `kelpc check --json`, which is why
  `server/src/diagnostics.rs` still parses prose.
- **Whole-program resolution.** The index reads one file at a time and has no type
  checker: generic receivers (`fun Pair<A, B>.first`) resolve only when the call
  site spells the argument types, and a receiver reached through a long chain of
  calls usually cannot be typed. `kelpc` holds the answer and keeps it to itself.
- **Semantic tokens.** Highlighting is still the TextMate grammar in `vscode/` and
  the hand-written lexer in `intellij/`; a real parser would beat both, and
  `kelpc`'s own lexer is the only authoritative one.

!!! note "One stale line in the server's README"
    Lighthouse's README lists "Formatting. No `kelpc fmt` exists to call" as
    missing. That is out of date: `kelpc fmt` shipped, with `-w` and `--check`
    (see [`kelpc` CLI](kelpc-cli.md)). The missing piece is the server *calling*
    it, not the formatter.

## See also

- [`kelpc` CLI](kelpc-cli.md)
- [Coral](coral.md)
- [Install and build](../getting-started/install.md)
