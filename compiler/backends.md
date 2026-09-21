---
title: "Backends"
description: "A code generator is selectable with --backend= or the KELPC_BACKEND environment variable, and an explicit flag wins over the variable; the default is c. The llvm backend lowers the scalar subset, `datac` records, the heap slice, tagged unions, the containers, references that are not a `datac`, and closures and function values, and refuses everything else by name."
isPublished: true
tags: "compiler"
---
A code generator is selectable, chosen with `--backend=` or the
`KELPC_BACKEND` environment variable. An explicit flag wins over the variable;
the default is `c`.

| Backend | Emits | Finished with | Status |
| --- | --- | --- | --- |
| `c` (default) | C source text | `cc -O2 -fwrapv -lm` | complete, and the reference |
| `llvm` | LLVM IR, then an object | `<out>.ll` and `<out>.o`, then `cc -O2 -o <out> <out>.o -lm` | the scalar subset (MK7 S1), `datac` records (MK7 S2A), the heap slice: `Bytes`/`String`, an owned field, drops, `panic` and `assert` (MK7 S2B), tagged unions: `enum` at the C `{ tag, union }` layout, `when`, `if let`, `?`, and one `switch` per drop (MK7 S2C), the containers: `List`, `Map`, `Box` and `[T; N]` (MK7 S2D), references that are not a `datac`: a `&T` to a scalar, a borrow of a field, the read and the write through one, and a `&T` parameter or return (MK7 S2F), and closures and function values: a declared `fun` as a bare code pointer, a `fun` literal, a capturing closure as the C backend's `{ ptr fn, ptr env, ptr drop }` fat pointer with a heap environment and its own drop, a function value or closure as a local, a parameter, a return value and a `datac` field, and a call through a value, with the environment passed first (MK7 S2E); everything outside them is refused by name |

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
`switch` on the tag per owning enum. At S2D, landed on 2026-09-21, it adds the
**containers**: `List`, `Map`, `Box` and the fixed-size `[T; N]`, as one
monomorphized IR function set per element or value type, with the C backend's own
header layouts, matched field for field: `List` and `String` as
`{ ptr, i64, i64 }`, `Box` as `{ ptr }`, `Map` as `{ ptr, i64, i64, i64, ptr,
i64, i64 }` with an entry `{ K, ptr, i8 }`, and an array inline as `[N x T]`.
Construction, the method surfaces, `for` over a list, a container as a local, a
parameter, a return value, a `datac` field and an element, the bounds checks and
one drop per container type all lower, and the bounds and panic text is
byte-identical to the C backend's.

At S2F, landed on 2026-09-21, it adds **references that are not a `datac`**: a
`&T` to a scalar, a borrow of a field, the read through one, the write through an
exclusive one, and a `&T` parameter or return value. `Ty::Ref` is one `ptr`
whatever the pointee, so `&place` is the place's address, `*p` is a pointee-typed
load and `*p = v` a store through it. At S2E, landed on 2026-09-21, it adds
**closures and function values**: a named `fun` used as a value is the function's
own address, a `fun` literal is a bare code pointer, and a literal that captures
is a closure at the C backend's fat pointer, one identified struct per signature,
`{ ptr fn, ptr env, ptr drop }`. The code pointer takes the environment as its
hidden first argument, so an indirect call is `fn(env, args...)`; a `fun`
parameter or return is a bare `ptr`. A function value or closure lowers as a
local, a parameter, a return value and a `datac` field, and the heap environment
is allocated with the same `malloc`/`free` the rest of the runtime uses. On a
program that stays inside the seven, the
`llvm` backend's stdout is byte-identical to the C backend's, which is the gates:
`kelpc/tests/run-llvm-scalar-subset.sh`,
`kelpc/tests/run-llvm-datac-subset.sh`,
`kelpc/tests/run-llvm-strings-drops.sh`,
`kelpc/tests/run-llvm-enum-subset.sh`,
`kelpc/tests/run-llvm-containers.sh`,
`kelpc/tests/run-llvm-references.sh` and
`kelpc/tests/run-llvm-closures.sh`, each carrying the earlier gates' fixtures
forward: the S2D gate adds the container fixtures (103 tests), the S2F gate the
reference fixtures (109 tests in one run) and the S2E gate the closure and
function-value fixtures (120 tests in one run). Each gate also reads the shape it
is about back out of the `<out>.ll` the backend wrote and asserts it: the S2C gate
the tag and payload offsets (three SysV classes, a one-byte union at offset 4, an
eight-byte union at offset 8 and a 24-byte one at offset 8), and the S2D gate the
container header and entry layouts, plus the guarantee that no runtime declaration
passes a container header by value. The S2F gate reads the borrowed-parameter
functions' signatures back out of the IR, asserting each takes a
`kelp_origin(ptr)`-style pointer, and asserts that a `panic` tail ends in
`unreachable`. The S2E gate reads the fat pointer's shape back as `{ ptr, ptr,
ptr }`, that a `fun` parameter and a `fun` return are both `ptr`, that a call
through a closure passes the environment first, and the shape of a two-field
environment (an `i32`, an `i64` and an owned `String` at their own alignments).
No fixture's own output would catch any of them.

Everything outside them is **refused by name**, never miscompiled and never a
panic. The error names the construct and the MK7 stage that will lower it:

```text
$ kelpc build src/main.kp --backend=llvm
error: the llvm backend cannot lower the call to 'std.mem.alloc_raw' yet (MK7 S3); use --backend=c
```

A field that owns a `String` or a `Bytes` lowers at S2B, a container or an
array field at S2D, and a borrow of a field at S2F. What is still refused: a
`str`, `View` or reference field in a `datac` (S2F, an arm the frontend never
reaches because it refuses a borrowed field before codegen), and `pd`,
`extern fun` and the raw stdlib externs (S3). No refusal names a closure or a
function value any more: a closure that reaches no stdlib import lowers at S2E,
and a closure-shaped fixture that still refuses does so under the S3 message,
because the backend lowers an `impl`ed module whole and `std/str` reaches
`std.mem.alloc_raw`. A
borrow of anything that is not a `datac` is no longer refused: S2F lowers it. An
`enum` is not, and neither is a container: S2C lowers the tagged union with
`when`, `if let` and `?`, and S2D lowers `List`, `Map`, `Box` and `[T; N]`.

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
- **Scale:** S3 to S7 remain, roughly 3 to 6 weeks of emission-layer work to a
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
   differential sweep that enforces it, `kelpc/tests/backend_coverage.rs`, was
   removed with the `asm` rows and has been rebuilt against the LLVM backend
   (`plan/mk7-llvm-backend.md` §6), where the baseline is `LLVM_BUILT_BASELINE`:
   it builds every fixture the C backend builds with `llvm`, runs both and compares
   stdout and exit status byte for byte, records each refusal with its message, and
   ratchets a coverage count that may only rise (140 of the 220 targets at the S2E
   tip, 80 of them refused, all by name: the runtime, `extern fun` and `pd` slice
   (S3) leads with 77, then the two owned-temporary shapes (S2B) with 3; no
   refusal names a closure or a function value any more, and none is unnamed, so
   the ranking is one slice, S3). On its first run it
   caught a silent miscompile,
   a borrow returned through the value position of an `if` and a returned `&String`,
   which now match the C backend.

## See also

- [Pipeline](/compiler/architecture)
- [Runtime](/compiler/runtime)
- [Tests](/compiler/tests)
- [Install and build](/getting-started/install): the flags and environment variables
