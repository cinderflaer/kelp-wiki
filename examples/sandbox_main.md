---
title: "sandbox_main"
description: "Two files that show where authority is declared and what exceeding it looks like. The program prints a file that is inside its grant, then names one that is not, and dies."
isPublished: true
tags: "example"
---
Two files that show where authority is declared and what exceeding it looks like.
The program prints a file that is inside its grant, then names one that is not,
and dies.

| | |
| --- | --- |
| Sources | [`src/sandbox_main.kp`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki-wikijs/raw/branch/main/examples/src/sandbox_main.kp), [`src/sandbox_vault.kp`](https://homelabone.xenoo.dev/gittea/Juniper/kelp-wiki-wikijs/raw/branch/main/examples/src/sandbox_vault.kp) |
| Needs | nothing beyond the standard library |
| Shows | a grant the consumer narrows, delegation inside a module, and a refusal |

## The two files

`sandbox_vault.kp` is a module with one job: read a file from one directory. Its
own `impl` line is where the read's authority comes from.

```kelp
impl "std/fs" with caps(fs = ["/tmp/kelp-sandbox/vault/**"])
impl "std/str"

// Reads a file inside the granted directory. A path outside it is refused by the
// capability check at the call, which panics with the call site, the attempted
// path and the granted patterns.
//
// The path is bound to a `val` first: `.as_str()` on a temporary is refused.
fun read(name: &str).R: String {
    val path = str.concat("/tmp/kelp-sandbox/vault/", name)
    return fs.read_text(path.as_str())
}
```

`sandbox_main.kp` imports it and decides what it holds. Authority flows down: the
entry module holds the wildcard for every domain, and the pattern written on the
import line is the ceiling for everything the imported module can do.

```kelp
impl "std/fs"
impl "sandbox_vault" as vault with caps(fs = ["/tmp/kelp-sandbox/vault/**"])

fun main() {
    print(vault.read("ok.txt"))

    // Inside the grant, straight from the entry module: fine, because the entry
    // module holds everything.
    print(fs.read_text("/tmp/kelp-sandbox/vault/ok.txt"))

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

kelpc build sandbox_main.kp -o sandbox_main && ./sandbox_main
```

Both `.kp` files have to be in the same directory, because `impl "sandbox_vault"`
is a module path relative to it.

## Output

On stderr, and the process exits 1:

```text
/tmp/kelp-sandbox-demo/sandbox_vault.kp:17:12: panic: '/tmp/kelp-sandbox/secret.txt' is outside the fs capability granted to module 'sandbox_vault'
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

- **The importer decides the pattern.** `sandbox_vault` asks for `fs`, and
  `sandbox_main` says how much of it the vault may have. A module that granted
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
  `fs.read_text(str.concat(...).as_str())` does not build: `.as_str()` on a
  temporary is refused.

## See also

- [Capabilities](/language/capabilities) for the model and the grant syntax
- [Capability patterns](/reference/capability-patterns) for what a pattern may look like
