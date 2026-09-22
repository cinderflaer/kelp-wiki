---
title: "Runtime"
description: "Most of what a program needs at run time is emitted by the code generator rather than linked - the Bytes/String heap routines, bounds checks, drop calls and the capability plumbing are C text held once in kelpc/runtime/kelp_rt.c, which codegen_c.rs emits into the generated program and the llvm backend links as a compiled object."
isPublished: true
tags: "compiler"
---
Most of what a program needs at run time is emitted by the code generator rather
than linked: the `Bytes`/`String` heap routines, bounds checks, drop calls and the
capability plumbing are C text that `codegen_c.rs` splices into the generated
program. Since MK7 stage S2B that text has **one home**:
`kelpc/runtime/kelp_rt.c` holds the bytes/string routines,
`kelp_panic`/`kelp_assert`, the allocation helpers and `kelp_argc`/`kelp_argv`.
The C backend still emits that file into its output, byte for byte, exactly as it
did when the text was a string literal in `codegen_c.rs`; the `llvm` path links
it as an object `kelpc/build.rs` compiles from the same file. One source, so the
panic text and the `Bytes`/`String` invariants cannot drift between the two
backends. `kelpc/runtime/` holds the runtime pieces that are not spliced in as
text: the C that stayed, the C references kept as oracles, and the newest pair,
a parser written in Kelp with its C reference beside it.

Since MK7 stage S3A the compiler-supplied `extern fun` bodies are compiled the
same way: `externs.rs` holds that C text, `codegen_c.rs` writes it into every
generated program, and the `llvm` path writes the same text to `<out>.externs.c`
and links the object it compiles, beside the runtime object and before `-lm`. It
is built per program rather than shipped fixed, because one body calls a
`std/path` function only the resolver injects and another names a per-program
container typedef.

| File | Status | Role |
| --- | --- | --- |
| `cap_glue.c` | emitted into every program that contains a gated call | the non-matching half of the capability check |
| `kelp_rt.c` | emitted into every generated program by `codegen_c.rs`; linked as an object into every `llvm`-built binary | the C runtime text: the `Bytes`/`String` routines, `kelp_panic`/`kelp_assert`, the allocation helpers and `kelp_argc`/`kelp_argv` |
| `cap_matcher_ref.c` | not emitted | the C capability matcher, kept as the differential oracle |
| `path_normalize_ref.c` | not emitted | the C path normalizer, kept as the differential oracle |
| `dns_parse.kp` | not emitted, not a std module | the stub resolver's DNS message parser, in Kelp |
| `dns_parse_ref.c` | not emitted | the same parser in C, kept as the differential oracle |

## `cap_glue.c`: what the capability runtime still is in C

Spliced together with prototypes for the `std/rt` functions it calls (see
`codegen_c.rs`), and deliberately free of any matching logic. Three things stayed:

| Piece | Why it is still C |
| --- | --- |
| Buffered plumbing: `host:port` formatting, `PATH_MAX` scratch buffers, cutting a pattern's host part | it is the same code the C reference used, so moving it cannot change a verdict; a buffer is declared one byte longer than `PATH_MAX` where a Kelp function writes into it, because `Bytes` keeps its NUL in the slot *at* `len` |
| The deny path: `fprintf` to stderr plus `exit(1)` | it is I/O, and belongs with the rest of the runtime's I/O |
| The allowlist loop: "any pattern that admits the resource admits the call" | three lines per check kind with no matching in it |

`kelp_resolve_path` is also still C: it resolves symlinks before matching, which
is the step that makes a symlink inside a grant pointing outside it a denial. It
needs `realpath` and a buffer, so it moves to Kelp with the filesystem half of the
runtime.

## Why the matcher exists twice

The retired hand-written track planned to move the runtime from C text into Kelp
one piece at a time. It is happening anyway, for its own reasons. The
matcher and the normalizer have now moved, and **the C versions were kept rather
than deleted**, because a port of a security check has no other oracle:

- the fixtures prove the grants still *work*;
- only a differential corpus proves the *verdicts* are identical, including for the
  shapes nobody wrote a fixture for.

That is the specific failure the plan's risk register names: *a lenient port widens
every grant*. So:

| Corpus | Compares | Test |
| --- | --- | --- |
| capability matching | `cap_matcher_ref.c` against `std/rt.kp`'s matcher, one verdict per case, both drivers generated from the same case list | `kelpc/tests/cap_matcher.rs` |
| path normalization | `path_normalize_ref.c` against `std/rt.kp`'s `path_normalize`, compared as the bytes left in the buffer *and* the verdict | `kelpc/tests/path_normalize.rs` |

Two details the C reference had to be reproduced exactly, because a port that
rounded them differently would change a boundary:

- the host part of `host:port` is cut at `PATH_MAX` in C, so the Kelp version
  bounds the match at the same index instead of copying, and the corpus covers
  lengths either side of that number;
- the *cut* of a pattern's host part lives in the glue, which is still C, so the
  port could not drift there.

Comparing bytes and not only verdicts is deliberate for the normalizer: a path
that normalizes to something *inside* the grant while resolving outside it is
exactly the escape being rejected.

The same discipline covers the stub resolver's message parser, which is not a
security check: `dns_parse.kp` and
`dns_parse_ref.c` are fed the same 1990-case corpus by `kelpc/tests/dns_parse.rs`,
one printed verdict per case, and the two have to agree line for line. A parser
that agrees only on a well-formed reply is the one that comes apart on a
compressed name, a truncated message or a count the message cannot hold, which is
what the corpus is made of. Neither file is emitted and neither is a std module,
so no program reaches the parser yet.

## What is still C in the runtime, and what that costs

| Item | State |
| --- | --- |
| Capability matcher | Kelp (`std/rt.kp`), with the C oracle kept |
| Path normalizer | Kelp (`std/rt.kp`), with the C oracle kept |
| DNS message parser | Kelp (`dns_parse.kp`), not shipped yet, with the C oracle kept |
| Symlink resolution (`kelp_resolve_path`) | still C |
| The allocator | still C; blocked on raw pointers, which the language does not expose |
| The `Bytes`/`String` heap routines and drop calls | the text of `kelp_rt.c`: emitted by `codegen_c.rs` into every generated program, and linked as an object by the `llvm` path |
| The compiler-supplied `extern fun` bodies | the C text of `externs.rs`: emitted by `codegen_c.rs` into every generated program, and linked as a per-program object by the `llvm` path |

`std/rt` is the compiler's own runtime module. Its source ships inside the
binary like a stdlib module's, and `impl "std/rt"` resolves, but it is not part
of the stdlib surface: `stdlib.rs::shipped()` does not list it, and the resolver
injects it for a program that imports a gated module or `std/path`. The one
program that imports it on purpose is the differential corpus itself
(`kelpc/tests/cap_matcher.rs`, `kelpc/tests/path_normalize.rs`), which calls the
matcher and the normalizer directly to compare them with their C references.

## See also

- [Backends](/compiler/backends)
- [Tests](/compiler/tests)
- [Capabilities](/language/capabilities)
- [Capability patterns](/reference/capability-patterns)
