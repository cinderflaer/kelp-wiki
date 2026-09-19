---
title: "`fsx`: composition over `std/fs`"
description: "Atomic writes, a recursive directory copy, a text tail, and a byte-for-byte file comparison."
isPublished: true
tags: "library, filesystem"
---
Atomic writes, a recursive directory copy, a text `tail`, and a byte-for-byte
file comparison.

**Gated on `fs`**, exactly like `std/fs`: the module itself touches the
filesystem, so the importer must grant it a pattern.

```toml
[dependencies]
fsx = "Juniper/fpl/fsx"
```

```kelp
impl "deps/fsx/lib" as fsx with caps(fs = ["/var/lib/myapp/**"])
```

`fs` patterns are absolute paths, normalized lexically and resolved through
symlinks before matching, so a symlink inside the grant that points outside it is
denied. The grant is the ceiling for the whole module: a helper that reads a file
needs the module holding the `impl` to have been granted it.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `write_atomic(path: &str, data: Bytes)` | `Unit` | writes to `<path>.fsx-tmp`, then `rename`s it over `path`. A rename within one filesystem is atomic, so a reader never observes a partially written file. **Panics** under the same conditions `fs.write`/`fs.rename` do, including when `path` is outside the grant |
| `copy_dir(from: &str, to: &str)` | `Unit` | recursively copies `from` onto `to`, creating directories as needed. `from` should not have a trailing `/`. **Panics** under the same conditions `fs.list`/`fs.mkdir_all`/`fs.copy` do |
| `tail(path: &str, n: usize)` | `List<String>` | the last `n` lines of a text file |
| `files_equal(a: &str, b: &str)` | `bool` | byte-for-byte; **panics** if either file cannot be read |

`write_atomic` leaves a `<path>.fsx-tmp` behind if the rename fails. `copy_dir`
replaces a same-named file, but does not delete extra files already in `to`.

### `tail` and trailing newlines

A file ending in `\n` counts the empty piece after the final newline as one more
line, the same way `str.split` does for any trailing separator. So
`tail("a\nb\n", 2)` is `["b", ""]`. Trim the file's own trailing newline first if
that is not what you want.

## Example

```kelp
impl "deps/fsx/lib" as fsx with caps(fs = ["/tmp/fplverify/**"])

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
- `copy_dir` is the walk `std/fs` stops short of: `fs.copy` copies one file
  only. `fsx` itself is a folder and cannot import another folder in this repo,
  so anything more (a filtered copy, a size cap) belongs in the caller.
- `tail` reads the whole file and splits it; it is not a seek-from-end.
- `files_equal` compares by reading both files whole.
