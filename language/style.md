---
title: "Style"
description: "House style for Kelp: what kelpc fmt enforces, file order, naming, and the lint warnings for comments, else if and naming case."
isPublished: true
tags: "language"
---
Source: [`syntax.md` §19](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

## Rules the formatter enforces

`kelpc fmt` enforces indentation, spacing, trailing whitespace, the final newline
and comment rules, and nothing else:

- **4 spaces, no tabs**, and a hard 100-column limit (the limit is a review
  convention: `fmt` preserves your wrapping rather than re-wrapping).
- No semicolons.
- Do not wrap an expression across lines unless the wrap is inside parentheses or
  an argument list.
- One blank line between top-level declarations and between functions; `fmt` caps
  a run of blank lines at one but never inserts a blank line you did not write.
- Comments are `//`, written as full sentences when they explain a decision, and
  never to restate the next line. `/* ... */` is for the two things a line comment
  cannot do: a note that spans lines, and commenting out a region of code. Block
  comments nest, so commenting out a region that already contains one works.

`fmt` holds four invariants, and they are why it is safe to run on any file:

| Invariant | Means |
| --- | --- |
| idempotent | formatting a formatted file changes nothing |
| token-faithful | no token's text is ever rewritten: a formatted file is the same program |
| comment-preserving | comments survive exactly, including their position |
| new-inode | a rewritten file is a new inode, so a hard link to it keeps the old bytes |

```sh
kelpc fmt <file.kp>          # print formatted to stdout
kelpc fmt -w <path>...       # rewrite in place (file or directory, recursing .kp)
kelpc fmt --check <path>...  # exit non-zero without writing when unformatted
```

A path that is not a regular file (a FIFO, a socket, a device) is refused before
it is read. A symlink named on the command line is followed and rewritten; a link
found inside a directory is skipped and reported.

## File order

The parser enforces the steps of the canonical order: `impl`, then `alias`,
`const` and `pd`, then `datac`/`enum`/`fun`. The order inside the last group is
left to review.

```kelp
impl "std/fs"          // 1. imports
const LIMIT: i32 = 10  // 2. constants and passdowns
pd val app = "demo"
datac Point(val x: i32, val y: i32)   // 3. types and functions
fun main() {
    print(LIMIT)
}
```

## Naming

- Standard-library modules, functions and `datac` fields are `snake_case`
  (`fs.read_text`, `str.is_empty`, `Line.text`); types are `PascalCase`
  (`String`, `Bytes`, `Box`, `Metadata`, `Url`).
- The case of **your own** names is configurable, and it is the one style rule
  with a setting: `coral.toml`'s `naming_case`, `0` for `camelCase` (the
  default) or `1` for `snake_case`. `kelpc lint` reports a declared name that
  does not match it, so either case keeps compiling whatever the setting says. A
  file with no `coral.toml` to read gets the default.
- Type names stay `PascalCase` and `const` names stay `UPPER_SNAKE` whatever the
  setting says. A fetched dependency under `src/deps/` is not linted for its
  names at all: it is not your project's code.
- Use named arguments wherever a call would otherwise be ambiguous. In practice,
  that means every `datac` construction with two or more fields:
  `Circle(r = 2.0, x = 1.0)`.

## What `fmt` will not do

- It does not re-wrap long lines to the 100-column limit.
- It does not insert blank lines for you.
- It does not reorder declarations.
- It does not rename anything.

So the column limit, the order inside the last group and the naming rules need a
review, not a formatter. `kelpc lint` is where those live: it is warning-only,
so it never fails a build, and it reports three rules: the comment run, an
`else if` link written where `elif` is preferred, and the naming case.

## The comment run

Two or more consecutive `//` lines with no blank line and no code between them
suggest one `/* ... */` comment, and `kelpc lint` warns about each run it finds:

```text
$ kelpc lint notes.kp
warning: 3 consecutive '//' lines suggest one '/* ... */' comment
  --> notes.kp:2:5
```

A blank line, code, a block comment, or a doc comment (`///`, `//!`, see
[Lexical structure](/language/lexical#documentation-comments)) between two `//`
lines ends the run; so does a line where the comment follows code, because a run
is *lines* of comments. The finding is a warning and the exit status stays 0:
the author may have meant every line, and a style finding is not a build
failure. Running `kelpc lint` over this repository's own standard library prints
findings for its explanatory comment blocks, which is the suggestion rather than
a defect.

## The `else if` link

A chain link is written `elif`:

```text
warning: 'else if' compiles, but 'elif' is the preferred spelling
  --> server.kp:14:7
```

The `else if` spelling stays legal and compiles identically; the warning is a
reading preference and nothing more, and `kelpc fmt` never rewrites one into the
other, because it never rewrites a token.

## The naming case

The project's case comes from `coral.toml`:

```toml
naming_case = 1  # 0 = camelCase (the default), 1 = snake_case
```

`kelpc lint` checks the names a file **declares**: a `fun` name, a parameter, a
`val`/`var`/`pd` binding, a `datac` field, an enum payload field, a loop binding,
and a pattern binding (`if let Circle(r) = s`, `when s { Circle(r) -> .. }`).

```text
warning: function 'read_text' is snake_case, and this project asks for camelCase (coral.toml 'naming_case = 0'); write 'readText'
  --> io.kp:7:5
```

- A **call is a use, not a declaration**, and that is the whole of the standard
  library's exception: the stdlib keeps its locked `snake_case`, so a
  `camelCase` project is never warned about `str.is_empty`, and a `snake_case`
  project is never warned about the stdlib's `read_text` either.
- A leading `_` is not part of either case: `_unused` and `_unused_name` are an
  ordinary `camelCase` pair, and the underscore is kept in the suggestion.
- A file outside a project gets the default (`camelCase`). A file under the
  project's `src/deps/` gets no case rule at all.
- The suggestion is a starting point, not a rename: `lint` writes nothing, and
  `read_HTTP` is suggested as `readHttp` rather than guessed at.

## See also

- [`kelpc` CLI](/tooling/kelpc-cli)
- [Lexical structure](/language/lexical)
