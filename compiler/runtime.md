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
Each file is embedded in `kelpc` with `include_str!` (`stdlib.rs:142` to `196`), so the binary does not depend on files beside it.

- A program may import the 35 modules listed by `stdlib::shipped()` (`stdlib.rs:198`).
  They are `std/option`, `std/str`, `std/fs`, `std/net` and the rest of the library.
  See [Standard library](/stdlib) for what each one provides.
- `std/rt` is also embedded, but no program imports it on purpose.
  The resolver loads it when a program imports a gated module or `std/path` (`resolve.rs:1766` to `1767`).
- `std/http` contains a placeholder, `__KELP_HTTP_POOL__`, which the compiler replaces with the connection pool size from the project (`stdlib.rs:126` to `140`).

The library is compiled by the same lexer, parser and checker as user code.
The resolver reads `std/...` ids from the embedded text before it looks at the project directory (`resolve.rs:1609` to `1620`).

## `extern fun` bodies

An `extern fun` declaration has no body in Kelp.
The checker accepts the declaration only when the compiler has a body for it.

1. A stdlib body is a Rust export in `kelp-rt`, listed in `RUST_PORTED` (`externs.rs`).
   The LLVM call resolves against the runtime archive under the mangled qualified name.
2. The checker asks `externs::has_body` (`infer.rs`).
   A project may declare its own extern only with a `[extern."<module>"]` section in `coral.toml`, and the checker checks that allowlist.
3. A user extern that names a native symbol gets a trampoline in the program's externs object (`lower_externs_object`, `extern_object.rs`).
   The trampoline calls the native symbol directly. A `move closure(...)` parameter is boxed and handed over with a thunk and a destructor.
   A user extern that takes or returns a struct by value is refused for now.

The trampolines are compiled for each program, not shipped as one fixed object, because each names the native symbols that program allowlisted.

## The runtime files

The runtime is the `kelp-rt` crate, a Rust crate with `no_std` (`kelp-rt/src/lib.rs`).
It replaced the C runtime `kelp_rt.c`, which is not in the tree.

| File or folder | What it is |
| --- | --- |
| `kelp-rt/src/*.rs` | The runtime: text and buffers, threads, mutexes and condition variables, panics, the environment cache, the child process table, the capability checks, and the exported functions. |
| `kelpc/gc/` | The collector crate `kelp_gc`. Only managed builds use it. |
| `kelpc/runtime/` | `abi_aggregate.c`, `dns_parse.kp` and `resolver_conf.kp`. The compiler does not embed the two `.kp` files. |

`kelp-rt` is built twice from one source folder.
The hosted build gives `libkelp_rt.a`, and the managed build gives `kelp_rt_managed.o`.
`kelpc/build.rs` builds both, and `driver.rs` embeds them with `include_bytes!`.
The hosted link uses the archive. The managed link uses the object.

The exported functions are listed in the `PROTOTYPES` table of `kelp-rt/src/abi.rs`, which has 99 rows.
The compiler does not read that table. It writes its own C prelude, with 22 declarations for the helpers it calls.
Nothing checks that the two agree, and the compiler does not check the ABI version.

The LLVM backend also emits small `Bytes`, `String` and `View` bodies into each module with internal linkage.
Those copies can be inlined.
The runtime object still defines every one of them, and the two definitions never meet at link time.

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
