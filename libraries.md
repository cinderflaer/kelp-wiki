---
title: "Libraries (fpl)"
description: "fpl is the first-party Kelp library catalogue - one folder per library in a single repository, twenty-six of them at the time of writing."
isPublished: true
tags: "library"
---
`fpl` is the first-party Kelp library catalogue: one folder per library in a
single repository, twenty-six of them at the time of writing.

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
impl "deps/json/lib"
impl "deps/hash/lib"
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
   same helper, they either carry their own copy (`httpx` holds a base64 encoder,
   and `url` a percent codec, because neither may import `encoding`) or they stop
   being two libraries.
4. **Publishing is pushing.** A library has no version, so there is nothing to
   tag: the next `coral sync` on any consumer takes the branch tip.

Every library targets `kelpc 0.1.5` or newer. `json` uses `str.less` and a
closure over its own `Json` type; `decimal`, `encoding`, `httpx` and `url` use
`str.is_digit`. Both helpers and the closure codegen landed in that release, so
an older compiler refuses those files at codegen rather than at the manifest.

Some libraries are **gated** exactly like a `std/*` module, because they wrap one:
the consumer delegates the capability at the `impl` line.

```kelp
impl "deps/fsx/lib" caps(fs = ["/var/lib/myapp/**"])
impl "deps/log/lib" caps(time = [])
impl "deps/lineproto/lib" caps(net = ["127.0.0.1:*"])
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

- [Catalogue](/libraries/catalogue): all twenty-six, grouped by what they do
- [Writing a library](/libraries/writing-a-library): what a library has to be

## See also

- [Projects and coral.toml](/getting-started/projects): the manifest side
- [Capabilities](/language/capabilities): what a grant means
