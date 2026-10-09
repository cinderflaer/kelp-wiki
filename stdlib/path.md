---
title: "`std/path`"
description: "Lexical path handling - split, join, name, extension, normalize. Ungated, and purely textual - nothing here touches the filesystem, and nothing here knows whether the path exists."
isPublished: true
tags: "stdlib, filesystem"
---
Lexical path handling: split, join, name, extension, normalize. Ungated, and
purely textual: nothing here touches the filesystem, and nothing here knows
whether the path exists.

```kelp
impl "std/path"
```

| Function | Returns | Notes |
| --- | --- | --- |
| `is_absolute(s: &str)` | `bool` | true when the text starts with `/` |
| `normalize(s: &str)` | `String` | lexical normalization (see below) |
| `absolute(base: &str, p: &str)` | `String` | `p` resolved against `base`, then normalized |
| `last_sep(s: &str)` | `usize` | offset of the last `/`, or 0 when there is none |
| `file_name(s: &str)` | `&str` | everything after the last `/`: a borrow |
| `extension(s: &str)` | `&str` | after the last `.`, or `""` |
| `has_extension(s: &str, ext: &str)` | `bool` | |
| `stem(s: &str)` | `String` | the file name without its extension |
| `split(s: &str)` | `List<String>` | the path components |
| `join_all(parts: List<String>)` | `String` | takes the list by value |
| `parent(s: &str)` | `String` | everything before the last `/` |
| `join(a: &str, b: &str)` | `String` | `a` + separator + `b` |

`normalize` is the one to know about: the compiler's capability matcher uses the
same lexical normalization, and `fs` patterns are matched against a normalized,
symlink-resolved path. It is documented in
[`syntax.md` §15.2](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/syntax.md)
and implemented twice (in Kelp here and in C in the runtime) with the
differential tests comparing the two.

`absolute(base, p)` is the pair `normalize` needs: `p` alone when `p` is already
absolute, otherwise `base` with `p` appended, then the same `normalize` call. The
result is what an `fs` call accepts, because the capability check takes only an
absolute path without `..`. The base a command-line tool has is
[`fs.cwd()`](/stdlib/fs).

```kelp
impl "std/path"

fun main() {
    val p = "/srv/data/report.csv"
    print(path.is_absolute(p))
    print(path.file_name(p))
    print(path.extension(p))
    print(path.stem(p))
    print(path.parent(p))
    print(path.has_extension(p, "csv"))
    print(path.join("/srv/data", "other.txt"))
    val parts = path.split(p)
    print(parts.len())
    print(path.join_all(parts))
}
```

```
true
report.csv
csv
report
/srv/data
true
/srv/data/other.txt
... (one entry per component)
/srv/data/report.csv
```

## Notes

- `last_sep` returns 0 when there is no separator, which makes `file_name` return
  the whole string: the intended behaviour for a bare name.
- `extension` looks at the last `.` **anywhere** in the name, so `.gitignore`
  has the extension `gitignore` and no stem-to-speak-of. Check for the shapes you
  care about if that matters.
- There is no `canonicalize`: resolving symlinks needs the filesystem, so it
  lives in `std/fs`/the runtime and is what the capability check does.
- `absolute` is lexical like everything else here: it does not check that the
  result exists, and it cannot see a symlink. `fs.cwd()` supplies the base it
  usually resolves against.
- `absolute` panics when the base is not absolute, or when the join climbs above
  `/` with `..`: the same refusal `normalize` makes, for the same reason.
- Paths are bytes: strings are assumed UTF-8 and the separators are ASCII `/`.

## See also

- [`std/fs`](/stdlib/fs)
- [`fsx`](/libraries/fsx) for `write_atomic`, `copy_dir`, `tail`
- [Capability patterns](/reference/capability-patterns)
