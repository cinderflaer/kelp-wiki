---
title: "Runtime"
description: "Most of what a program needs at run time is emitted by the code generator rather than linked - the Bytes/String heap routines, bounds checks, drop calls and the capability plumbing are C text that..."
isPublished: true
tags: "compiler"
---
Most of what a program needs at run time is emitted by the code generator rather
than linked: the `Bytes`/`String` heap routines, bounds checks, drop calls and the
capability plumbing are C text that `codegen_c.rs` splices into the generated
program. Three files in `kelpc/runtime/` are what stayed C on purpose, and one of
them is no longer emitted at all.

| File | Status | Role |
| --- | --- | --- |
| `cap_glue.c` | emitted into every program that contains a gated call | the non-matching half of the capability check |
| `cap_matcher_ref.c` | not emitted | the C capability matcher, kept as the differential oracle |
| `path_normalize_ref.c` | not emitted | the C path normalizer, kept as the differential oracle |

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

MK7's §8 track moves the runtime from C text into Kelp one piece at a time. The
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

## What is still C in the runtime, and what that costs

| Item | State |
| --- | --- |
| Capability matcher | Kelp (`std/rt.kp`), with the C oracle kept |
| Path normalizer | Kelp (`std/rt.kp`), with the C oracle kept |
| Symlink resolution (`kelp_resolve_path`) | still C |
| The allocator | still C; blocked on raw pointers, which the language does not expose |
| The `Bytes`/`String` heap routines and drop calls | emitted as a fixed C preamble by `codegen_c.rs` |

`std/rt` is compiler-internal: it is not in `stdlib.rs::shipped()`, so a program
cannot import it, and the resolver injects it for a program that imports a gated
module.

## See also

- [Backends](/compiler/backends)
- [Tests](/compiler/tests)
- [Capabilities](/language/capabilities)
- [Capability patterns](/reference/capability-patterns)
