---
title: "Sandbox directory grant"
description: "Shows where authority is declared and what exceeding it looks like: the program prints a file inside its grant, then names one outside it, and stops."
isPublished: true
tags: "example"
---

The `sandbox-directory-grant` program prints a file inside its grant.
Then it names a file outside the grant, and the refusal ends the program.
The `vault` module is the one that holds the narrower grant.

| | |
| --- | --- |
| Sources | [`src/sandbox-directory-grant.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki-wikijs/raw/branch/main/examples/src/sandbox-directory-grant.kp), [`src/vault.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki-wikijs/raw/branch/main/examples/src/vault.kp) |
| Needs | nothing beyond the standard library |
| Shows | a grant the consumer narrows, delegation inside a module, and a refusal |

## The two files

`vault.kp` is a module with one job: read a file from one directory. Its
own `impl` line is where the read's authority comes from.

```kelp
impl "std/fs" caps(fs = ["/tmp/kelp-sandbox/vault/**"])

// Reads a file inside the granted directory. A path outside it is refused by the
// capability check at the call, which panics with the call site, the attempted
// path and the granted patterns.
//
// The path is bound to a `val` first: `.as_str()` on a temporary is refused.
// `pub` exports the name: the entry module is another module, so it reaches this
// one only through the qualifier, and a private `read` would be refused there.
pub fun read(name: str) => String {
    val path = str.concat("/tmp/kelp-sandbox/vault/", name)
    return fs.readText(path.as_str())
}
```

`sandbox-directory-grant.kp` imports it and decides what it holds. Authority flows down: the
entry module holds the wildcard for every domain, and the pattern written on the
import line is the ceiling for everything the imported module can do.

```kelp project
impl "std/fs"
impl "vault" caps(fs = ["/tmp/kelp-sandbox/vault/**"])

fun main() {
    print(vault.read("ok.txt"))

    // Inside the grant, straight from the entry module: fine, because the entry
    // module holds everything.
    print(fs.readText("/tmp/kelp-sandbox/vault/ok.txt"))

    // Outside the grant, through the gated module: refused.
    print(vault.read("../secret.txt"))
}
```

Note the path resolution in `vault.read("../secret.txt")`: the joined path is
`/tmp/kelp-sandbox/vault/../secret.txt`, which normalizes to
`/tmp/kelp-sandbox/secret.txt`, and that is what the refusal names. Lexical
normalization happens before matching, so no spelling of the path gets around it.

## Run it

```sh
mkdir -p /tmp/kelp-sandbox/vault
printf 'inside the grant\n' > /tmp/kelp-sandbox/vault/ok.txt
printf 'outside the grant\n' > /tmp/kelp-sandbox/secret.txt

kelpc build sandbox-directory-grant.kp -o sandbox-directory-grant && ./sandbox-directory-grant
```

Both `.kp` files have to be in the same directory, because `impl "vault"`
is a module path relative to it.

## Output

On stderr, and the process exits 1:

```text
/tmp/kelp-sandbox-demo/vault.kp:19:12: panic: '/tmp/kelp-sandbox/secret.txt' is outside the fs capability granted to module 'vault'
  granted:
    /tmp/kelp-sandbox/vault/**
```

On stdout:

```text
inside the grant

inside the grant

```

The panic text appears before the program's own output because stderr is not
buffered the way stdout is. The three lines of stdout are two successful reads
and the empty line each `print` of a trailing newline leaves.

## What to take from it

- **Authority and reachability are separate clauses.** `sandbox-directory-grant` calls
  `vault.read`, so `read` is declared `pub` (A-13). The `caps(...)`
  grant decides what that call may touch; it does not carry the name into
  another module's reach. Drop the `pub` and the build stops at the call site:
  `'vault.read' is private: 'read' is declared in module 'vault'
  without 'pub', so only that module can name it; add 'pub' to its declaration
  to export it`.
- **The importer decides the pattern.** `vault` asks for `fs`, and
  `sandbox-directory-grant` says how much of it the vault may have. A module that granted
  itself more than its importer holds is a compile error, not a runtime surprise:
  "it does not hold that pattern itself ... a module can delegate less than it has,
  never more".
- **A refusal is a panic, not a catchable error.** There is no `try`, so code that
  must survive an out-of-grant path checks the path first. What the panic gives
  you is the call site, the attempted path and the granted patterns, which is
  usually enough to see the mistake.
- **The paths are normalized and symlinks resolved before matching,** so a grant
  cannot be escaped by `..`, by a double slash, or by a symlink inside the
  directory that points outside it.
- **The entry module is not a sandbox.** The second read succeeds because the
  program's own module holds everything. Authority matters at module boundaries,
  which is where a library lives.
- **The `.as_str()` bind in `vault.read` is not decoration.** Writing
  `fs.readText(str.concat(...).as_str())` does not build: `.as_str()` on a
  temporary is refused.

## See also

- [Capabilities](/language/capabilities) for the model and the grant syntax
- [Capability patterns](/reference/capability-patterns) for what a pattern may look like
