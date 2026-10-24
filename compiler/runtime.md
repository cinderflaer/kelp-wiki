---
title: "Runtime"
description: "The standard library sources compiled into kelpc, the extern fun bodies, the kelp-rt runtime crate and the capability matcher. Covers what each runtime file does and how it is linked."
isPublished: true
tags: "compiler"
---
A Kelp program depends on three kinds of code at run time: the standard library, the `extern fun` bodies and the runtime.
Most of this code is written as text that the compiler writes into each program or compiles beside it.
This page covers where each piece comes from and how it is linked.

## The standard library in the binary

The standard library is Kelp source under `kelpc/std/`.
Each file is embedded in `kelpc` with `include_str!`, so the binary does not depend on files beside it.

- A program may import the 35 modules listed by `stdlib::shipped()`.
  They are `std/option`, `std/str`, `std/fs`, `std/net` and the rest of the library.
  See [Standard library](/stdlib) for what each one provides.
- `std/rt` is also embedded, but no program imports it on purpose.
  The resolver loads it when a program imports a gated module or `std/path`.
- `std/http` contains a placeholder, `__KELP_HTTP_POOL__`, which the compiler replaces with the connection pool size from the project.

The library is compiled by the same lexer, parser and checker as user code.
The resolver reads `std/...` ids from the embedded text before it looks at the project directory.

## `extern fun` bodies

An `extern fun` declaration has no body in Kelp.
The checker accepts the declaration only when the compiler has a body for it.

1. A stdlib body is a Rust export in `kelp-rt`, listed in `RUST_PORTED` (`externs.rs`).
   The LLVM call resolves against the runtime archive under the mangled qualified name.
2. The checker asks `externs::has_body` (`infer.rs`).
   A project may declare its own extern only with a `[extern."<module>"]` section in `coral.toml`, and the checker checks that allowlist.
3. A user extern that names a native symbol gets a trampoline in the program's externs object (`lower_externs_object`, `extern_object.rs`).
   The trampoline calls the native symbol directly. A `move closure fun(...)` parameter is boxed and handed over with a thunk and a destructor.
   A user extern that takes or returns by value a struct, `Bytes`, `String`, `View`, `List`, `Box`, `Map`, an array or a closure is refused by name. The message says the llvm backend cannot pass it to a native symbol yet, and asks for a pointer or a handle instead.

The trampolines are lowered to LLVM IR for each program, not shipped as one fixed object, because each names the native symbols that program allowlisted.

## The runtime files

The runtime is the `kelp-rt` crate, a `no_std` Rust crate (`kelp-rt/src/lib.rs`).
No C runtime and no C source is in the tree.

| File or folder | What it is |
| --- | --- |
| `kelp-rt/src/*.rs` | The runtime: text and buffers, threads, mutexes and condition variables, panics, the environment cache, the child process table, the capability checks, and the exported functions. |
| `kelpc/gc/` | The collector crate `kelp_gc`. Every hosted build links it. |
| `kelpc/runtime/` | `dns_parse.kp` and `resolver_conf.kp`. The compiler does not embed these two `.kp` files. |

`kelp-rt` is built twice from one source folder: as `libkelp_rt.a`, and as `kelp_rt_managed.o` with the `managed` feature.
`kelpc/build.rs` builds both, and `driver.rs` embeds them with `include_bytes!`.
A hosted build links `kelp_rt_managed.o` with the collector archive. See [Driver](/compiler/driver#linking).

The exported functions are listed in the `PROTOTYPES` table of `kelp-rt/src/abi.rs`.
The LLVM backend declares the runtime functions it calls as LLVM declarations, and the tests in `kelpc/tests/runtime_prototypes.rs` and `kelpc/tests/runtime_exports.rs` check the table against the archive's exports.

## The capability runtime

The matching logic of the capability check is Kelp code in `std/rt.kp`.
`glob_match`, `host_glob`, `host_match` and `path_normalize` are the functions the checks call.
`kelp-rt/src/cap.rs` declares them as weak imports.

The runtime owns the other capability pieces:

- the checks `kelp_cap_check_host`, `kelp_cap_check_hostport`, `kelp_cap_check_name`, `kelp_cap_check_path` and `kelp_cap_check_port`;
- the deny path, `kelp_cap_deny`;
- the per-thread loopback flag for listening sockets.

The compiler emits a check call before each gated call.
See [Resolve](/compiler/resolve) for how the checks are placed.

## Standard library runtime text

`std/rt` is the only Kelp module that holds the capability matcher, and no program imports it on purpose.
The resolver loads it when a program imports a gated module or `std/path`.

## See also

- [Modules and capabilities](/compiler/resolve)
- [Backends](/compiler/backends)
- [Driver](/compiler/driver#linking)
- [Standard library](/stdlib)
- [Capabilities](/language/capabilities)
