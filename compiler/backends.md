---
title: "Backends"
description: "kelpc builds every program with the LLVM backend, the only code generator. The retired C backend and its selectors are refused by name. Covers the LLVM lowering steps, the value layouts and the optimisation levels."
isPublished: true
tags: "compiler"
---
`kelpc` builds every program with one backend, `llvm`.
The C backend has been removed. Its golden outputs remain in the tree, and the selectors that reached it are refused by name.

## Choosing a backend

The LLVM backend is the only code generator. There is no choice to make.
The retired selectors are refused by name:

- `--backend` and `--backend=...`;
- `KELPC_BACKEND`, when it is set;
- `KELPC_ORACLE`, when it is set, for any value.

The refusal says the backend is no longer a user choice.
`backend.rs` is the only module that mentions the retired selectors, and it only refuses them.
`main.rs` calls `codegen_llvm::compile` at its single call site.

Some features are refused by name on the LLVM backend:

- sanitizers, because the LLVM backend has no sanitizer passes;
- `--incremental` for a freestanding project, and for a hosted project named on the command line. A hosted manifest that sets `[build] incremental = true` is built whole-program, with a warning.

## The LLVM backend

`codegen_llvm.rs` lowers the typed IR to LLVM IR.
`llvm_ffi.rs` is the only code that calls LLVM.
It wraps `llvm-sys` 211, which is LLVM 21.1, and links it dynamically.

`compile` and `lower_to_object` in `codegen_llvm/driver.rs` do the work:

1. Create the target machine first. Enum sizes come from the data layout, so the layout must be known before any type is built (in `compile`).
2. Create the module, set the triple and data layout, and build the generator state (`Gen::new`).
3. Declare every type, aggregate, closure environment, capability array, drop, clone and compare function, and function signature (`Gen::declare`).
4. Emit the bodies. One `FnGen` emits each non-extern function (`emit_all`).
5. Verify the module, and write the unoptimised IR to `<out>.ll` before any pass runs.
6. Run the pass pipeline for the chosen level, verify again, and write `<out>.o`.
7. If the program has a user `extern fun` or a gated call, lower its trampolines, callback glue and capability allowlists to LLVM IR and write them to `<out>.externs.o` with the same target machine (`lower_externs_object`, `extern_object.rs`).
8. Link. See [Driver](/compiler/driver#linking).

The per-program externs object holds the user `extern fun` trampolines, the native-callback glue and the capability allowlists.
It is written only when the program has one of them, and it is LLVM IR like the rest of the program: no C source is written and no C compiler runs.

### Value layouts

- Scalars: `i32`, `u32` and `char` are `i32`. `i64`, `u64`, `usize` and `isize` are `i64`. `u8` is `i8`, `u16` is `i16` and `bool` is `i1`.
- `str`, borrows, `Thread`, `Mutex`, handles and raw pointers are one opaque `ptr` (`llvm_type`).
- `String` and `Bytes` are `{ ptr, i64 len, i64 cap }`. `View` is `{ ptr, i64 len }`.
- A `datac` is an identified struct with its fields in declaration order (`declare_aggregates`).
- An `enum` is `{ tag, union }`. The tag width follows the `repr`, and it is `i32` by default.
- `Option` and `Result` have no special layout. They are ordinary enums.
- `List<T>` is `{ ptr, i64 len, i64 cap }`. `Box<T>` is `{ ptr }`.
- `Map<K, V>` keeps its entries densely in insertion order, with an open-addressed index of `u32` values.
- `[T; N]` is an inline LLVM array.
- A closure is `{ ptr fn, ptr env, ptr drop }`. A `dyn` object is `{ ptr data, ptr vtable }`.

### Calls, traits and closures

`emit_call` tries these in order:

1. Special names such as `std.source.file`.
2. User functions. Arguments are evaluated left to right, the capability checks run, and then the call is made.
3. Runtime helpers, named `kelp_<name>`.
4. Container methods.

A method call through a `dyn` value loads the vtable from the second word and calls the slot with the data pointer (`DynCall`).
A closure call passes the environment pointer first (`emit_indirect_call`).

### Run-time checks

- A panic calls `kelp_panic` with the message and then `unreachable` .
- Bounds checks compare the index with the length as unsigned values .
- A shift amount that is not known to be in range is checked against the width.
- A narrowing conversion checks only the bounds that the source type cannot rule out.
- Integer arithmetic has no overflow check and carries no `nsw` or `nuw` flags, so it wraps.
- Integer division has no zero check in the generated code.
  The front end rejects a constant division by zero .

### Debug information

The object carries DWARF line information for each module.
A fault at run time therefore names a `.kp` file and line.
Each statement gets a location, and no variables are described.

## Optimisation levels

`OptLevel` has the values `-O0`, `-O1`, `-O2`, `-O3` and `-Os`.
The default is `-O2`.
The level selects the LLVM pass pipeline and the target machine's codegen level.
It is also the codegen level of the externs object, and `ld.lld` ignores it.
`-Oz` is refused.

## The retired C backend

The C backend was removed on 2026-10-10.
Its golden outputs remain in `kelpc/tests/golden/`.
The C-versus-LLVM differential test is gone with it.

No C text remains in the tree. The stdlib's extern bodies are Rust exports in `kelp-rt`, and the per-program object of step 7 is LLVM IR.
A few comments in `codegen_llvm.rs` still name the removed backend. They describe no behaviour.

## See also

- [Pipeline](/compiler/architecture)
- [Ownership and drops](/compiler/ownership)
- [Driver](/compiler/driver)
- [Runtime](/compiler/runtime)
- [Tests](/compiler/tests)
