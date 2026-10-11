---
title: "Runtime"
description: "The standard library sources compiled into kelpc, the extern fun bodies, the C runtime files and the capability matcher. Notes that kelp-rt is embedded but not linked."
isPublished: true
tags: "compiler"
---
A Kelp program depends on three kinds of code at run time: the standard library, the `extern fun` bodies and the C runtime.
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
The compiler supplies the body as C text, and the checker accepts the declaration only when the compiler has a body for it.

1. The bodies are kept in one table, `EXTERNS` (`externs.rs:19`).
   Each entry is a module, a name and C statements.
   `externs::body` (`externs.rs:748`) finds an entry by its module and name.
2. The checker asks `externs::has_body` (`infer.rs:9699` and `11113`).
   A project may declare its own extern only with a `[extern."<module>"]` section in `coral.toml`, and the checker checks that allowlist (`infer.rs:11113` to `11125`).
3. The C text for each body is written by `write_extern` (`cdecl.rs:245`).
   A user extern that names a native symbol becomes a call to that symbol (`cdecl.rs:293`).

The bodies are compiled for each program, not shipped as one fixed object.
One body calls a `std/path` function that only the resolver injects, and another names a container type that exists only in the program.
The C backend writes the bodies into its output.
The LLVM backend writes them into `<out>.externs.c` and compiles that file into `<out>.externs.o` (`codegen_llvm.rs:477` to `487`).

## The C runtime files

`kelpc/runtime/` holds the C that the compiler uses at run time, and the reference files used by tests.

| File | Used by | What it is |
| --- | --- | --- |
| `kelp_rt.c` | Written into every C program. Compiled by `build.rs` into `kelp_rt.o` and linked into every LLVM program. | The `Bytes` and `String` routines, `kelp_panic` and `kelp_assert`, the allocation helpers, `kelp_argc` and `kelp_argv`, the thread and lock records. |
| `cap_glue.c` | Written into a program that has a gated call. | The capability deny path and the buffer code around the matcher. See [The capability runtime](#the-capability-runtime). |
| `cap_matcher_ref.c` | Not written into programs. | The C capability matcher, kept as the oracle for `std/rt.kp`. |
| `path_normalize_ref.c` | Not written into programs. | The C path normalizer, kept as the oracle for `std/rt.kp`. |
| `dns_parse.kp`, `dns_parse_ref.c` | Not a standard library module. | A DNS message parser in Kelp, and its C reference. |
| `resolver_conf.kp`, `resolver_conf_ref.c` | Not a standard library module. | A resolver configuration parser in Kelp, and its C reference. |
| `abi_aggregate.c` | Not traced. | C helper in the runtime folder. This page did not confirm where it is used. |

`kelp_rt.c` is 1620 lines.
`driver.rs:12` embeds the object compiled from it, and `codegen_c.rs:39` includes the source text in the C backend.

The LLVM backend also emits small `Bytes`, `String` and `View` bodies into each module with internal linkage.
Those copies can be inlined.
The runtime object still defines every one of them, and the two definitions never meet at link time.

## The capability runtime

The matching logic of the capability check is Kelp code in `std/rt.kp`.
`glob_match`, `host_glob`, `host_match` and `path_normalize` are the functions the checks call.

C remains for three things:

- buffers, `host:port` formatting and the cut of a pattern's host part (`cap_glue.c`);
- the deny path, which prints the message to stderr and exits with status 1 (`kelp_cap_deny`, `cap_glue.c:148`);
- the allowlist loop, which accepts a call when a pattern admits the resource.

`kelp_resolve_path` is also C.
It resolves symbolic links before matching, which keeps a link inside a grant from reaching outside it.

The C backend writes `cap_glue.c` into a program that has a gated call (`codegen_c.rs:175`).
The LLVM backend compiles it into the program's C object when `program.gated` is not empty (`program_c_source`, `codegen_llvm.rs:15202`).

The C matcher and normalizer are kept because a port of a security check needs an independent check.
The tests `cap_matcher.rs` and `path_normalize.rs` compare the verdicts of the two versions on generated cases.

## The Rust port (`kelp-rt`)

`kelp-rt/` is a Rust port of part of the runtime, in progress.
It exports the same six `kelp_cap_*` functions as `cap_glue.c`, in `src/cap.rs`.
`build.rs` builds it into `libkelp_rt.a` (`kelpc/build.rs:139` to `245`).

`driver.rs:16` embeds that archive, with `#[allow(dead_code)]`.
No code path reads it, and the linker uses the C runtime object.
The comment on the constant says the link will switch to the archive in a later stage.

Open question: the code does not say whether the Rust port will replace the C runtime or sit beside it.

## See also

- [Modules and capabilities](/compiler/resolve)
- [Backends](/compiler/backends)
- [Driver](/compiler/driver#linking)
- [Standard library](/stdlib)
- [Capabilities](/language/capabilities)
