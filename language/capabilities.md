---
title: "Capabilities"
description: "Source section - syntax.md \u00a715."
isPublished: true
tags: "language, capability"
---
Source section:
[`syntax.md` §15](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

Kelp's headline feature: **a program cannot read a file, open a socket, spawn a
process or read the clock unless the module making the call was granted that
resource**, and the grant is written in the source.

```kelp
impl "std/http" with caps(net = ["127.0.0.1:*"])
impl "std/fs"
```

Those two lines are `examples/download.kp`'s entire network and filesystem
authority. "What can this code do?" is answered by the first few lines of a file
instead of by auditing it.

## The model

- Six domains: **`fs`**, **`net`**, **`process`**, **`env`**, **`time`**,
  **`rand`**.
- Each has a corresponding bare built-in namespace, and the *only* way to reach
  the outside is through a stdlib module that holds it (`kelpc/src/stdlib.rs`).
- **The entry module holds the wildcard for every domain**, so a single-file
  program needs no grant for its own calls.
- **Every other module holds exactly what its importer granted it, and nothing
  else.** A module can delegate less than it holds, never more: granting a pattern
  the importer does not hold is an error.
- Referencing a gated function without holding the domain is a **compile error
  naming the missing domain and the grant to write**: not a runtime refusal.

## Grants

```kelp
impl "std/fs"
impl "std/http" with caps(net = ["api.example.com:443", "127.0.0.1:*"])
impl "logger" with caps(fs = ["/var/log/myapp/**"], env = ["LOG_*"])
```

A grant is `domain = [pattern, ...]`. Two domains in one line are fine. An **empty
pattern list denies everything**: `with caps(process = [])` is a grant that
permits no program, which is also the smallest grant a consumer can write to
satisfy the compiler for a module it does not actually want to let out.

### Patterns

| Domain | Pattern forms | Matching |
| --- | --- | --- |
| `net` | `host`, `host:port`, `*.host`, `*:port`, `*` | against the **host string the program wrote**, never a resolved address |
| `fs` | absolute paths, `*` within a component, `**` across components | path normalized lexically and symlinks resolved **before** matching |
| `process` | absolute program paths | same normalization as `fs` |
| `env` | names, `*` | name matching |
| `time`, `rand` | no pattern | an empty list is the whole grant |

Consequences worth internalizing:

- `127.0.0.1:*` does **not** cover `localhost`, even though both are this machine.
  Two spellings of one address can fall under different grants, and the HTTP
  connection pool is keyed on the host as written for exactly that reason.
- A symlink inside a granted directory that points outside it is denied, because
  resolution happens first.
- **An `fs` path passed to a gated call must be absolute and must not contain
  `..`.**

## Library grants

A library declares the grant it needs, and the *consumer* decides the pattern at
its own `impl` line:

```kelp
impl "deps/fsx/lib" with caps(fs = ["/var/lib/myapp/**"])
impl "deps/log/lib" with caps(time = [])
impl "deps/lineproto/lib" with caps(net = ["127.0.0.1:*"])
```

`fsx` needs `fs`, `log` and `benchkit` need `time`, `term` needs `env` for
`NO_COLOR`, and `lineproto` needs `net`. A library holding no authority (`json`, `hash`, `month`-style arithmetic) needs
nothing, and that is a property you can
check by reading one line.

There is a subtle case worth knowing: a module can hold a domain *without using
it*, purely to satisfy the compiler on behalf of its own imports. `httpx` is the
example: it only builds and reads plain data, but importing `std/http` needs
`net` delegated, so `httpx` writes `with caps(net = [])` internally: the smallest
grant that compiles, and it never dials.

When that delegation is missing and the failing module is **not** the one you
wrote the call in, the diagnostic points at the link that broke: it names the
`impl` line that imported the module with no `caps(...)` clause, and that line is
the one to change.

## Why this is checkable

The capability matcher exists twice on purpose: in Kelp (`std/rt`, which is
compiler-internal and not importable) and in C in `kelpc/runtime/`, with
differential tests comparing the two on a corpus. A grant is checked statically
*and* enforced at runtime against the pattern list, so neither a compiler bug nor
a library trick widens authority.

## Testing a restriction

The entry module holds everything, so the interesting module sits one level down:

```kelp
// sandbox.kp — a module with exactly one directory
impl "std/fs" with caps(fs = ["/srv/data/**"])
impl "std/str"

fun read(name: &str).R: String = fs.read_text(str.concat("/srv/data/", name))
```

Anything outside `/srv/data/**` is refused at the call, and the caller sees the
failure as a panic from the gated call.

## See also

- [Capability patterns](/reference/capability-patterns): the pattern grammar in full
- [`std/fs`](/stdlib/fs), [`std/net`](/stdlib/net), [`std/process`](/stdlib/process),
  [`std/env`](/stdlib/env), [`std/time`](/stdlib/time), [`std/rand`](/stdlib/rand)
- [Compiler](/compiler): how the check is implemented
