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
is denied, and so is a write through a link whose target does not exist yet. The
grant is the ceiling for the whole module.

## Types

```kelp
datac Metadata(val size: u64, val mtime: i64, val mode: u32, val is_dir: bool, val is_file: bool)
```

`Metadata` follows a symlink: every field describes what the path resolves to.
`is_symlink` is the predicate that describes the link itself.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `read(path)` | `Result<Bytes, io.IoErr>` | whole file, as owned bytes |
| `read_text(path)` | `Result<String, io.IoErr>` | whole file as text; a file that is not UTF-8 is an `Err` |
| `write(path, data)` | `Result<unit, io.IoErr>` | truncates and writes |
| `write_text(path, text)` | `Result<unit, io.IoErr>` | takes the `String` by value |
| `append(path, data)` | `Result<unit, io.IoErr>` | |
| `exists(path)` | `bool` | |
| `is_file(path)` / `is_dir(path)` | `bool` | follows a symlink |
| `is_symlink(path)` | `bool` | `lstat`: true for the link itself, broken ones included |
| `read_link(path)` | `String` | the stored target text; panics when the path is not a link |
| `cwd()` | `String` | the process's working directory, absolute |
| `size(path)` | `u64` | |
| `metadata(path)` | `Metadata` | size, mtime, mode, kind |
| `remove(path)` | `Result<unit, io.IoErr>` | a file or an empty directory |
| `remove_all(path)` | `Result<unit, io.IoErr>` | recursive; unlinks a symlink rather than descending it; stops at the first failure |
| `rename(from, to)` | `Result<unit, io.IoErr>` | atomic within one filesystem |
| `mkdir(path)` | `Unit` | |
| `mkdir_all(path)` | `Result<unit, io.IoErr>` | creates parents |
| `list(path)` | `Result<List<String>, io.IoErr>` | entry names in one directory |
| `walk(dir)` | `List<String>` | every path below, recursively; reports a symlink but does not descend it |
| `copy(from, to)` | `Unit` | one file |
| `symlink(target, link)` | `Result<unit, io.IoErr>` | |
| `touch(path)` | `Unit` | |
| `set_mode(path, mode)` | `Unit` | sets the low 12 permission bits, the ones `Metadata.mode` reads; `493` is octal 755 |
| `sync(path)` | `Unit` | flush to disk |
| `open(path, mode)` | `Result<io.File, io.IoErr>` | see [open modes](#open-modes) |
| `read_lines(path)` | `List<String>` | the file, split on newlines |
| `temp_path(prefix)` | `String` | a fresh, empty file in the temp directory |

### Open modes

`fs.open(path, mode)` takes one of four mode strings: `"r"`, `"w"` (create and
truncate), `"a"` (create and append) and `"rw"` (create, no truncate). Anything
else is an `Err` with `errno` `EINVAL` (22). There are no `+`/`b` spellings: a
`"b"` is a no-op on POSIX and `"rw"` is what `+` would mean.

`read_text` fails on a file that is not valid UTF-8 as well, with `errno` 0
(no syscall failed) and a message that says so.

## Errors are values

A fallible function returns `Result`. Its `Err` is an `io.IoErr`, which carries
the POSIX `errno` (for a branch on the cause) and its text (for a message). A
unit operation returns `Result<unit, io.IoErr>`, so `Ok(())` is the success
value. Code that must survive a missing file checks `exists` or `is_file` first,
or matches the result:

```kelp
when fs.read_text(path) {
    Ok(text) -> print(text)
    Err(e) -> print(e.message)
}
```

A program that wants a panic on failure wraps the call in `result.expect`, with
the message it should print. A path outside the grant is still refused by the
capability check, and that refusal is not a value:

```kelp
impl "std/fs"
impl "std/result"

val text = result.expect(fs.read_text(path), "cannot read the config")
```

The fallible forms are the ones a tool needs when it is walking a tree the
author did not write.

```kelp
when fs.mkdir_all(dir) {
    Ok(_) -> print("ready")
    Err(e) -> print(e.message)
}
```

```kelp
impl "std/fs"
impl "std/result"

fun main() {
    val path = "/tmp/kelp-example.txt"
    result.expect(fs.write_text(path, "line one\nline two\n"), "write")
    print(fs.exists(path))
    print(fs.size(path))

    val text = result.expect(fs.read_text(path), "read")
    print(text)

    val entries = result.expect(fs.list("/tmp"), "list")
    print(entries.len() >= 0)

    result.expect(fs.append(path, Bytes.from_str("line three\n")), "append")
    print(fs.read_lines(path).len())

    result.expect(fs.remove(path), "remove")
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
- `temp_path` **creates** the file as well as naming it: it is built on
  `mkstemp`, so the returned path is a fresh, empty file, not a free name.
  Nothing removes it for you: call `fs.remove` on the path when you are done,
  or the file stays behind.

## See also

- [`std/path`](/stdlib/path) for textual path handling
- [`std/io`](/stdlib/io) for `File` and buffered reading
- [`fsx`](/libraries/fsx) for the compositions the stdlib stops short of
- [Capability patterns](/reference/capability-patterns)
