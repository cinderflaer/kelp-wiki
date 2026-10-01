---
title: "Freestanding mode"
description: "A bare-metal build: no libc, no runtime preamble, a compiler-emitted `_start`, the entry and panic functions and a linker script named in `[target]`. LLVM-only. riscv64 and aarch64. The allocator hook reroutes `Box`, `List` and `Map`."
isPublished: true
tags: "language, freestanding, kernel"
---
A project opts into bare metal with a `[target]` section in `coral.toml`. A
project with no `[target]` section, or with `mode = "hosted"`, builds for the
host exactly as every project before this stage did; that is the whole
compatibility promise. The design is
[`plan/freestanding.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/freestanding.md).

There is no libc and no `kelp_rt.c` behind a freestanding image, so everything
that would reach either is a compile error rather than an undefined symbol the
linker reports. `kelpc check` enforces the same set `kelpc build` does, because
the check lives in the front end.

## The `[target]` section

```toml
[target]
mode = "freestanding"
triple = "riscv64-unknown-none-elf"
entry = "kmain"
linker_script = "kernel.ld"
panic = "kp_panic"          # optional
alloc = "kmalloc"           # optional, with dealloc
dealloc = "kfree"           # optional, with alloc
realloc = "krealloc"        # optional, needs the pair
```

| Key | Required | Meaning |
| --- | --- | --- |
| `mode` | yes | `"hosted"` or `"freestanding"` |
| `triple` | yes in freestanding | the LLVM triple the project targets |
| `entry` | yes in freestanding | a bare `fun` name in the entry module, with no parameters and no return |
| `linker_script` | yes in freestanding | a path relative to the directory holding `coral.toml` |
| `panic` | no | the bare name of a `fun(msg: str)` that never returns normally. Without it, the compiler generates a handler whose body loops forever |
| `alloc`, `dealloc` | no | the project's own allocator; see below |
| `realloc` | no | the growth fast path; needs `alloc`/`dealloc` |

`riscv64-unknown-none-elf` and `aarch64-unknown-none` are the two kernel 0
boots, and the two the compiler has a target machine and a `_start` stub for.
Any other triple is refused by name at the stub:

```text
error: kelpc has no freestanding '_start' stub for the triple 'x86_64-unknown-none': it has one for riscv64 and aarch64
```

An x86-64 image has to wait for its own entry stub, a 32-bit PVH/Multiboot one
that enters long mode first.

A freestanding project is **LLVM-only**. `KELPC_ORACLE=c` refuses with a message
naming the mode and the backend, because the C backend's runtime preamble is
libc:

```text
error: 'examples/kernel0' sets '[target] mode = "freestanding"', which only the llvm backend can build: the C backend's runtime preamble is libc (the KELPC_ORACLE switch cannot build a freestanding project)
```

`kelpc run` refuses one too: the artifact is a bare-metal ELF to be loaded by a
boot loader or an emulator, not a host process.

```text
error: 'examples/kernel0' is a freestanding project, whose artifact is a bare-metal ELF; 'kelpc run' does not run one
```

## What freestanding removes

Each is refused at the call site, the type use or the module import, and the
message names the construct.

- **Refused:** `print`/`print!` (the `printf` call), `assert` (the runtime's
  `kelp_assert`), a defined `main` (the hosted entry point and its
  `argc`/`argv` globals), `Ptr.alloc`/`Ptr.free` (the hosted `malloc`/`free`),
  passdowns (`pd`, whose initializers run through the generated `kelp_init_pds`
  that only the hosted entry point calls), `String`, `Bytes`, `View` and
  `Thread` (which always reach the hosted C runtime), `Box`, `List` and `Map`
  when no allocator pair is configured, and any `std/*` module except the pure
  ones below.

```text
error: 'print' is unavailable in a freestanding build: it writes through the hosted runtime's 'printf'
```

```text
error: 'Ptr#alloc' is unavailable in a freestanding build: it allocates through the hosted runtime's 'malloc'
```

```text
error: the binding 'xs' has type 'List', which needs an allocator in a freestanding build: set '[target] alloc' and '[target] dealloc' to the project's own functions
```

The list is a closure over reachability, not the language's surface: `print` is
refused as a call, `String` as a type wherever it appears (a local, a parameter,
a field, a return), and a `std/*` module as both. A shape not on the allowed
list is refused rather than lowered, so a program that compiles freestanding
cannot reference a symbol the link would miss.

## What freestanding keeps

- Every integer width, `bool`, `char`, `f32`/`f64`, `unit`; `str` as a borrowed
  literal in read-only data; user `datac` and `enum` values; arrays `[T; N]`;
  borrows `&T`/`&mut T`.
- `if`, `when`, loops, functions, and closures that capture nothing (a capturing
  literal owns a heap environment that only the runtime could free).
- `Atomic<T>` and its methods, plus the pure `std/atomic`, `std/option` and
  `std/result` modules.
- The five `std/str` operations the compiler lowers itself: `str.len`,
  `str.byte`, `str.eq`, `str.starts_with` and `str.ptr`. Every other `std/str`
  function is refused by name, and the rest of the module (and `std/mem`, which
  it imports) is dropped from the AST before inference, so its bodies and the
  type instances they would instantiate never exist.
- `Ptr<T>`, the compile-time `size_of`/`align_of`/`offset_of`, `unsafe`,
  `asm` and naked functions. `Ptr.alloc`/`Ptr.free` stay refused.
- `static`/`static mut` and `defer`.
- A user `extern fun` whose module has its own `[extern."<id>"]` section.
- A call to the builtin `panic(msg)`, and the arithmetic/bounds checks, which
  all call the project's `panic` handler (or the generated infinite loop).

`std/str` is the one module that is partly allowed, because a kernel that prints
anything has to walk text. Its raw primitives are emitted into the module as
byte loops marked `optnone`, so the target's own loop-idiom pass cannot rewrite
the NUL scan into a `strlen` call.

## The allocator hook

A freestanding project that wants the heap types names the functions that own
its memory:

```toml
[target]
mode = "freestanding"
# ... triple, entry, linker_script, panic ...
alloc = "kmalloc"
dealloc = "kfree"
realloc = "krealloc"      # optional
```

All three are bare names of `fun`s in the entry module, `extern`-free, with
fixed signatures:

```kelp
fun alloc(size: usize, align: usize).R: Ptr<u8>                                  // the null pointer on failure
fun dealloc(p: Ptr<u8>, size: usize, align: usize)
fun realloc(p: Ptr<u8>, old: usize, new: usize, align: usize).R: Ptr<u8>         // optional
```

A wrong signature is a compile error naming the expected one:

```text
error: the allocator function 'alloc' named by coral.toml's '[target]' has the wrong signature: it must be 'fun alloc(usize, usize).R: Ptr<u8>'
```

`alloc` and `dealloc` are required together; `realloc` needs the pair. With a
pair configured, `Box<T>`, `List<T>` and `Map<V>` are allowed whenever their
element types are allowed, and every allocation and free they make in the LLVM
output calls the project's functions instead of libc's `malloc`, `realloc` and
`free`. Without a `realloc`, growth is alloc + copy + dealloc. A failed
allocation (the project's `alloc` returns null) calls the project's panic
handler with `"out of memory"`, so it is a panic and never a null dereference.

`String`, `Bytes`, `View` and `Thread` stay refused either way, because their
operations reach `strlen`/`memcpy`/`realloc` in the hosted runtime.

`examples/kernel0-heap` is the idiom: a bump allocator over a `static mut`
arena, a `List<i32>` of 1..=10, and a counting wrapper that prints `balanced`
when every allocation reached a matching free.

## `section(...)`, the `_start` stub and the link

`section("<name>")` is an optional leading clause on a top-level `const` or
`fun`, in either order round `pub`. On a `fun` the backend sets the function's
section; on a `const` it must be a fixed-size array of integers, emitted as
read-only data in that section. On any other item, or on an `extern fun`, it is
refused. RISC-V calls `section` and `repr` "contextual words", like `unsafe`:
the word is an identifier unless the following `(` or `fun` makes it a marker.

The compiler emits a `_start` symbol as module-level assembly (LLVM `module asm`),
because loading `sp` from a linker-script symbol is not expressible in the
language yet. The stub is per-architecture, selected by the manifest's `triple`.
The riscv64 one loads `sp` from `__stack_top`, zeroes `[__bss_start, __bss_end)`
a word at a time, calls `kelp_kmain`, and loops on `wfi` if the entry returns;
the aarch64 one is the same shape with `ldr x0, =__stack_top`, `wfe` and `str
xzr, [x0], #8`. `sp` is loaded first, and nothing between it and the entry call
touches memory except the clear loop itself, so a kernel's first instruction
already has a stack and already has zeroed statics.

The two bounds are declared `.weak`: a linker script that does not assign them
still links, both resolve to 0, and the loop runs zero times. A script that does
assign them should put both around the same word-aligned range, with
`.bss.dirty`, `.sbss`, `.bss` and `COMMON` inside it. `.text.boot` is where a
script should place the stub first.

`kelpc build` in freestanding mode loads the target's backend by name, creates
the `TargetMachine` for the triple, writes the object, and links it with
`ld.lld -T <script> -o <out> --static <obj>`. A missing `ld.lld` is an error
naming it; `kelpc` never falls back to `cc`, which would link the hosted startup
files back in. There is no runtime object, no per-program C object and no `-lm`.

riscv64 gets the `generic-rv64` CPU, `+m,+a,+c` features and the **medium** code
model; aarch64 gets the `generic` CPU, no extra features and the **small** code
model, because LLVM refuses `medium` on AArch64. The relocation model is static
for both, and the module's triple and data layout are set from the machine.

### The compiler's `mem*` fallbacks

LLVM's own lowering of a large aggregate copy, a whole-array fill or a generated
clone calls `memcpy`, `memmove`, `memset`, `memcmp` or `bcmp`. The compiler
therefore defines all five in every freestanding object, as byte loops generated
as IR. Each is **weak** and marked `nobuiltin`, so an object the image links
beside it that defines any of them strongly wins, and the loop-idiom pass cannot
rewrite the loop inside one into a call to the library function of the same
name. A Kelp `fun` cannot define one, because a Kelp `fun`'s symbol is mangled.
A freestanding image that uses none of them still carries the five small loops.

The acceptance artifact is `tests/projects/freestanding_memcpy`: a 4 KiB `datac`
and a `[u8; 4096]` array copied whole, linked with zero undefined symbols, whose
`llvm-objdump -d` shows no self-call in any of the five bodies.

## A minimal project, built

The smallest thing the backend can emit an ELF for: an entry that loops, in
`.text.boot`, with an integer-array `const` in `.rodata.boot`.

```kelp
// src/main.kp
section(".rodata.boot") const BOOT_MAGIC: [u8; 4] = [75, 69, 76, 80]

section(".text.boot") fun kmain() {
    var i: u64 = 1
    while true {
        i = i * 3 + BOOT_MAGIC.get(i = 0).to_u64()
    }
}
```

```toml
# coral.toml
name = "freestandingmin"

[target]
mode = "freestanding"
triple = "riscv64-unknown-none-elf"
entry = "kmain"
linker_script = "kernel.ld"
```

```sh
kelpc build . -o kernel.elf
llvm-readelf -h kernel.elf      # Machine: RISC-V, Entry point address: 0x80000000
llvm-nm -u kernel.elf           # nothing: no undefined symbol
```

The five `mem*` definitions are visible in the image as weak symbols:

```text
00000000800000b8 W bcmp
000000008000004c W memcmp
0000000080000034 W memcpy
000000008000007e W memmove
000000008000006c W memset
0000000080000000 T _start
```

## See also

- [Kernel 0](/language/kernel): the examples that boot under QEMU, with the real
  serial output
- [Unsafe code and raw pointers](/language/unsafe): `Ptr<T>`, `repr(...)` and
  volatile access
- [Statics and `defer`](/language/statics-and-defer): the globals a kernel keeps
  and the cleanup it runs on the way out
- [Coral: the manifest](/tooling/coral#target-a-freestanding-build): the
  `[target]` section
