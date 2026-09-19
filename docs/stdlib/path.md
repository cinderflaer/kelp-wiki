# `std/path`

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
[`syntax.md` §15.2](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md)
and implemented twice (in Kelp here and in C in the runtime) with the
differential tests comparing the two.

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
- Paths are bytes: strings are assumed UTF-8 and the separators are ASCII `/`.

## See also

- [`std/fs`](fs.md)
- [`fsx`](../libraries/fsx.md) for `write_atomic`, `copy_dir`, `tail`
- [Capability patterns](../reference/capability-patterns.md)
