---
title: "Count lines in a Kelp tree"
description: "Walks a directory tree, keeps the .kp files, counts their lines and prints a total: the smallest example that combines a walk with a pattern filter."
isPublished: true
tags: "example, filesystem"
---

The `count-lines-in-kelp-tree` program walks a directory tree.
It keeps the `.kp` files, counts the lines in each one, and prints a total.
It is the smallest example that combines a filesystem walk with a pattern filter.

| | |
| --- | --- |
| Source | [`src/count-lines-in-kelp-tree.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki-wikijs/raw/branch/main/examples/src/count-lines-in-kelp-tree.kp) |
| Needs | `glob = "Lilly/fpl/glob"` |
| Shows | `fs.walk`, `glob.glob_filter`, `fs.is_file`, `std/path`, a running total |

## The dependency

```toml
[dependencies]
glob = "Lilly/fpl/glob"
```

## The program

```kelp project
impl "deps/glob/lib"
impl "std/fs"
impl "std/process"
impl "std/path"

// Printing the file name keeps the output short; the walk returns full paths,
// and they are absolute because a gated call needs one.
fun report(file: str, lines: usize) {
    val name = path.file_name(file)
    val number = lines.toText()
    val count = fmt.pad_left(number.as_str(), 6, ' ')
    val line = str.concat(count.as_str(), "  ")
    print(str.concat(line.as_str(), name))
}

// A relative argument is resolved against the working directory, so the gated
// call still receives an absolute path: `fs` patterns are absolute, and the
// capability check normalizes before it matches.
fun absolute_or_here(name: str, here: str) => String {
    if path.is_absolute(name) {
        return String.from_str(name)
    }
    return path.absolute(here, name)
}

fun main() {
    val argv = process.args()
    // Annotated, because `raw = argv.get(1).clone()` assigns a `String`: a bare
    // `"."` would have made this binding a `str`. With no argument the walk
    // starts at the working directory, resolved to an absolute path because
    // every gated call needs one: patterns are absolute and the check
    // normalizes before it matches.
    var raw: String = "."
    if argv.len() >= 2 {
        raw = argv.get(1).clone()
    }
    val here = fs.cwd()
    val root = absolute_or_here(raw.as_str(), here.as_str())

    val everything = fs.walk(root.as_str())
    val candidates = glob.glob_filter("*.kp", everything)

    var total: i64 = 0
    var counted: i64 = 0
    var i: int = 0
    while i < candidates.len() {
        val entry = candidates.get(i)
        if fs.is_file(entry.as_str()) {
            val lines = fs.read_lines(entry.as_str())
            report(entry.as_str(), lines.len())
            total += lines.len().to_i64()
            counted += 1
        }
        i += 1
    }

    val files = counted.toText()
    val sum = total.toText()
    val files_line = str.concat("files: ", files.as_str())
    val lines_line = str.concat("lines: ", sum.as_str())
    print("")
    print(files_line)
    print(lines_line)
}
```

## Run it

```sh
kelpc build count-lines-in-kelp-tree.kp -o count-lines-in-kelp-tree && ./count-lines-in-kelp-tree [directory]
```

## Output

Run against this page's own `examples/src` directory:

```
    49  build-http-request-parts.kp
    60  checksums-encodings-dates.kp
    79  count-lines-in-kelp-tree.kp
    80  count-lines-words-bytes.kp
    43  download-url-to-file.kp
   118  exact-numeric-libraries.kp
    42  filter-json-by-score.kp
    78  list-and-set-helpers.kp
    54  pack-bit-fields.kp
    44  ping-pong-client.kp
    60  ping-pong-server.kp
    53  read-manifest-settings.kp
    25  recursive-fibonacci.kp
    30  sandbox-directory-grant.kp
    54  self-test-and-timing.kp
    68  terminal-table-and-logs.kp
    69  total-csv-column.kp
    20  vault.kp
   159  word-count-with-flags.kp

files: 19
lines: 1185
```

Those counts are the chapter's own sources at the time of the run, so they move
when the examples do.

## What to take from it

- **`fs.walk` returns full paths, and directories too.** The filter keeps the
  `.kp` names and `fs.is_file` drops the directories, which is why both calls are
  there. Without the second, the program would try to read a directory as a file.
- **A gated call takes an absolute path.** `fs.read_text("notes.txt")` panics with
  "is outside the fs capability granted to module ..." even under a `/**` grant,
  because the matcher compares absolute patterns, so a relative argument is
  resolved with `path.absolute(fs.cwd(), arg)` first. The directory argument is
  optional: with none, the walk starts at the working directory. See the trap
  list in the
  [chapter index](/examples#what-the-examples-deliberately-do-not-hide).
- **`glob_filter` clones what it keeps,** because a `List` only lends its elements
  by reference. The candidates are owned strings.
- **`usize` and `i64` are different types,** so the total is an `i64` from the
  start and each count is converted at the boundary: `lines.len().to_i64()`.
- **`str.concat` needs binds for both operands** when either is a temporary:
  `val files_line = str.concat("files: ", files.as_str())` is three lines where
  another language would write one. That is the price of `.as_str()` refusing a
  temporary.

## See also

- [`glob`](/libraries/glob) for the pattern language (`*` and `?`, nothing else)
- [`std/fs`](/stdlib/fs) for `walk`, `list` and `is_file`
- [`std/path`](/stdlib/path) for `file_name`, `is_absolute` and friends
