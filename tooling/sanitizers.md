---
title: "Sanitizer builds"
description: "Sanitizer builds are removed. kelpc refuses --sanitize and the [build] sanitize key, because the LLVM backend links no sanitizer passes."
isPublished: true
tags: "tooling, cli, unsafe"
---
Sanitizer builds are removed from `kelpc`.
The `--sanitize` flag and the `[build] sanitize` key in `coral.toml` are refused by name.
The LLVM backend, which builds every program, links no sanitizer passes.

The plan for sanitizer builds is marked removed.
Safe Kelp cannot read or write out of bounds, but `unsafe`, `Ptr<T>` and `extern` calls can.
For memory errors in a binary, the compiler's own valgrind gate is the check that remains.
It runs as the ignored `memory_gate` test in `kelpc/tests/memory_gate.rs`.

```bash
cargo test --test memory_gate -- --ignored
```

## See also

- [`kelpc` CLI](/tooling/kelpc-cli)
- [Front-end fuzzing and parser limits](/tooling/fuzzing)
