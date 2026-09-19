# Style

Source section:
[`syntax.md` §19](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

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
  never to restate the next line.

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
fun main() { ... }
```

## Naming

- Standard-library modules, functions and `datac` fields are `snake_case`
  (`fs.read_text`, `str.is_empty`, `Line.text`); types are `PascalCase`
  (`String`, `Bytes`, `Box`, `Metadata`, `Url`).
- User code case is **not** enforced. The plan and the examples use `snake_case`
  for functions and lowercase for bindings, matching the standard library.
- Named arguments are used wherever a call would otherwise be ambiguous: in
  practice every `datac` construction with two or more fields:
  `Circle(r = 2.0, x = 1.0)`.

## What `fmt` will not do

- It does not re-wrap long lines to the 100-column limit.
- It does not insert blank lines for you.
- It does not reorder declarations.
- It does not rename anything.

So the column limit, the order inside the last group and the naming rules need a
review, not a formatter: `kelpc` has no `lint` command.

## See also

- [`kelpc` CLI](../tooling/kelpc-cli.md)
- [Lexical structure](lexical.md)
