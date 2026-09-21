---
title: "Backends"
description: "One code generator is selectable with --backend= or the KELPC_BACKEND environment variable, and an explicit flag wins over the variable; the default is c. The next backend is LLVM IR."
isPublished: true
tags: "compiler"
---
One code generator is selectable, chosen with `--backend=` or the
`KELPC_BACKEND` environment variable. An explicit flag wins over the variable;
the default is `c`.

| Backend | Emits | Finished with | Status |
| --- | --- | --- | --- |
| `c` (default) | C source text | `cc -O2 -fwrapv -lm` | complete, and the reference |

The hand-written **`asm`** backend, which emitted x86-64 assembly text itself and
finished with `as` and `ld`, was retired on 2026-09-20 and its source was removed
on 2026-09-21. `--backend=asm` is no longer accepted; the diagnostic reads
`unknown backend 'asm'; expected one of: c`. Its plan, its counts, its refusal
ranking and the measurements behind them stay as history in
[`plan/asm-backend/`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/asm-backend/).

```sh
kelpc build examples/hello.kp                 # the default, and the reference
KELPC_BACKEND=c kelpc run examples/hello.kp   # the same, spelled out
```

`backend.rs` holds only the selector: how a backend is named, which names exist,
and how the choice is resolved. The `match` that calls a generator stays at its
single call site in `main.rs`, and it becomes a trait when a third backend makes
the interface worth naming. `llvm` is the next name it will carry.

## The next backend is LLVM IR

`kelpc` will emit **LLVM IR** and let LLVM optimize and generate the code, the way
`rustc` does. The plan of record is
[`plan/mk7-llvm-backend.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/mk7-llvm-backend.md).

- **What is reused:** everything up to the typed IR. The lexer, the preprocessor,
  the parser, the type checker, the move and borrow checker and the meaning of
  every AST construct do not depend on the target, so only the emission layer is
  new.
- **What LLVM supplies:** the optimizer, register allocation, instruction
  selection, the encoder, the ELF writer, the debug-info format, sanitizers and
  the target list. The retired plan called the optimizer alone "the multi-year
  part".
- **What stays ours:** the lowering from `tir` to IR, and Kelp's move and borrow
  semantics mapped onto LLVM's model, which includes the new UB surface: no
  `nsw`/`nuw`, no `inbounds`, and `noalias` only where the borrow checker proves
  it. `-fwrapv` stops being a flag on the C path and becomes "we never write the
  flag that would make overflow undefined".
- **Scale:** roughly feature-complete with the fixture suite green in about 3 to
  6 weeks of work, not months and not years. The phases and their estimates are in
  the plan's §0.1, and the stages in its §5.
- **Crate and linking:** `llvm-sys` plus a thin wrapper of our own, linked
  dynamically against the host's `libLLVM`, which makes the LLVM major part of the
  compiler's build contract. The trade-offs are in the plan's §1. The dev shell
  that provides the LLVM build half is `shell.nix` at the repository root.
- **Debug info:** LLVM emits DWARF from the locations we attach, so the format is
  not our work; the C backend's `#line` directive stays until that lands.

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
   miscompiled.** The differential sweep that enforced an agreed refusal prefix,
   `kelpc/tests/backend_coverage.rs`, was removed with the `asm` rows; it is
   rebuilt against the LLVM backend (`plan/mk7-llvm-backend.md` §6), where the
   baseline becomes `LLVM_BUILT_BASELINE`.

## See also

- [Pipeline](/compiler/architecture)
- [Runtime](/compiler/runtime)
- [Tests](/compiler/tests)
- [Install and build](/getting-started/install): the flags and environment variables
