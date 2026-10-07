---
title: "Tutorial 12: Capabilities"
description: "Chapter 12 of the Kelp tutorial: grants on impl lines, what the filesystem and environment grants allow, the compile error for a module nobody granted, and the rule that a module can delegate less than it holds, never more."
isPublished: true
tags: "tutorial, capabilities, security"
---
This is the feature Kelp is built around. **A program cannot read a file, open a
socket, spawn a process or read the clock unless the module making the call was
granted that resource, and the grant is written in the source.** The reference pages
are [Capabilities](/language/capabilities) and
[Capability patterns](/reference/capability-patterns); the threat model is
[here](/reference/capability-threat-model).

## The default, and why it is not enough

In every program so far the one file was the **entry module**, and the entry module
holds the wildcard for every domain, so `impl "std/fs"` alone was enough to touch
files. The interesting case is a *second* module: it holds **exactly what its importer
granted it, and nothing else**. The domains are `fs`, `net`, `process`, `env`, `time`
and `rand`, plus `ui`, `mmio`, `irq` and `frames` for display and bare metal.

## A logger that may only write under one directory

`capdemo` is a project (chapter 11) with `coral.toml` like the last chapter's (name,
version, entry) and two modules. The logger:

```kelp
impl "std/fs"

pub fun log_to(path: &str, line: &str) {
    fs.write_text(path, String.from_str(line))
}
```

The entry module imports it with a grant:

```kelp
impl "logger" caps(fs = ["/tmp/kelp-tut/**"])

fun main() {
    logger.log_to("/tmp/kelp-tut/log.txt", "hello from the logger")
    print("wrote inside the grant")
    logger.log_to("/tmp/kelp-tut/../outside.txt", "escape?")
    print("not reached")
}
```

Running it (the directory `/tmp/kelp-tut` existed; the panic line's file path is shortened here to be
relative to the directory the programs were built in):

```text
$ ./capdemo; echo "exit $?"
capdemo/src/logger.kp:4:5: panic: '/tmp/outside.txt' is outside the fs capability granted to module 'logger'
  granted:
    /tmp/kelp-tut/**
wrote inside the grant
exit 1
```

Both backends printed this. The first write, inside `/tmp/kelp-tut/**`, worked. The
second used `..` to climb out; the path is normalised first (the message shows
`/tmp/outside.txt`), compared with the grant, and refused with a panic that names the
module and what it was granted. Patterns are matched on the **normalised, symlink-resolved
path**, so a link inside the directory that points outside is refused too.

## No grant at all is a compile error

Drop the `caps(...)` clause from `main.kp`:

```text
$ kelpc check cap_nogrant
error: 'std.fs.write_text' needs the 'fs' capability, which module 'logger' was not granted; the module that imports this one must delegate it (`impl "<this module>" caps(fs = ["<pattern>"])`)
  --> cap_nogrant/src/logger.kp:4:5
```

This one is caught **before** the program runs, and the message names the call, the
missing domain, and the exact line the importer would write. Holding the domain is the
whole check for an item that names no resource (like `fs.cwd`); an item that names one
is additionally checked against the patterns at the call, as above.

## Grants for the other domains

The patterns differ by domain (the table is on the
[language page](/language/capabilities#patterns)): `net` takes `host`, `host:port`,
`*.host`, `*:port` or `*`, matched against the host **string the program wrote**;
`fs` and `process` take absolute paths with `*` and `**`; `env` takes names with `*`;
`time` and `rand` take no pattern. An empty list denies everything.

The environment works the same way. `settings.kp` reads a variable, and `main.kp`
grants `env = ["KELP_TUT_*"]`:

```kelp
impl "std/env"

pub fun read(name: &str).return: String {
    if env.has(name) {
        return env.get(name)
    }
    return String.from_str("(unset)")
}
```

```kelp
impl "settings" caps(env = ["KELP_TUT_*"])

fun main() {
    val who = settings.read("KELP_TUT_NAME")
    print("name: ${who}")
    val home = settings.read("HOME")
    print("home: ${home}")
}
```

Run with `KELP_TUT_NAME=ada` set:

```text
$ KELP_TUT_NAME=ada ./cap_env; echo "exit $?"
cap_env/src/settings.kp:4:8: panic: 'HOME' is outside the env capability granted to module 'settings'
  granted:
    KELP_TUT_*
name: ada
exit 1
```

Even asking whether `HOME` is set is gated: `env.has` panicked before `env.get` could
run. With `caps(env = [])` nothing is allowed, not even `KELP_TUT_NAME`:

```text
cap_empty/src/settings.kp:4:8: panic: 'KELP_TUT_NAME' is outside the env capability granted to module 'settings'
  granted: (nothing)
exit 1
```

## Delegation can only narrow

A module may pass on less than it holds, never more. Here `mid` holds
`/tmp/kelp-tut/**` and tries to hand `inner` all of `/tmp/**`:

```kelp
impl "inner" caps(fs = ["/tmp/**"])

pub fun go() {
    inner.run()
}
```

```text
$ kelpc check cap_more
error: module 'mid' cannot grant 'fs' access to '/tmp/**': it does not hold that pattern itself (held: /tmp/kelp-tut/**); a module can delegate less than it has, never more
  --> cap_more/src/mid.kp:1:19
```

This is why "what can this code do?" is answered from the top of a file: authority can
only flow downward through `impl` lines, and only shrink. `caps(*)` is the whole
grant in one clause, but it hands over the delegator's own set, so it is not a way to
acquire authority either. There is no other way to acquire it: no ambient `open`, no
environment lookup that bypasses the gate, and a gated item cannot even be named as a
function value (`val f = fs.read` is refused).

## Exercises

1. Make `cap_more` compile by narrowing `mid`'s grant to what it holds, and run it.
   What does `fs.exists("/tmp/kelp-tut")` give?
2. What do you expect a grant of `env = []` to do to `KELP_TUT_NAME`? Check against the
   output above.

<details>
<summary>Solutions</summary>

1. Change `/tmp/**` to `/tmp/kelp-tut/**` in `mid.kp`. It builds and the program
   printed, on both backends:

```text
true
```

2. It is refused like any other name: an empty list is a grant that permits nothing,
   and the panic text above says `granted: (nothing)`.

</details>

Next: [Concurrency](/tutorial/13-concurrency).
