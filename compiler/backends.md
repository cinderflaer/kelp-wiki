---
title: "Backends"
description: "A code generator is selectable with --backend= or the KELPC_BACKEND environment variable, and an explicit flag wins over the variable; the default is c. The llvm backend lowers the scalar subset, `datac` records, the heap slice and tagged unions, and refuses everything else by name."
isPublished: true
tags: "compiler"
---
A code generator is selectable, chosen with `--backend=` or the
`KELPC_BACKEND` environment variable. An explicit flag wins over the variable;
the default is `c`.

| Backend | Emits | Finished with | Status |
| --- | --- | --- | --- |
| `c` (default) | C source text | `cc -O2 -fwrapv -lm` | complete, and the reference |
| `llvm` | LLVM IR, then an object | `<out>.ll` and `<out>.o`, then `cc -O2 -o <out> <out>.o -lm` | the scalar subset (MK7 S1), `datac` records (MK7 S2A), the heap slice: `Bytes`/`String`, an owned field, drops, `panic` and `assert` (MK7 S2B), and tagged unions: `enum` at the C `{ tag, union }` layout, `when`, `if let`, `?`, and one `switch` per drop (MK7 S2C); everything outside them is refused by name |

The hand-written **`asm`** backend, which emitted x86-64 assembly text itself and
finished with `as` and `ld`, was retired on 2026-09-20 and its source was removed
on 2026-09-21. `--backend=asm` is no longer accepted; the diagnostic reads
`unknown backend 'asm'; expected one of: c, llvm`. Its plan, its counts, its refusal
ranking and the measurements behind them stay as history in
[`plan/asm-backend/`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/asm-backend/).

```sh
kelpc build examples/hello.kp                 # the default, and the reference
KELPC_BACKEND=c kelpc run examples/hello.kp   # the same, spelled out
```

`backend.rs` holds only the selector: how a backend is named, which names exist,
and how the choice is resolved. The `match` that calls a generator stays at its
single call site in `main.rs`, and it becomes a trait when a third backend makes
the interface worth naming.

## The LLVM backend

`kelpc` lowers the typed IR to **LLVM IR** and lets LLVM generate the object, the
way `rustc` does. This is MK7, begun at stage S1 on 2026-09-21, and the plan of
record is
[`plan/mk7-llvm-backend.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-llvm-backend.md).

At S1 it covers the **scalar subset**: the integer types (`i32`, `i64`, `u32`,
`u64`, `u8`, `u16`, `usize`, `isize`), `f32`/`f64`, `bool`, `char`, arithmetic,
comparisons, `if`/`while`, calls, string literals and `print`. At S2A, landed on
2026-09-21, it adds a **`datac` whose fields are all scalars or earlier
all-scalar `datac`s**: the struct type at the same field order and natural
alignment the C backend's typedef has, construction, a field read and a field
write, a whole-value assignment, a nested struct, a struct as a local, a `move`
parameter and a return value, a field mutated through a method's `self`, and the
shared or exclusive borrow a `datac` parameter resolves to, which is the same
address either way. At S2B, landed on 2026-09-21, it adds the **heap and the
runtime**: `Bytes` and `String` as a pointer and a length reached through the
runtime, a `datac` field that owns one, the **drop plan** `borrowck` produced
emitted at the same points the C backend emits it (the end of a block, before a
`return`, and before an assignment overwrites an owned binding, with a move
clearing its source slot), and `panic`, `assert` and the out-of-range panic of a
narrowing conversion. At S2C, landed on 2026-09-21, it adds the **tagged union**:
`enum` at the same `{ tag, union }` shape the C backend gives it, an `i32` tag at
offset 0 and the payload at the C union's offset, with the size and alignment read
from the target machine's data layout rather than assumed. Construction, a payload
read, an `enum` as a local, a parameter and a return value, a nested payload,
`when`, `if let` and `?` all lower, and only the live variant is dropped: one
`switch` on the tag per owning enum. On a program that stays inside the four, the
`llvm` backend's stdout is byte-identical to the C backend's, which is the gates:
`kelpc/tests/run-llvm-scalar-subset.sh`,
`kelpc/tests/run-llvm-datac-subset.sh`,
`kelpc/tests/run-llvm-strings-drops.sh` and
`kelpc/tests/run-llvm-enum-subset.sh`, the last of which carries the first three
forward and adds the tagged-union fixtures: 58 tests in one run. It also reads the
tag and payload offsets back out of the `<out>.ll` the backend wrote and asserts
them, which no fixture's own output would catch: three SysV classes, a one-byte
union at offset 4, an eight-byte union at offset 8 and a 24-byte one at offset 8.

Everything outside them is **refused by name**, never miscompiled and never a
panic. The error names the construct and the MK7 stage that will lower it:

```text
$ kelpc build src/main.kp --backend=llvm
error: the llvm backend cannot lower 'a List field' yet (MK7 S2D); use --backend=c
```

A field that owns a `String` or a `Bytes` lowers at S2B; a container or an array
field does not. `List`, `Map`, `Box` and arrays generally, a `str` or `View`
field in a `datac` (S2D), a borrow of anything that is not a `datac`, closures and
function values (S2E), `pd` and `extern fun` (S3) are all refused today. An `enum`
is not: S2C lowers it, and with it `when`, `if let` and `?`.

- **What is reused:** everything up to the typed IR. The lexer, the preprocessor,
  the parser, the type checker, the move and borrow checker and the meaning of
  every AST construct do not depend on the target, so only the emission layer is
  new.
- **What LLVM supplies now:** instruction selection, register allocation, the
  encoder and the ELF writer, and an object at LLVM's default codegen level. The
  optimizer and DWARF are still to come.
- **What stays ours:** the lowering from `tir` to IR, and Kelp's move and borrow
  semantics mapped onto LLVM's model, which includes the new UB surface: no
  `nsw`/`nuw`, no `inbounds`, and `noalias` only where the borrow checker proves
  it. `-fwrapv` stops being a flag on the C path and becomes "we never write the
  flag that would make overflow undefined".
- **The runtime's one home:** `kelpc/runtime/kelp_rt.c` holds the
  bytes/string routines, `kelp_panic`/`kelp_assert`, the allocation helpers and
  `kelp_argc`/`kelp_argv`. `codegen_c.rs` still emits that text into every
  generated C program, byte for byte; the `llvm` path links it as an object that
  `kelpc/build.rs` compiles from the same file. One source, so the panic text
  and the `Bytes`/`String` invariants cannot drift between the backends.
- **Scale:** S2D to S7 remain, roughly 3 to 6 weeks of emission-layer work to a
  suite-green backend (the plan's §0.1 and §5, whose stage-2 table names each
  slice the refusals point at).
- **No pass pipeline yet:** there is no IR optimization pass pipeline, so the
  object is emitted at LLVM's default codegen level. Choosing the pipeline is
  stage S6, and debug info (DWARF from attached locations) is stage S4. There is
  no measurement behind the `llvm` backend, so it is not claimed to match the C
  backend's speed: the `bench/speed` numbers are the C path's.
- **Crate and linking:** `llvm-sys` plus a thin wrapper of our own, linked
  dynamically against the host's `libLLVM`. A `kelpc` built with this backend
  links `libLLVM-21.so` and needs it at runtime: on a build from this checkout the
  RUNPATH points into the nix store, and a binary built elsewhere records a
  different path. The trade-offs are in the plan's §1. The dev shell that
  provides the LLVM build half is `shell.nix` at the repository root.
- **Artifacts:** the LLVM path writes `<out>.ll` (textual IR) and `<out>.o` beside
  the binary, where the C path writes `<out>.c`. Linking still goes through `cc`
  (`cc -O2 -o <out> <out>.o -lm`), which is the plan's §1.3 decision.

## The C backend is the oracle

The fixture suite is backend-agnostic by construction: it compiles a fixture, runs
the result, and compares stdout. So a second backend is validated by running the
suite again with `KELPC_BACKEND` set to it, and the C backend's own output becomes
the thing the new backend is compared against, rather than a second opinion.

Two consequences worth knowing:

1. **`--backend=c` and `KELPC_BACKEND=c` stay selectable forever**, and
   `codegen_c.rs` is never deleted. With one backend, "correct" means "matches the
   author's intent"; with two, it is a measurement over the corpus. A flip with no
   way back is how a second backend becomes unmaintained.

2. **A construct a second backend cannot lower must be refused by name, never
   miscompiled.** The `llvm` backend already follows this (the errors above). The
   differential sweep that enforces an agreed refusal prefix,
   `kelpc/tests/backend_coverage.rs`, was removed with the `asm` rows; it is
   rebuilt against the LLVM backend (`plan/mk7-llvm-backend.md` §6), where the
   baseline becomes `LLVM_BUILT_BASELINE`.

## See also

- [Pipeline](/compiler/architecture)
- [Runtime](/compiler/runtime)
- [Tests](/compiler/tests)
- [Install and build](/getting-started/install): the flags and environment variables
