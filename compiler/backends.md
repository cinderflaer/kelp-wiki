---
title: "Backends"
description: "A code generator is selectable with --backend= or the KELPC_BACKEND environment variable, and an explicit flag wins over the variable; the default is c. The llvm backend lowers the scalar subset and refuses everything else by name."
isPublished: true
tags: "compiler"
---
A code generator is selectable, chosen with `--backend=` or the
`KELPC_BACKEND` environment variable. An explicit flag wins over the variable;
the default is `c`.

| Backend | Emits | Finished with | Status |
| --- | --- | --- | --- |
| `c` (default) | C source text | `cc -O2 -fwrapv -lm` | complete, and the reference |
| `llvm` | LLVM IR, then an object | `<out>.ll` and `<out>.o`, then `cc -O2 -o <out> <out>.o -lm` | the scalar subset only (MK7 S1); everything outside it is refused by name |

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
way `rustc` does. This is MK7 stage S1, done on 2026-09-21, and the plan of record
is
[`plan/mk7-llvm-backend.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-llvm-backend.md).

At S1 it covers the **scalar subset only**: the integer types (`i32`, `i64`,
`u32`, `u64`, `u8`, `u16`, `usize`, `isize`), `f32`/`f64`, `bool`, `char`,
arithmetic, comparisons, `if`/`while`, calls, string literals and `print`. On a
program that stays inside it, the `llvm` backend's stdout is byte-identical to the
C backend's, which is the gate: `kelpc/tests/run-llvm-scalar-subset.sh`.

Everything outside the subset is **refused by name**, never miscompiled and never
a panic. The error names the construct and the MK7 stage that will lower it:

```text
$ kelpc build src/main.kp --backend=llvm
error: the llvm backend cannot lower 'datac' yet (MK7 S2); use --backend=c
```

`datac`, `enum`, `pd`, arrays, references, closures, containers and `extern fun`
are all refused today.

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
- **Scale:** S2 to S7 remain, roughly 3 to 6 weeks of emission-layer work to a
  suite-green backend (the plan's §0.1 and §5).
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
   miscompiled.** The `llvm` backend already follows this at S1 (the errors
   above). The differential sweep that enforces an agreed refusal prefix,
   `kelpc/tests/backend_coverage.rs`, was removed with the `asm` rows; it is
   rebuilt against the LLVM backend (`plan/mk7-llvm-backend.md` §6), where the
   baseline becomes `LLVM_BUILT_BASELINE`.

## See also

- [Pipeline](/compiler/architecture)
- [Runtime](/compiler/runtime)
- [Tests](/compiler/tests)
- [Install and build](/getting-started/install): the flags and environment variables
