# Libraries (fpl)

`fpl` is the first-party Kelp library catalogue: one folder per library in a
single repository, twenty-five of them at the time of writing.

Unlike the standard library, which is compiled into `kelpc` and imported as
`std/…`, every fpl library is a **dependency you fetch**: a folder from a git
remote, landed in your project's `src/deps/`.

```toml
# coral.toml
[dependencies]
json = "Juniper/fpl/json"
hash = "Juniper/fpl/hash"
```

```kelp
impl "deps/json/lib" as json
impl "deps/hash/lib" as hash
```

## The four rules that shape the catalogue

1. **A dependency is a folder.** A consumer depends on `json`, not on `fpl`, so it
   gets `json` and nothing else. Two libraries are two manifest lines, and neither
   fetches the other.
2. **There is no version and no lockfile.** A dependency is a git remote and
   `coral sync` takes its tip. What makes a build reproducible is that
   `src/deps/<name>/` *is* the tree it built with, and `coral build` never touches
   a dependency that is already there.
3. **A folder must stand alone.** Only the named folder is fetched, so a library
   here cannot `impl` another one: the sibling was never downloaded and there is
   no `deps/fpl/...` in the consumer's tree to name. When two libraries need the
   same helper, they either carry their own copy (`httpx` and `encoding` both
   hold a base64 encoder) or they stop being two libraries.
4. **Publishing is pushing.** A library has no version, so there is nothing to
   tag: the next `coral sync` on any consumer takes the branch tip.

Some libraries are **gated** exactly like a `std/*` module, because they wrap one:
the consumer delegates the capability at the `impl` line.

```kelp
impl "deps/fsx/lib" as fsx with caps(fs = ["/var/lib/myapp/**"])
impl "deps/log/lib" as log with caps(time = [])
impl "deps/lineproto/lib" as lineproto with caps(net = ["127.0.0.1:*"])
```

| Library | Needs |
| --- | --- |
| `fsx` | `fs` |
| `log`, `benchkit` | `time` |
| `term` | `env` (`NO_COLOR`) |
| `lineproto` | `net` |
| everything else | nothing |

## Reading a library page

Each page in this chapter is written to the same shape: what it is, the dependency
line and capability grant, the whole API with argument and panic behaviour, an
example whose output was checked against `kelpc`, and what it deliberately does
**not** do. The library's own source is one file, `lib.kp`, in the
[fpl repository](https://homelabone.xenoo.dev/gittea/Juniper/fpl).

## Pages

- [Catalogue](catalogue.md): all twenty-five, grouped by what they do
- [Writing a library](writing-a-library.md): what a library has to be

## See also

- [Projects and coral.toml](../getting-started/projects.md): the manifest side
- [Capabilities](../language/capabilities.md): what a grant means
