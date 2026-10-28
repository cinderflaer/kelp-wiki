---
title: "Capability patterns"
description: "Source section - syntax.md \u00a715.2."
isPublished: true
tags: "reference, capability"
---
Source section:
[`syntax.md` §15.2](/design/syntax).

A grant is written on the `impl` line that acquires it:

```kelp
impl "std/fs"
impl "std/http" caps(net = ["api.example.com:443", "127.0.0.1:*"])
impl "logger" caps(fs = ["/var/log/myapp/**"], env = ["LOG_*"])
```

`domain = [pattern, ...]`, one or more domains, in any order, or the whole set in
one clause, `caps(*)` (see [Delegation](#delegation)). **An empty list
denies everything**: `caps(process = [])` is a grant that permits no program. It is also the smallest grant that satisfies
the compiler for a module you do not want to let out.

## Pattern grammar by domain

| Domain | Forms | Matched against |
| --- | --- | --- |
| `net` | `host`, `host:port`, `*.host`, `*:port`, `*` | the **host string the program wrote** |
| `fs` | absolute path, `*` within one component, `**` across components | a path normalized lexically and **symlink-resolved** first |
| `process` | absolute program path, same wildcards as `fs` | the program path, normalized as for `fs` |
| `env` | variable name, `*` | the name string |
| `time` | no pattern | (an empty list is the whole grant) |
| `rand` | no pattern | (an empty list is the whole grant) |
| `machine` | no pattern | (an empty list is the whole grant) |
| `ui` | `*` only | the domain gate alone: no display call names the display |
| `mmio` | `0xBASE+LEN`, or `*` | the byte range of a device register block; `LEN` counts bytes |
| `frames` | `0xBASE+LEN`, or `*` | the physical byte range `frame.claim` may take frames from |
| `irq` | a decimal line (`10`), an inclusive range (`32-47`), or `*` | the interrupt lines `irq.claim` may take |

The three range domains are written as ranges, not as paths or names. `BASE` and
`LEN` take hex (`0x`) or decimal, and `LEN` must be at least 1. `irq` takes
decimal only, so a line number reads the same to the author and the checker.

## `net`

```kelp
impl "std/net" caps(net = ["api.example.com:443"])   // one host, one port
impl "std/net" caps(net = ["*.example.com"])         // any subdomain
impl "std/net" caps(net = ["127.0.0.1:*"])           // loopback, any port
impl "std/net" caps(net = ["*"])                     // anything
```

- Matching is on **names, never resolved addresses**. `127.0.0.1:*` does not cover
  `localhost`, even though both are this machine; two spellings of one address can
  fall under different grants.
- The connection pool in [`std/http`](/stdlib/http) is keyed on the host as
  written for exactly this reason.
- A bare `host` matches any port on that host.
- `*` in a host stands for one label only: `*.example.com` matches
  `api.example.com`, not `a.b.example.com`. A bare `*` matches any host.
- A host part made only of digits, dots and `*` (`10.0.0.*`) matches **IPv4
  literals only**, a dotted quad, never a name like `10.0.0.xyz`, whatever DNS
  says about that name. See the [threat model](/reference/capability-threat-model).
- **Listening is checked differently.** `net.listen(port)` is checked on the
  **port alone**. Its host part decides only the interface: a grant that admits
  every interface (a host of `*`, `0.0.0.0`, a glob matching `0.0.0.0`, or no host
  at all) binds every interface, and any other grant (`127.0.0.1:*`) binds
  `127.0.0.1` alone, so a loopback grant cannot become a public server.
  `net.listenOn(host, port)` is checked on `host:port` like `connect`: a grant of
  `127.0.0.1:8080` allows `listen_on("127.0.0.1", 8080)` and refuses
  `listen_on("0.0.0.0", 8080)`. Passing `"*"` or `"0.0.0.0"` binds every
  interface.

## `fs` and `process`

```kelp
impl "std/fs" caps(fs = ["/var/lib/myapp/**"])
impl "std/fs" caps(fs = ["/srv/data/*.csv"])
impl "std/process" caps(process = ["/usr/bin/curl"])
```

- Paths must be **absolute**, and a path containing `..` is refused.
- The path is normalized lexically and resolved through symlinks **before**
  matching, so a symlink inside the grant that points outside it is denied.
- `*` stays within one component; `**` spans components.
- `process` matches the program path; `process.args()` needs no pattern, so
  `caps(process = [])` is enough to read `argv`.

## `env`

```kelp
impl "std/env" caps(env = ["NO_COLOR"])   // one variable
impl "std/env" caps(env = ["APP_*"])      // a prefix
impl "std/env" caps(env = ["*"])          // anything
```

There is no way to enumerate the environment: a grant names what may be read, so
"which variables exist?" is not a question the language lets you ask.

## `time`, `rand` and `machine`

No pattern exists: the domain is the grant:

```kelp
impl "std/time" caps(time = [])
impl "std/rand" caps(rand = [])
impl "std/os" caps(machine = [])
```

`machine` covers the host name, the user name, the home and temporary directories,
and the numeric user and group ids that [`std/os`](/stdlib/os) reads. It is a
domain of its own rather than an `env` name, so a grant of one variable does not
read the host name.

## `ui`

No pattern is enforceable: a call in this domain carries no argument that names
the display server, so the wildcard is the only accepted grant.

```kelp
impl "display" caps(ui = ["*"])
```

An empty list or any named pattern is refused where it is written. This is the
domain gate alone, and it is what a GTK binding asks for (see
[User FFI](/language/externs)).

## Delegation

- The **entry module holds the wildcard** for every domain by default, so a
  single-file program needs no grant for its own calls. `coral.toml`'s
  `[caps]` section can narrow this (see
  [Coral: the manifest](/tooling/coral#the-manifest)) so the entry module
  itself holds less than everything.
- `caps(*)` is that whole set in one clause: `impl "helper" caps(*)` delegates
  `/**` for the path domains and `*` for the name domains, the same set the
  importing module holds. It stands alone (`caps(*, net = [...])` is a parse
  error in either order), it can never grant more than the delegator holds, and
  it is refused on an import that reaches no capability domain at all.
- `coral.toml`'s `[caps."<module id>"]` section (#301) gives an imported module a grant once, whichever file imports it. It is a ceiling: a `caps(...)` clause on that module may grant only what the section covers (see [Coral: the manifest](/tooling/coral#caps-module-id-the-grant-for-one-imported-module)).
- A non-entry module holds exactly what its importer granted, and **can delegate
  less than it holds, never more**: granting a pattern the importer does not hold
  is an error.
- A module can hold a domain without using it: `httpx` writes
  `caps(net = [])` internally only because importing `std/http` requires
  `net` to be delegated somewhere. The smallest grant that compiles is the
  idiomatic way to say "this module does not dial".
- Referencing a gated item without holding the domain is a compile error
  naming the missing domain and the grant to spell. Every item the gated module
  declares is covered, its `extern fun` primitives and its receiver methods
  included, and every place the item is named (a call, a receiver method call, a
  function value, a `pd` initializer).

## Where the patterns are enforced

The matcher is written in Kelp, in the compiler's own runtime module, `std/rt`. A grant is checked statically and
enforced at runtime against the same pattern list, at the call sites that name a
resource (a wrapper, the primitive behind it, a receiver method, a closure body,
a `pd` initializer), and the two implementations are
compared by a differential test corpus. See [Compiler](/compiler).

## See also

- [Capabilities](/language/capabilities): the model
- [Standard library](/stdlib), which module needs which domain
- [Standard library index](/reference/stdlib-index): domains per module at a glance
