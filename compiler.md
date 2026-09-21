---
title: "Compiler"
description: "kelpc is a Rust program that takes .kp sources through lexing, preprocessing, parsing, type checking, move/borrow checking and code generation, then hands the result to a backend. The compiler is..."
isPublished: true
tags: "compiler"
---
`kelpc` is a Rust program that takes `.kp` sources through lexing, preprocessing,
parsing, type checking, move/borrow checking and code generation, then hands the
result to a backend. The compiler is a single pipeline in a single crate, and the
standard library ships **inside the binary** as Kelp sources rather than as files
next to it.

```sh
cargo build --release -p kelpc
./target/release/kelpc run examples/hello.kp
```

## Stages

| Stage | File | Job |
| --- | --- | --- |
| CLI | `main.rs` | `build`, `run`, `check`, `fmt`, `lint`, `version`; picks the backend |
| Lexing | `lexer.rs` | source to span-carrying tokens; newline-sensitive; UTF-8 in literals |
| Preprocessing | `preprocess.rs` | `%*alias*%` text substitution, before the parser |
| Parsing | `parser.rs` | recursive descent plus a Pratt expression parser; `if let` and `for` are desugared here |
| Module loading | `resolve.rs` | `impl` imports, module ids, aliases, capability gating |
| Type checking | `infer.rs` | types, generics, stdlib overload resolution; fills in implicit borrows |
| Typed IR | `tir.rs` | every node carries its resolved type and span |
| Move/borrow checking | `borrowck.rs` | moves, borrows, and the drop plan the code generators read |
| Code generation | `codegen_c.rs`, `codegen_llvm.rs` | typed IR to C source text, or to LLVM IR covering the whole language (MK7; one guard remains for an owned temporary at a place the lowering did not stage) |
| Backend selection | `backend.rs` | `--backend=` / `KELPC_BACKEND` |
| Finishing | `driver.rs` | writes the artifact and invokes the C compiler |
| Diagnostics | `diag.rs` | a span is one file's byte range; this maps a module id back to `file:line:col` |
| Stdlib sources | `stdlib.rs` | the `std/*.kp` text, embedded with `include_str!`, and the capability domains |
| C bodies for `extern fun` | `externs.rs` | the operations that cannot be written in Kelp at all: written into every generated C program, and compiled per program from `<out>.externs.c` into the object the `llvm` path links |
| C runtime text | `kelpc/runtime/kelp_rt.c` | `kelpc`'s own C runtime: the `Bytes`/`String` routines, the panic path and the allocation helpers. `codegen_c.rs` emits it into every generated program, and `build.rs` compiles it into the object the `llvm` path links |
| Formatting | `fmt.rs` | `kelpc fmt`, token-level |

The design authority for this chapter is
[`plan/architecture.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/architecture.md),
with the backend's plan of record in
[`plan/mk7-llvm-backend.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-llvm-backend.md),
and the retired hand-written track in
[`plan/asm-backend/`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/asm-backend/).

## Pages

- [Pipeline](/compiler/architecture): each stage, and what it is responsible for
- [Backends](/compiler/backends): `c` and `llvm`, and why `c` stays the oracle
- [Runtime](/compiler/runtime): the C that is still C, and the capability matcher
- [Tests](/compiler/tests): the fixture suite, the differential sweeps, the memory gate

## See also

- [Install and build](/getting-started/install): building `kelpc` and running a file
- [Language](/language): the surface syntax these stages implement
- [Capabilities](/language/capabilities): the model the checker enforces
- [Changelog](/changelog): what each release changed in the language and in these stages
