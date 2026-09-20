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
impl "std/http" caps(net = ["127.0.0.1:*"])
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
- **Every item a gated module declares is gated**, not only the wrapper
  functions a program normally calls: the `extern fun` primitives behind them
  and the module's receiver methods are gated names too, so `fs.read_raw` and
  `process.Child.kill` are refused in a module that does not hold the domain.
  The module that declares an item is the one module exempt from the gate, which
  is what lets a wrapper call its own primitive.
- A gated item is gated **wherever it is named**: a direct call, a receiver
  method call, a name used as a function value, a closure body and a `pd`
  initializer all go through the same gate.
- **The entry module holds the wildcard for every domain**, so a single-file
  program needs no grant for its own calls.
- **Every other module holds exactly what its importer granted it, and nothing
  else.** A module can delegate less than it holds, never more: granting a pattern
  the importer does not hold is an error.
- Referencing a gated item without holding the domain is a **compile error
  naming the missing domain and the grant to write**: not a runtime refusal.
  Holding the domain is the whole check for an item that names no resource
  (`fs.cwd`, `time.now_mono_ns`, a receiver method); an item that does name one
  is additionally checked against the patterns at the call.

## Grants

```kelp
impl "std/fs"
impl "std/http" caps(net = ["api.example.com:443", "127.0.0.1:*"])
impl "logger" caps(fs = ["/var/log/myapp/**"], env = ["LOG_*"])
```

A grant is `domain = [pattern, ...]`. Two domains in one line are fine. An **empty
pattern list denies everything**: `caps(process = [])` is a grant that
permits no program, which is also the smallest grant a consumer can write to
satisfy the compiler for a module it does not actually want to let out.

The `with` that used to introduce the clause (`impl "std/fs" with caps(...)`) is
**outdated**: it still compiles, and a build prints an `outdated:` finding naming
it. Drop it and the grant is unchanged.

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
  `..`.** Build one from a relative argument with
  `path.absolute(fs.cwd(), arg)`: `fs.cwd()` reads the process's working
  directory, it matches no pattern (holding `fs` is the whole grant for a call
  with no path argument), and `path.absolute` normalizes the join so the check
  accepts the result.

## Library grants

A library declares the grant it needs, and the *consumer* decides the pattern at
its own `impl` line:

```kelp
impl "deps/fsx/lib" caps(fs = ["/var/lib/myapp/**"])
impl "deps/log/lib" caps(time = [])
impl "deps/lineproto/lib" caps(net = ["127.0.0.1:*"])
```

`fsx` needs `fs`, `log` and `benchkit` need `time`, `term` needs `env` for
`NO_COLOR`, and `lineproto` needs `net`. A library holding no authority (`json`, `hash`, `month`-style arithmetic) needs
nothing, and that is a property you can
check by reading one line.

There is a subtle case worth knowing: a module can hold a domain *without using
it*, purely to satisfy the compiler on behalf of its own imports. `httpx` is the
example: it only builds and reads plain data, but importing `std/http` needs
`net` delegated, so `httpx` writes `caps(net = [])` internally: the smallest
grant that compiles, and it never dials.

When that delegation is missing and the failing module is **not** the one you
wrote the call in, the diagnostic points at the link that broke: it names the
`impl` line that imported the module with no `caps(...)` clause, and that line is
the one to change.

## Why this is checkable

The capability matcher exists twice on purpose: in Kelp (the compiler's own
runtime module, `std/rt`) and in C in `kelpc/runtime/`, with differential tests
comparing the two on a corpus. A grant is checked statically *and* enforced at
runtime against the pattern list, at every call site that names a resource: a
wrapper, the primitive behind it, a receiver method, a closure body and a `pd`
initializer are each checked against the grant of the module they are written
in.

One shape is not covered yet: a gated item named as a *function value*
(`val f = fs.read`) and called through the pointer. Holding the domain is needed
to name it, but the pattern check is emitted from the call's own callee, and an
indirect call has no callee in the source, so a narrowed grant does not reach
that call: the wrapper spelling builds under *both* backends and reads outside the
grant (measured at compiler commit `2593e3e`). Only the `extern fun` spelling
(`val f = fs.read_raw`) is refused by name, and only by `--backend=asm`, which has
no symbol to take the address of; the C backend builds that one too. `BUG-k2Qv7`
is the open report for the C side. Nothing in the shipped stdlib or in the
examples uses a gated item as a value.

## Testing a restriction

The entry module holds everything, so the interesting module sits one level down:

```kelp
// sandbox.kp — a module with exactly one directory
impl "std/fs" caps(fs = ["/srv/data/**"])
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
