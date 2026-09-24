---
title: "Backends"
description: "`llvm` is the compiler: it lowers the whole language to LLVM IR and hands the object to `cc`. The C backend is the project's own oracle, and the two agree byte for byte over the corpus."
isPublished: true
tags: "compiler"
---
`kelpc` has **one backend for anyone building a program**: `llvm`. It lowers the
typed IR to LLVM IR, runs LLVM's own pass pipeline over the module, emits an
object and hands it to `cc`. There is no backend to choose: no `--backend=` flag
and no `KELPC_BACKEND`.

| Backend | Emits | Finished with | Status |
| --- | --- | --- | --- |
| `llvm` (the one backend) | LLVM IR, then an object | `<out>.ll` and `<out>.o`, then `cc -O2 -o <out> <out>.o -lm` | the whole language the [Language](/language) pages describe; one guard remains for an owned temporary at a place the lowering did not stage, and nothing in the corpus reaches it; the object carries DWARF line locations |
| `c` (the project's own oracle) | C source text | `cc -O2 -fwrapv -lm` | complete and maintained, reached only through the project's internal switch, and the thing every `llvm` build is compared against: same stdout and exit status byte for byte over the corpus (223 of 223 targets, the refusal ranking empty) |

A retired spelling names its own removal rather than reading as an unknown flag.
Whatever `--backend=` carries is refused with

```text
error: --backend is gone: kelpc builds every program with the llvm backend, and the C backend is kept as the project's own oracle rather than as a user choice
```

and a set `KELPC_BACKEND` earns the same refusal, worded for the variable. A shell
that still exports the variable is the case silence would get wrong: it would keep
believing its builds used one backend while every one of them used the other.

The hand-written **`asm`** backend, which emitted x86-64 assembly text itself and
finished with `as` and `ld`, was retired on 2026-09-20 and its source was removed
on 2026-09-21. Its plan, its counts, its refusal
ranking and the measurements behind them are history rather than a live
measurement.

```sh
kelpc build examples/hello.kp   # llvm, the one backend
```

`backend.rs` holds the seam: how a backend is named, which names exist, and how
the default and the oracle switch resolve. `Backend::DEFAULT` is `llvm`, and the
`match` that calls a generator stays at its single call site in `main.rs`; it
becomes a trait when a third backend makes the interface worth naming.

## The LLVM backend

`kelpc` lowers the typed IR to **LLVM IR** and lets LLVM generate the object, the
way `rustc` does. This is MK7, begun at stage S1 on 2026-09-21, and the milestone
record is
[`plan/done.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/done.md).

It covers the **whole language**, the surface the [Language](/language) pages
describe. `c` is still the oracle that build is compared against, and the
categories below are what the differential sweep measures:

- the scalar types (`i32`, `i64`, `u32`, `u64`, `u8`, `u16`, `usize`, `isize`),
  `f32`/`f64`, `bool` and `char`: arithmetic, comparisons, `if`/`while`, calls,
  string literals and `print`;
- a `datac` at the same field order and natural alignment the C backend's typedef
  has, and `enum` at the same `{ tag, union }` shape, with `when`, `if let` and
  `?` and only the live variant dropped;
- `Bytes` and `String` through the runtime, an owned field, the drop plan
  `borrowck` produced emitted at the same points the C backend emits it, and
  `panic`, `assert` and the out-of-range panic of a narrowing conversion;
- `List`, `Map`, `Box` and the fixed-size `[T; N]` at the C backend's own header
  layouts, with the method surfaces, `for` over a list, a container as a field
  and an element, the bounds checks and one drop per container type;
- references that are not a `datac`: `Ty::Ref` is one `ptr` whatever the
  pointee, so `&place` is the place's address, `*p` a pointee-typed load and
  `*p = v` a store, and a `&T` parameter or return is a `ptr`;
- closures and function values: a named `fun` used as a value is its own address,
  a `fun` literal is a bare code pointer, and a capturing literal is the C
  backend's `{ ptr fn, ptr env, ptr drop }` fat pointer, one identified struct per
  signature, with the environment passed first to the code pointer and a heap
  environment of its own;
- the compiler-supplied `extern fun` bodies: the C text `externs.rs` holds,
  written to `<out>.externs.c` with the C backend's own includes, typedefs and
  prototypes and compiled into a per-program object linked between the IR object
  and `-lm`;
- the `pd` globals: one module-scope global per passdown with internal linkage,
  filled in declaration order by the generated `kelp_init_pds` so a chained
  initializer reads what an earlier one wrote, with `kelp_drop_pds` registered
  with `atexit` for an owned passdown, and `main` as `i32 @main(i32, ptr)` saving
  `kelp_argc`/`kelp_argv`, which `process.args()` reads;
- the capability check: the same call sites and the same arguments
  `codegen_c.rs::cap_plan` decides, the resource argument evaluated once into a
  value the check and the call share, against the per-`(module, domain)`
  allowlist arrays, with `runtime/cap_glue.c` compiled into the per-program
  object so the deny path's text is the C backend's byte for byte.

The corpus agrees byte for byte. The differential sweep builds every fixture the
C backend builds with `llvm` too, runs both and compares stdout and exit status:

```text
223 of 380 corpus targets built by 'c' (157 rejected by it),
223 also built by 'llvm', 0 refused, 0 mismatch(es), 0 crash(es)
```

`LLVM_BUILT_BASELINE` is 223 of the 223 targets the C backend builds and the
refusal ranking is empty, which is the plan's §4.1 gate. The deny path is
byte-identical on all eight denied projects: stdout, stderr and the exit status
compare equal between the two backends, including `caps_double_eval`, whose
stdout is one `SIDE` line under both, which is the once-only resource evaluation
the C side needed a fix for.

Each slice keeps its own gate, and each also reads the shape it is about back out
of the `<out>.ll` the backend wrote:
`kelpc/tests/run-llvm-scalar-subset.sh`, `run-llvm-datac-subset.sh`,
`run-llvm-strings-drops.sh`, `run-llvm-enum-subset.sh`, `run-llvm-containers.sh`,
`run-llvm-references.sh`, `run-llvm-closures.sh` (120 tests),
`run-llvm-externs.sh` (138 tests) and `run-llvm-pd-caps.sh` (38 tests). The reads
are the ones no fixture's own output would catch: the tag and payload offsets of
three SysV `enum` classes, the container header and entry layouts and the
guarantee that no runtime declaration passes a container header by value, the
borrowed-parameter signatures as `kelp_origin(ptr)`-style pointers and a `panic`
tail ending in `unreachable`, the fat pointer's `{ ptr, ptr, ptr }` shape, `fun`
parameters and returns as `ptr`, a call through a closure passing the environment
first, and each extern declaration matching its body's C signature. The
`run-llvm-pd-caps.sh` gate adds the last half: the `pd` globals, the capability
check and the last three refusals, and it pins the deny path's text against the C
backend's own. Six of the nine gates strip a `, !dbg !N` suffix before asserting
an instruction's shape: where a line came from is a separate claim from what the
instruction is. The ignored valgrind sweep covers 32 `pd`/capability binaries
besides the closure, extern and container sweeps, and the four LLVM sweeps plus
the C sweep (209 binaries) are green.

The backend no longer refuses a corpus construct. One guard stays, in
`codegen_llvm.rs::place_of`, for an owned rvalue no staging site claimed; its
message is `error: the llvm backend cannot lower 'an owned temporary' at a place
this lowering does not stage yet (MK7 S3); this is a compiler defect`. Nothing in
the corpus
reaches it, and it is kept because a wrong lowering is worse than a named refusal:
a place this lowering did not stage is a bug, and the guard turns it into a
diagnostic rather than a miscompile. Read the empty refusal ranking as a
measurement over the corpus, not as a promise that the backend can never refuse.

- **What is reused:** everything up to the typed IR. The lexer, the preprocessor,
  the parser, the type checker, the move and borrow checker and the meaning of
  every AST construct do not depend on the target, so only the emission layer is
  new.
- **What LLVM supplies now:** the module pass pipeline, instruction selection,
  register allocation, the encoder, the ELF writer, DWARF and an object.
- **A fault in an `llvm` binary names the `.kp` file and line.** The object
  carries DWARF line locations, so a program that faults at run time prints a
  backtrace whose frame is a `.kp` source line, and `llvm-symbolizer` or
  `addr2line` resolves the same address to the same `file:line:column`. The C
  backend's `#line` was the only route to that, and this is stage S4's exit
  criterion rather than a nice-to-have: for a default backend, a crash report
  that points into generated IR instead of a Kelp source line is the difference
  between actionable and not. What it is: a line table, one compile unit per
  module, one file per `.kp` source, one subprogram per `.kp`-declared function
  carrying its declaration's own line, and a location per statement and block
  tail. What it is not: no variables, no types, no lexical blocks, no `inlinedAt`
  (nothing inlines), and no subprogram for the generated helpers (the drops, the
  container sets, the closure machinery) or for an `extern fun` whose body is C. A
  location is per statement rather than per sub-expression, which is the C
  backend's granularity too. `kelpc/tests/llvm_debug_info.rs` is the proof: its fixture
  `kelpc/tests/llvm-debug/fault.kp` divides by a run-time zero on purpose, and
  the test reads the decoded line table back with `readelf` and places the fault
  at `fault.kp:16` through `gdb`.
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
- **The `extern fun` bodies are the C backend's own text too:** `externs.rs` holds
  the C for every compiler-supplied `extern fun`, and `codegen_c.rs` writes it
  into every generated C program. The `llvm` path writes the same text to
  `<out>.externs.c`, with the C backend's own includes, typedefs and prototypes,
  and links the object it compiles between the IR object and `-lm`. A fixed
  object cannot work, because one body calls a `std/path` function only the
  resolver injects and another names a per-program container typedef.
- **Where it stands:** S6 (the optimization-level decision) and S7 (the flip)
  landed on 2026-09-21, so `build` and `run` take `-O0`, `-O1`, `-O2`, `-O3` or
  `-Os`, with `-O2` the default, and `llvm` is the one backend a person can build
  with. S5 (fuzzing and conformance) landed the same day as
  `kelpc/tests/differential_fuzz.rs`: one seed is one program, built with both
  backends and compared byte for byte, 256 seeds with 0 mismatches, plus a
  checked-in 24-seed conformance corpus. It found and fixed two defects the
  curated corpus could not see, both `llvm`-confined: a float `List`'s `contains`
  emitted an integer compare, and an unread owned `pd` made `atexit` drop a
  container set that was never declared. The MK7 record in `plan/done.md`
  names each stage.
- **One level is one level for the whole build:** the level selects the module
  pass pipeline LLVM runs, the target machine's codegen level, and the `-O` flag
  the per-program C object and the final link are given, so the differential
  sweep compares the two backends *at a level* rather than two runs that happen
  to agree. `-Oz` is refused, because it is a clang-only spelling and the linking
  `cc` may be gcc; `-Os` is the size level. There is still no measurement behind
  the `llvm` backend, so it is not claimed to match the C backend's speed: the
  `bench/speed` numbers are the C path's.
- **Crate and linking:** `llvm-sys` plus a thin wrapper of our own, linked
  dynamically against the host's `libLLVM`. Every `kelpc` links `libLLVM-21.so`
  and needs it at runtime, whichever backend it is run with: on a build from this
  checkout the
  RUNPATH points into the nix store, and a binary built elsewhere records a
  different path. The trade-offs are in the plan's §1. The dev shell that
  provides the LLVM build half is `shell.nix` at the repository root.
- **Artifacts:** the LLVM path writes `<out>.ll` (textual IR) and `<out>.o` beside
  the binary, where the C path writes `<out>.c`. A program that reaches an
  `extern fun` also gets `<out>.externs.c`, the C source of its extern object.
  Linking still goes through `cc` (`cc -o <out> <out>.o -lm`, at the build's
  optimization level, with the runtime object and, when the program reaches one,
  the extern object on the line), which is the plan's §1.3 decision.

## The C backend is the oracle

The fixture suite is backend-agnostic by construction: it compiles a fixture, runs
the result, and compares stdout. So the C backend's own output is the thing an
`llvm` build is measured against, rather than a second opinion. The suite runs
`llvm` by default and the C oracle through the project's internal switch, and
`./kelpc/tests/run-all-backends.sh` runs both (`BACKENDS`, default `c llvm`),
which it could not while one test asserted the C backend's own `.c` sat beside
the artifact.

Two consequences worth knowing:

1. **The C backend is never deleted and never stops being maintained**, and the
   project's internal oracle switch keeps reaching it. With one backend,
   "correct" means "matches the author's intent"; with the oracle beside it, it is
   a measurement over the corpus, and a backend with no way back is how an oracle
   stops being one.

2. **A construct a backend cannot lower must be refused by name, never
   miscompiled.** The `llvm` backend already follows this (the guard above). The
   differential sweep that enforces it, `kelpc/tests/backend_coverage.rs`, was
   removed with the `asm` rows and has been rebuilt against the LLVM backend,
   where the baseline is `LLVM_BUILT_BASELINE`:
   it builds every fixture the C backend builds with `llvm`, runs both and compares
   stdout and exit status byte for byte, and records a refusal with its message
   rather than failing it. The baseline is 223 of the 223 targets and the ranking
   is empty. A refusal that arrived with a new fixture would still be recorded, so
   the ratchet stays the instrument: it may only rise, and a backward step is a
   regression. On its first run it caught a silent miscompile, a borrow returned
   through the value position of an `if` and a returned `&String`, which now match
   the C backend.

## See also

- [Pipeline](/compiler/architecture)
- [Runtime](/compiler/runtime)
- [Tests](/compiler/tests)
- [Install and build](/getting-started/install): the flags and environment variables
