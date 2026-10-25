---
title: "When it does not work"
description: "Which program spoke, how to read a span, and the failures a first week produces - each with the message you actually see and the fix. Most of them are one line of code, and the rest are not your bug."
isPublished: true
tags: "getting-started, errors"
---
Four things can stop you, and the prefix tells you which one spoke.

| What you see | Who said it | What it means |
| --- | --- | --- |
| `coral: ...` | Coral, the project tool | progress, `up to date`, or a manifest problem |
| `error: ...` with a `--> file:line:col` below | `kelpc`, the compiler | a problem in your source, at that span |
| `panic: ...` | your program, at run time | it ran and aborted |

Errors go to stderr and the process exits non-zero, so a shell script and a
CI job both see the failure without extra work.

## Read the span first

```text
$ kelpc run hello.kp
error: call to undefined function 'println'
  --> /tmp/hello.kp:2:5
```

Line 2, column 5 is where the compiler gave up. Go there before reading the
message twice. `println` is not a Kelp function, and the name it wants is `print`.

## A worked example

This one costs everyone a minute, so here it is in full. Writing a signature that
mentions `option.Option` without importing `std/option`:

```kelp
fun count_from(text: str) => option.Option<i64> {
    return option.Option.None
}
```

```text
$ kelpc build head.kp
error: unknown module alias 'option' in type 'option.Option'
  --> /tmp/head.kp:3:31
```

The message ends by asking whether the module was imported, and it is right: every
standard-library type named by path needs its `impl` line, even when another
module already returns it.

```kelp
```

## The first week's failures

| Message | What happened | Fix |
| --- | --- | --- |
| `unknown module alias 'x' in type 'x.T'` | the module was never imported | add `impl "std/x"` for a standard module, or the local path for a file |
| `cannot find module 'shapes/circle': expected '/proj/src/shapes/circle.kp'` | the `impl` path does not resolve | in a project, paths are relative to `src/`, never to the importing file |
| `use of moved value 'a'` | an owned value was consumed and then used | a plain parameter borrows; check whether the call needed `move` at all |
| `cannot assign value of type 'String' to 'y' declared as 'str'` | an owned string bound to a `str` | add `.as_str()` |
| `List.empty()` or `Map.new()` has no element type | nothing said what is inside | write it on the binding (`var xs: List<i32> = List.empty()`), or let the first `push`/`insert` decide it |
| `unexpected argument 'extra'` | `kelpc run` was given arguments | it takes none: `kelpc build` then run the binary, or `coral run -- <args>` |
| `--backend is gone: kelpc builds every program with the llvm backend` | a `--backend=` flag or a set `KELPC_BACKEND` | there is no choice: `llvm` is the one backend ([Backends](/compiler/backends)) |
| `could not write generated IR to '/path/app.ll': No such file or directory` | `-o` named a directory that does not exist | create it first, or build without `-o` and take the artifact from `build/` |
| `panic: fs.read: cannot open file` / `errno 2` | the call ran and the file was not there | `fs` fails by panicking; check `fs.exists(path)` first, or use `fs.open` |
| `panic: '<path>' is outside the fs capability granted to module '<m>'` | the pattern on the `impl` line does not cover the path | widen the grant, or note that the **entry module holds the wildcard** and only an imported module is restricted |
| `error: entry file '.../tests/main.kp' is not inside '.../src'` | a task entry outside `src/` | task files live in `src/tasks/`; the top-level `tests/` directory Coral makes cannot be one |
| `error: unknown key 'bogus' in coral.toml` | a flat key that is not `name`, `version` or `entry` | remove it: the same key under a `[section]` is ignored instead, which is why a typo there is silent |

Two notes on that table:

- **A pattern on the entry module's own `impl` line does nothing.** The entry
  module holds the wildcard for every domain, so `impl "std/fs" caps(fs =
  ["/tmp/ok/**"])` in a single-file program still reads `/etc/hostname`. To see a
  restriction, put the gated call in a module one level down.
- **A mistyped key placed after a `[section]` is silently ignored**, because it
  parses as a key of that section and sections are not closed. `bogus = "x"` at
  the top level is refused by name; the same line under `[tasks]` is not.

The language rules behind these are on [Pitfalls](/language/pitfalls), which is
worth reading once on purpose rather than once per error.

## When it is not your code

A backend refusing a construct by name, rather than miscompiling it, is
documented behaviour rather than a bug in your program. The `llvm` backend lowers
the whole language today, so it refuses no corpus construct; one guard remains in
the lowering for an owned temporary at a place it did not stage, and its message
says the shortfall is the compiler's rather than sending you to a backend you
cannot choose. There is no `--backend=` flag: `kelpc build --backend=c` is refused
with a message that says the choice is gone.

## Make a refusal happen on purpose

The capability model is easier to trust after watching it refuse something. Two
files, one grant, one call outside it:

```kelp
// src/vault.kp
impl "std/fs" caps(fs = ["/tmp/kelp-sandbox/vault/**"])

fun read(name: str) => String {
    val path = str.concat("/tmp/kelp-sandbox/vault/", name)
    return fs.read_text(path.as_str())
}
```

A caller that hands `vault.read` the name `"../secret.txt"` gets

```text
panic: '/tmp/kelp-sandbox/secret.txt' is outside the fs capability granted to module 'vault'
  granted:
    /tmp/kelp-sandbox/vault/**
```

Note what the message contains: the **normalized** path, so `..` does not get
around the grant, and the patterns that were granted, so you can see which one
missed. [sandbox_main](/examples/sandbox-directory-grant) is this program with the caller
attached.

## Where to report a bug

- The program must be valid per [`design/syntax`](/design/syntax),
  which is the language authority. A construct that is refused by design belongs
  on [Limits in v1](/language/limits), not in a report.
- Include `kelpc version`, the optimization level, the source, the command, and
  the output verbatim.
- [Contributing](/meta/contributing) has the workflow.

## See also

- [Pitfalls](/language/pitfalls): every rule that produces a compile error
- [Capabilities](/language/capabilities) and [Capability patterns](/reference/capability-patterns)
- [Coral](/tooling/coral): what each manifest key means
- [Install and build](/getting-started/install): backends and environment variables
