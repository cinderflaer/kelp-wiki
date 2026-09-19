---
title: "glob_tree"
description: "Walks a directory tree, keeps the .kp files, counts their lines and prints a total. It is the smallest program here that combines a filesystem walk with a pattern filter."
isPublished: true
tags: "example, filesystem"
---
Walks a directory tree, keeps the `.kp` files, counts their lines and prints a
total. It is the smallest program here that combines a filesystem walk with a
pattern filter.

| | |
| --- | --- |
| Source | [`src/glob_tree.kp`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki-wikijs/raw/branch/main/examples/src/glob_tree.kp) |
| Needs | `glob = "Juniper/fpl/glob"` |
| Shows | `fs.walk`, `glob.glob_filter`, `fs.is_file`, `std/path`, a running total |

## The dependency

```toml
[dependencies]
glob = "Juniper/fpl/glob"
```

## The program

```kelp
impl "deps/glob/lib" as glob
impl "std/fs"
impl "std/str"
impl "std/fmt"
impl "std/process"
impl "std/path" as p

// Printing the file name keeps the output short; the walk returns full paths,
// and they are absolute because a gated call needs one.
fun report(path: &str, lines: usize) {
    val name = p.file_name(path)
    val number = fmt.int(lines.to_i64())
    val count = fmt.pad_left(number.as_str(), 6, ' ')
    val line = str.concat(count.as_str(), "  ")
    print(str.concat(line.as_str(), name))
}

fun main() {
    val argv = process.args()
    // Annotated, because `root = argv.get(1).clone()` assigns a `String`: a bare
    // `"."` would have made this binding a `str`.
    var root: String = "."
    if argv.len() >= 2 {
        root = argv.get(1).clone()
    }
    if !p.is_absolute(root.as_str()) {
        print("error: glob_tree takes an absolute directory (this language has no cwd accessor)")
        process.exit(2)
    }

    val everything = fs.walk(root.as_str())
    val candidates = glob.glob_filter("*.kp", everything)

    var total: i64 = 0
    var counted: i64 = 0
    var i: usize = 0
    while i < candidates.len() {
        val path = candidates.get(i)
        if fs.is_file(path.as_str()) {
            val lines = fs.read_lines(path.as_str())
            report(path.as_str(), lines.len())
            total += lines.len().to_i64()
            counted += 1
        }
        i += 1
    }

    val files = fmt.int(counted)
    val sum = fmt.int(total)
    val files_line = str.concat("files: ", files.as_str())
    val lines_line = str.concat("lines: ", sum.as_str())
    print("")
    print(files_line)
    print(lines_line)
}
```

## Run it

```sh
kelpc build glob_tree.kp -o glob_tree && ./glob_tree /absolute/directory
```

## Output

Run against this chapter's own `docs/examples/src` directory:

```
   151  cli_tool.kp
    72  csv_report.kp
    25  fib.kp
    68  glob_tree.kp
    43  http_fetch.kp
    43  json_filter.kp
    44  lines_client.kp
    60  lines_server.kp
    30  sandbox_main.kp
    18  sandbox_vault.kp
    54  tests_and_bench.kp
    80  wordcount.kp

files: 12
lines: 688
```

Those counts are the chapter's own sources at the time of the run, so they move
when the examples do.

## What to take from it

- **`fs.walk` returns full paths, and directories too.** The filter keeps the
  `.kp` names and `fs.is_file` drops the directories, which is why both calls are
  there. Without the second, the program would try to read a directory as a file.
- **A gated call takes an absolute path.** `fs.read_text("notes.txt")` panics with
  "is outside the fs capability granted to module ..." even under a `/**` grant,
  because there is no `cwd` accessor in v1 and the matcher compares absolute
  patterns. The example checks with `p.is_absolute` and exits 2 with a sentence
  instead of panicking. See the trap list in the
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
