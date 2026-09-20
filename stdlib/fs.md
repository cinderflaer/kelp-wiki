---
title: "`std/fs`"
description: "Files and directories. Gated on fs."
isPublished: true
tags: "stdlib, filesystem"
---
Files and directories. **Gated on `fs`.**

```kelp
impl "std/fs"                                    // the entry module holds the wildcard
impl "std/fs" caps(fs = ["/srv/data/**"])   // a library, granted a pattern
```

`fs` patterns are **absolute paths**, normalized lexically and resolved through
symlinks *before* matching, so a symlink inside the grant that points outside it
is denied. The grant is the ceiling for the whole module.

## Types

```kelp
datac Metadata(val size: u64, val mtime: i64, val mode: u32, val is_dir: bool, val is_file: bool)
```

`Metadata` follows a symlink: every field describes what the path resolves to.
`is_symlink` is the predicate that describes the link itself.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `read(path)` | `Bytes` | whole file |
| `read_text(path)` | `String` | whole file as text |
| `write(path, data)` | `Unit` | truncates and writes |
| `write_text(path, text)` | `Unit` | takes the `String` by value |
| `append(path, data)` | `Unit` | |
| `exists(path)` | `bool` | |
| `is_file(path)` / `is_dir(path)` | `bool` | follows a symlink |
| `is_symlink(path)` | `bool` | `lstat`: true for the link itself, broken ones included |
| `read_link(path)` | `String` | the stored target text; panics when the path is not a link |
| `cwd()` | `String` | the process's working directory, absolute |
| `size(path)` | `u64` | |
| `metadata(path)` | `Metadata` | size, mtime, mode, kind |
| `remove(path)` | `Unit` | |
| `remove_all(path)` | `Unit` | recursive; unlinks a symlink rather than descending it |
| `rename(from, to)` | `Unit` | atomic within one filesystem |
| `mkdir(path)` | `Unit` | |
| `mkdir_all(path)` | `Unit` | creates parents |
| `list(path)` | `List<String>` | entry names in one directory |
| `walk(dir)` | `List<String>` | every path below, recursively; reports a symlink but does not descend it |
| `copy(from, to)` | `Unit` | one file |
| `symlink(target, link)` | `Unit` | |
| `touch(path)` | `Unit` | |
| `sync(path)` | `Unit` | flush to disk |
| `open(path, mode)` | `io.File` | |
| `read_lines(path)` | `List<String>` | the file, split on newlines |
| `temp_path(prefix)` | `String` | a fresh path in the temp directory |

### Open modes

`fs.open(path, mode)` takes a mode string; the runtime maps it to the C `fopen`
modes (`"r"`, `"w"`, `"a"`, and their `+`/`b` forms).

## Errors are panics

There is no `Result` here: a failing syscall **panics** with the errno, and a path
outside the grant is refused by the capability check. Code that must survive a
missing file checks `exists`/`is_file` first, or uses the fallible forms where a
library provides them.

```kelp
impl "std/fs"

fun main() {
    val path = "/tmp/kelp-example.txt"
    fs.write_text(path, "line one\nline two\n")
    print(fs.exists(path))
    print(fs.size(path))

    val text = fs.read_text(path)
    print(text)

    val entries = fs.list("/tmp")
    print(entries.len() >= 0)

    fs.append(path, Bytes.from_str("line three\n"))
    print(fs.read_lines(path).len())

    fs.remove(path)
    print(fs.exists(path))
}
```

## Notes

- `list` returns **names**, not paths; join them with
  [`path.join`](/stdlib/path) or use `walk`, which returns full paths.
- `is_file` and `is_dir` **follow** a symlink, so both answer for what it
  points at; `is_symlink` answers for the link. A broken link is `true` for
  `is_symlink` and `false` for both of the others.
- `walk` and `remove_all` **do not descend** a symlink: `walk` reports it as an
  entry and `remove_all` unlinks it. A link back up the tree therefore cannot
  make either one run until the kernel refuses the path length, and a recursive
  delete of one directory can no longer reach into another one it was not given.
- `read_link` returns the target exactly as it was stored, so a relative target
  stays relative (to the link's own directory); join it with
  `path.parent(link)` when you need the resolved location.
- `cwd()` matches no pattern: holding `fs` is the whole grant, because a call
  with no path argument has nothing to match. Resolve a relative argument with
  `path.absolute(fs.cwd(), arg)`; the capability check takes only an absolute
  path free of `..`, so a bare `"notes.txt"` cannot be passed to `read` at all.
- `remove` on a directory fails; `remove_all` is the recursive one.
- `copy` is files-only. A recursive copy is
  [`fsx.copy_dir`](/libraries/fsx), which is also where `write_atomic`
  (write-then-rename) lives: `write_text` truncates in place, so a crash
  mid-write leaves a half-file.
- `Metadata.mode` is the raw mode bits; the boolean `is_dir`/`is_file` are what
  most callers want.
- `temp_path` returns a name; it does not create the file.

## See also

- [`std/path`](/stdlib/path) for textual path handling
- [`std/io`](/stdlib/io) for `File` and buffered reading
- [`fsx`](/libraries/fsx) for the compositions the stdlib stops short of
- [Capability patterns](/reference/capability-patterns)
