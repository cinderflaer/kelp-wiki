---
title: "`fsx`: composition over `std/fs`"
description: "Atomic writes, a recursive directory copy, a text tail, a byte-for-byte file comparison, and a depth-capped walk that skips what nobody may read."
isPublished: true
tags: "library, filesystem"
---
Atomic writes, a recursive directory copy, a text `tail`, a byte-for-byte file
comparison, and a depth-capped walk with a skip for what nobody may read.

**Gated on `fs`**, exactly like `std/fs`: the module itself touches the
filesystem, so the importer must grant it a pattern.

```toml
[dependencies]
fsx = "Lilly/fpl/fsx"
```

```kelp
impl "deps/fsx/lib" caps(fs = ["/var/lib/myapp/**"])
```

`fs` patterns are absolute paths, normalized lexically and resolved through
symlinks before matching, so a symlink inside the grant that points outside it is
denied. The grant is the ceiling for the whole module: a helper that reads a file
needs the module holding the `impl` to have been granted it.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `write_atomic(path: &str, data: Bytes)` | `Unit` | writes to `<path>.fsx-tmp`, then `rename`s it over `path`. A rename within one filesystem is atomic, so a reader never observes a partially written file. **Panics** under the same conditions `fs.write`/`fs.rename` do, including when `path` is outside the grant |
| `copy_dir(from: &str, to: &str)` | `Unit` | recursively copies `from` onto `to`, creating directories as needed. `from` should not have a trailing `/`. **Panics** under the same conditions `fs.list`/`fs.mkdirAll`/`fs.copy` do |
| `tail(path: &str, n: usize)` | `List<String>` | the last `n` lines of a text file |
| `files_equal(a: &str, b: &str)` | `bool` | byte-for-byte; **panics** if either file cannot be read |
| `survey(root: &str, max_depth: usize, keep: closure fun(&PathInfo) => bool)` | `Survey` | walks `root` depth-first to `max_depth` levels, keeping the files `keep` accepts. `keep` is a callback, so this module needs no glob: the caller writes the match |
| `walk_files(root: &str, max_depth: usize)` | `List<String>` | the paths of every readable file under `root`, and nothing else about them |
| `any_path(p: &PathInfo)` | `bool` | always true, for a walk with no filter |
| `file_readable(mode: u32)` / `dir_listable(mode: u32)` | `bool` | the mode-bit tests `survey` uses |

`write_atomic` leaves a `<path>.fsx-tmp` behind if the rename fails. `copy_dir`
replaces a same-named file, but does not delete extra files already in `to`.

### The walk

`Survey` is the walk's result, and the two counts in it are what make a walk over
a tree you do not own honest:

```kelp
datac PathInfo(val path: String, val name: String, val size: u64, val mtime: i64, val mode: u32)
datac Survey(val dirs: usize, val files: List<PathInfo>, val unreadable: usize, val too_deep: usize)
```

- `dirs` counts the directories it descended into, `files` is what `keep`
  accepted.
- `unreadable` counts the paths it skipped because no read bit was set on a file,
  or no read and search bit was set on a directory. `std/fs.list` returns an `Err` for a
directory it may not read, so this is the difference between surveying a tree and
dying on it. The test is the mode bits only, so a file that is mode-readable but
  unreadable in practice (owned by someone else, mode `0400`) passes the filter;
  the caller who then reads it should use `fs.read`/`fs.readText`, which
  report the failure as an `Err` instead of panicking on it.
- `too_deep` counts the directories at the ceiling that were not descended into.

That ceiling is a safety valve for huge trees, and it is also still what bounds
a tree that is simply deep. A cycle is no longer part of the problem: `survey`
**does not descend a symlink**, because `fs.isSymlink` tells one from the
directory it points at, so a link back up the tree is skipped instead of walking
until the kernel refuses the path length.

### `tail` and trailing newlines

A file ending in `\n` counts the empty piece after the final newline as one more
line, the same way `str.split` does for any trailing separator. So
`tail("a\nb\n", 2)` is `["b", ""]`. Trim the file's own trailing newline first if
that is not what you want.

## Example

```kelp project
impl "deps/fsx/lib" caps(fs = ["/tmp/fplverify/**"])

fun main() {
    fsx.write_atomic("/tmp/fplverify/fsxtest/a.txt", Bytes.from_str("line1\nline2\nline3\n"))
    print(fsx.files_equal("/tmp/fplverify/fsxtest/a.txt", "/tmp/fplverify/fsxtest/a.txt"))
    val lines = fsx.tail("/tmp/fplverify/fsxtest/a.txt", 2)
    print(lines.len())
    print(lines.get(0).as_str())
    fsx.copy_dir("/tmp/fplverify/fsxtest/src", "/tmp/fplverify/fsxtest/dst")
}
```

With `/tmp/fplverify/fsxtest/src` present, output:

```
true
2
line3
```

## Notes

- `write_atomic` is the point of the library: `std/fs.write` truncates in place,
  so a crash mid-write leaves a half-written file.
- `copy_dir` is the walk `std/fs` stops short of: `fs.copy` copies one file only.
  `fsx` itself is a folder and cannot import another folder in this repo, so
  anything more (a filtered copy, a size cap) belongs in the caller.
- `tail` reads the whole file and splits it; it is not a seek-from-end.
- `files_equal` compares by reading both files whole.
- `survey` calls `fs.metadata` once per entry, and `fs.metadata` fills a
  `Metadata` from one `stat`, so the walk pays one syscall per entry rather than
  the five it charged before: a large tree is no longer syscall-bound before it
  is I/O-bound.
