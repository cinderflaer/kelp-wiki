---
title: "Capability patterns"
description: "Source section - syntax.md \u00a715.2."
isPublished: true
tags: "reference, capability"
---
Source section:
[`syntax.md` §15.2](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

A grant is written on the `impl` line that acquires it:

```kelp
impl "std/fs"
impl "std/http" caps(net = ["api.example.com:443", "127.0.0.1:*"])
impl "logger" caps(fs = ["/var/log/myapp/**"], env = ["LOG_*"])
```

`domain = [pattern, ...]`, one or more domains, in any order. **An empty list
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
| `rand` | no pattern | — |

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

## `time` and `rand`

No pattern exists: the domain is the grant:

```kelp
impl "std/time" caps(time = [])
impl "std/rand" caps(rand = [])
```

## Delegation

- The **entry module holds the wildcard** for every domain, so a single-file
  program needs no grant for its own calls.
- A non-entry module holds exactly what its importer granted, and **can delegate
  less than it holds, never more**: granting a pattern the importer does not hold
  is an error.
- A module can hold a domain without using it: `httpx` writes
  `caps(net = [])` internally only because importing `std/http` requires
  `net` to be delegated somewhere. The smallest grant that compiles is the
  idiomatic way to say "this module does not dial".
- Referencing a gated function without holding the domain is a compile error
  naming the missing domain and the grant to spell.

## Where the patterns are enforced

The matcher exists twice on purpose: in Kelp (`std/rt`, compiler-internal, not
importable) and in C in `kelpc/runtime/`. A grant is checked statically and
enforced at runtime against the same pattern list, and the two implementations are
compared by a differential test corpus. See [Compiler](/compiler).

## See also

- [Capabilities](/language/capabilities): the model
- [Standard library](/stdlib), which module needs which domain
- [Standard library index](/reference/stdlib-index): domains per module at a glance
