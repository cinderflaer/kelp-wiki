---
title: "Backends"
description: "Two code generators are selectable with --backend= or the KELPC_BACKEND environment variable, and an explicit flag wins over the variable; the default is c. The next backend is LLVM IR, and the hand-written assembly backend is retired as a direction."
isPublished: true
tags: "compiler"
---
Two code generators are selectable, chosen with `--backend=` or the
`KELPC_BACKEND` environment variable. An explicit flag wins over the variable;
the default is `c`.

| Backend | Emits | Finished with | Status |
| --- | --- | --- | --- |
| `c` (default) | C source text | `cc -O2 -fwrapv -lm` | complete, and the reference |
| `asm` | x86-64 assembly text | `as --64`, then `ld` with `crt1.o`/`crti.o`/`crtn.o`, `-lc`, `-lm` | selectable, but **retired as a direction** |

`asm` still builds most of the language. It is removed from the compiler once the
LLVM backend passes the fixture corpus, and it stays selectable until then because
a backend that is still selectable must still work. Its counts, its refusal
ranking and the measurements behind them are in
[`plan/asm-backend/plan.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/asm-backend/plan.md)
§0 and §5.

```sh
kelpc build examples/hello.kp --backend=asm   # until the LLVM backend lands
KELPC_BACKEND=c kelpc run examples/hello.kp   # the oracle, and the default
```

`backend.rs` holds only the selector: how a backend is named, which names exist,
and how the choice is resolved. The `match` that calls a generator stays at its
single call site in `main.rs`, and it becomes a trait when a third backend makes
the interface worth naming.

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
  compiler's build contract. The trade-offs are in the plan's §1.
- **Debug info:** LLVM emits DWARF from the locations we attach, so the format is
  not our work; the C backend's `#line` directive stays until that lands.

## The C backend is the oracle

The fixture suite is backend-agnostic by construction: it compiles a fixture, runs
the result, and compares stdout. So a second backend is validated by running the
suite again with `KELPC_BACKEND` set to it, and the C backend's own output becomes
the thing the new backend is compared against, rather than a second opinion.

Three consequences worth knowing:

1. **A construct a second backend cannot lower is refused by name, never
   miscompiled.** The refusal prefix is a constant in the test suite
   (`REFUSAL_PREFIX`, `kelpc/tests/backend_coverage.rs`), and the differential
   sweep asserts that every refusal begins with it. The `asm` backend's refusals
   read like this one:

   ```
   error: the 'asm' backend does not support the `extern fun std.process.arg_count_raw` yet
   ```

2. **A refusal is a feature.** A backend earns coverage by agreeing with the C
   backend on the fixtures it does build, and the coverage number can only rise.

3. **`--backend=c` and `KELPC_BACKEND=c` stay selectable forever**, and
   `codegen_c.rs` is never deleted. With one backend, "correct" means "matches the
   author's intent"; with two, it is a measurement over the corpus. A flip with no
   way back is how a second backend becomes unmaintained.

## See also

- [Pipeline](/compiler/architecture)
- [Runtime](/compiler/runtime)
- [Tests](/compiler/tests)
- [Install and build](/getting-started/install): the flags and environment variables
