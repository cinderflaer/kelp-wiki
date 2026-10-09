---
title: "Freestanding mode"
description: "A bare-metal build: no libc, no runtime preamble, a compiler-emitted `_start`, the entry and both panic shapes, a linker script named in `[target]`, and the admitted `std` subset. LLVM-only. riscv64, aarch64 and x86-64."
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
| `panic` | no | the bare name of the handler every compiler-inserted check calls. Two shapes: `fun(msg: str)` and the location-carrying `fun(msg: str, file: str, line: u32)`; any other shape is a compile error naming both. Without it, the compiler generates a handler whose body loops forever |
| `alloc`, `dealloc` | no | the project's own allocator; see below |
| `realloc` | no | the growth fast path; needs `alloc`/`dealloc` |

`riscv64-unknown-none-elf`, `aarch64-unknown-none` and `x86_64-unknown-none`
(the `-elf` spelling too) are the three kernel 0 boots, and the three the
compiler has a target machine, a `_start` stub and a wait instruction for. Any
other triple is refused by name before any code is emitted:

```text
error: kelpc has no code generator to load for the freestanding triple 'mips-unknown-none'
```

A triple whose backend does load but whose stub or wait instruction is missing
is refused the same way by name (for example the 32-bit `i686-unknown-none`,
which loads the X86 backend but has neither an x86-64 `_start` nor an x86-64
wait instruction).

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
  that only the hosted entry point calls), `Thread` (which always reaches the
  hosted C runtime), `Box`, `List`, `Map`, `String` and `Bytes` when no
  allocator pair is configured, and any `std/*` module except the admitted ones
  below.

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
- `Atomic<T>` and its methods, plus the admitted standard modules below:
the pure `std/atomic`, `std/arena`, `std/irq` and `std/frame`, `std/option`'s
and `std/result`'s value helpers, `std/math`'s integer
`abs`/`min`/`max`/`clamp`, and, with the `[target] alloc`/`dealloc` pair
configured, `std/list`, `std/regex` and the `std/option`/`std/result` callback
combinators.
- The five `std/str` operations the compiler lowers itself: `str.len`,
  `str.byte`, `str.eq`, `str.starts_with` and `str.ptr`. With an allocator
  configured, the three builders `str.concat`, `str.from_u64` and `str.from_i64`
  are kept too. Every other `std/str` function is refused by name, and the rest
  of the module (and `std/mem`, which it imports) is dropped from the AST before
  inference, so its bodies and the type instances they would instantiate never
  exist.
- `View`, the borrowed `{ptr, len}` pair with no storage of its own: all five of
  its operations (`len`, `is_empty`, `get`, `slice`, `eq`) are lowered into the
  module as byte loops. `View.to_string` copies into an owned `String`, so it is
  kept only with the `[target] alloc`/`dealloc` pair.
- A `datac` or `enum` with a `String` field. The derived key equality the
  compiler emits for a keyable type is now a length-aware byte loop in a
  freestanding image too, the body hosted code gets from `kelp_map_key_eq`, so
  such a type compares and hashes with no libc behind it. `examples/kernel0-eq`
  is the proof: it prints a `String`-field equality, a `Map` lookup through the
  derived pair, a `Bytes`-field equality (a declared `eq` that walks the bytes),
  a `View` slice and a `std/regex` match over the UART on riscv64 and x86-64.
- `Ptr<T>`, the compile-time `size_of`/`align_of`/`offset_of`, `unsafe`,
  `asm` and naked functions. `Ptr.alloc`/`Ptr.free` stay refused; `Ptr.try_alloc`
  is allowed by the same `[target] alloc`/`dealloc` pair `String` and `Bytes`
  need.
- `static`/`static mut` and `defer`.
- A user `extern fun` whose module has its own `[extern."<id>"]` section.
- A call to the builtin `panic(msg)`, and the bounds checks, which all route
  through the compiler's panic entry to the project's `panic` handler (or the
  generated infinite loop); see [Panic semantics](#panic-semantics).

`std/str` is the one module that is partly allowed, because a kernel that prints
anything has to walk text. Its raw primitives are emitted into the module as
byte loops marked `optnone`, so the target's own loop-idiom pass cannot rewrite
the NUL scan into a `strlen` call.

## The freestanding standard subset

Which shipped `std/*` modules a freestanding program may use is one table in
`freestanding.rs` (`std_admission`), one row per module, and the call-site check
and the body-pruning pass are driven by the same row. The row is one of five
verdicts: **Pure** (every item callable, no body reaches libc), **Allocator**
(callable once `[target] alloc`/`dealloc` are configured), **Subset** (only the
named items are callable; the rest are refused by name at the call and pruned),
**Present** (the module may be in the program but nothing in it is callable),
and **Hosted** (nothing of it may be in a freestanding program). The table is
checked against `stdlib::shipped()` by a unit test, so a new shipped module
fails the build rather than defaulting to allowed.

| Module | Verdict | What is admitted |
| --- | --- | --- |
| `std/atomic` | Pure | every item; `Ordering` is a plain `enum` |
| `std/option` | Subset | `is_some`, `is_none`, `unwrap_or`, `unwrap`, `expect`; with `[target] alloc`/`dealloc`, `map`, `and_then`, `or_else`, `each` |
| `std/result` | Subset | the value helpers as-is; with the allocator pair, `map`, `map_err`, `and_then`, `or_else`, `each` |
| `std/arena` | Pure | every item; the region is the caller's |
| `std/convert`, `std/ops` | Pure | every item; they are trait declarations (`From`, `Into`, `Add`, `Sub`, `Mul`, `Div`, `Rem`, `Neg`, `Ord`), so the `?` conversion and an operator on a user type lower to ordinary calls |
| `std/iter` | Subset | `Iterator`, `Range`, `range`, `range_step`, `count`, `sum_i64`; with the allocator pair, `collect_list` |
| `std/irq` | Pure | `claim` and `Line.number` (under an `irq` grant) |
| `std/frame` | Pure | `claim`, `Frame.addr` and `Frame.offset` (under a `frames` grant) |
| `std/str` | Subset | `len`, `byte`, `eq`, `starts_with`, `ptr`; with the allocator pair, `concat`, `from_u64`, `from_i64`; every other function refused by name |
| `std/math` | Subset | the integer `abs`, `min`, `max` and `clamp`; the sixteen libm externs, the `f64` overloads of the four arithmetic ones and `sign` are refused by name |
| `std/list` | Allocator | every item, once `[target] alloc`/`dealloc` are configured |
| `std/regex` | Allocator | every item, once `[target] alloc`/`dealloc` are configured; the parser, the program and the Pike VM are `List` and integer code, and the derived `String` equality plus the `View` operations are lowered into the module |
| `std/mem` | Present | nothing is callable; `std/str` imports it, and the pruning pass drops its one extern |
| `std/rt` | Present | nothing is callable; the resolver injects it for a gated module, and its bodies are pruned |
| `std/encoding`, `std/path`, `std/io`, `std/fs`, `std/net`, `std/tls`, `std/http`, `std/ws`, `std/process`, `std/env`, `std/time`, `std/tz`, `std/rand`, `std/thread`, `std/sync`, `std/fmt` | Hosted | refused by name; they reach libc, the allocator or the hosted runtime (`std/fmt`'s `hex_raw`/`bytes_raw` are `snprintf`-backed, `std/tz` reads a TZif file and asks the environment for `$TZDIR`, and `std/sync`'s `Mutex<T>`, `RwLock<T>` and `Condvar` are pthread objects) |

A module whose row is `Allocator` and a program with no allocator pair is
refused with the two manifest keys named, not left to the linker (`std/list`
and `std/regex` are the two). A whole-module
refusal says "needs a hosted runtime" and then names the modules a freestanding
project may implement, derived from the same table so it cannot drift:
`std/arena, std/atomic, std/convert, std/frame, std/irq, std/iter, std/list,
std/math, std/ops, std/option, std/regex, std/result, std/str`.

```text
error: the module 'std/time' is unavailable in a freestanding build: it needs a hosted runtime (libc or the 'kelp_rt' helpers); the std modules a freestanding project may implement are std/arena, std/atomic, std/convert, std/frame, std/irq, std/iter, std/list, std/math, std/ops, std/option, std/regex, std/result, std/str
```

A refused item inside an admitted module is refused at the call instead, the
same way, so nothing reaches `ld.lld`:

```text
error: the call to 'std.math.sqrt' is unavailable in a freestanding build: it needs the hosted runtime, which 'std/math' reaches for everything but abs, clamp, max, min
```

Admitting `std/math` without a per-item set would not work: every concrete body
in an admitted module is emitted, so an uncalled `sqrt` left `undefined symbol:
sqrt` at the link, and an admitted `sign` left `__ltdf2`, the soft-float compare
a riscv64 image has no library for. The integer overloads are one-line Kelp
comparisons, so the subset separates by name and by parameter type (`prune`
drops the `f64` overloads). Nothing new is added: what is admitted is what the
shipped modules already declare, and `std/bits` is not shipped on this branch.

## Panic semantics

There is no process to kill and no stderr to print to, so a check that fires
has to say what it caught and where. `[target] panic` names the handler; two
shapes are accepted, and any other shape is a compile error naming both:

```kelp
fun kp_panic(msg: str)                                   // the original form
fun kp_panic(msg: str, file: str, line: u32)             // with the location
```

```text
error: the freestanding panic handler 'kp_panic' must be a 'fun(msg: str)' or a 'fun(msg: str, file: str, line: u32)', with no return, which are the shapes the compiler's checks call
```

The three-argument form also receives the source *file name* (`main.kp`, the
last component of the module's path, the same spelling a diagnostic's `-->`
ends with) and the 1-based *line* of the statement the check was inserted into.
That is the same per-statement span the hosted backends' line tables and
`#line` directives are built from, so a freestanding panic names the same line a
hosted one would. The line is the statement the check belongs to, not the exact
sub-expression: one `locate` per statement is the granularity both backends
carry.

A check never calls the handler directly. Every check calls one compiler-emitted
entry, `kelp_panic_entry(msg, file, line)`, which:

1. atomically exchanges a flag (`kelp_panic_active`, an `i32` in `.bss`) from 0
   to 1,
2. calls the handler when the old value was 0, because this is the first panic,
   with one or three arguments by the handler's own shape, and
3. calls `kelp_double_panic()` when the old value was 1, because a panic is
   already in progress, and halts if that returns.

`kelp_double_panic` is emitted as a **weak** definition whose body loops on the
target's wait-for-interrupt instruction (`wfi` on riscv64, `wfe` on aarch64),
the same way the `mem*` fallbacks below are weak. A project that supplies a
strong definition in an object linked beside the image wins at link time, so a
double panic can print instead of wedging; the weak halt is always defined, so
the image has no undefined symbol. The exchange is atomic rather than a load and
a store so two harts that panic at once cannot both think they are first.

The location of a check inside a *generated* body (`Array.get`'s bounds check,
`List.get`, `Bytes.get`, the allocator's out-of-memory path) cannot be a
per-call-site constant, because that body is emitted once per type and shared by
every call site. The compiler keeps two module globals, `kelp_panic_file` (a
`ptr` to the current file-name string) and `kelp_panic_line` (an `i32`), stores
the current statement's file and line into them before every statement of a
`.kp` function, and the check loads them. The caller's statement is the last
thing stored, so a panic inside the generated body names the user's line. A
check emitted inline in the user's own function (`to_u8`'s range check,
`panic(msg)`, `cpu_index()`) reads the same two globals. The cost is two stores
per statement, and only a freestanding build pays it: the globals are declared
and written only when `mode = "freestanding"`.

Every compiler-inserted check in a freestanding build calls the entry with the
message below.

| Check | Message | Where emitted |
| --- | --- | --- |
| `Array.get`/`get_const`/`set` index | `Array.get: index out of bounds` | generated body |
| `List.get`/`get_const` index | `List.get: index out of bounds` | generated body |
| `List.pop` on an empty list | `List.pop: the list is empty` | generated body |
| `List.insert` index | `List.insert: index out of bounds` | generated body |
| `List.remove` index | `List.remove: index out of bounds` | generated body |
| `List.slice` range | `List.slice: range out of bounds` | generated body |
| `Box.get` on an empty box | `Box.get: the box is empty` | generated body |
| `Box.take` on an empty box | `Box.take: the box is empty` | generated body |
| `Map.get` missing key | `Map.get: key not found` | generated body |
| `Map.remove` missing key | `Map.remove: key not found` | generated body |
| `Bytes.get`/`set` index | `Bytes.get: index out of bounds` | generated body |
| `Bytes.read_*`/`write_*` offset | `Bytes.read_u32_le: offset out of bounds` (per accessor) | inline |
| `View.get` index | `View.get: index out of bounds` | generated body |
| `str.byte` index | `str.byte: index out of bounds` | generated body |
| narrow conversion | `i32.to_u8: value out of range` (per call) | inline |
| allocator failure | `out of memory` | generated body |
| `panic(msg)` | the program's own message | inline |
| `std/option.unwrap`/`expect` | `Option.unwrap: value is None` (its own `panic`) | inline |
| `std/arena.alloc` bad alignment | its own `panic` | inline |
| `cpu_index()` out of range (debug) | `cpu index out of range` | inline |

Two things a reader might expect to find in that table are deliberately not
checks in this language:

- **Integer overflow wraps.** There is no `nsw`/`nuw` on any arithmetic
  instruction and no runtime overflow check.
- **Division by zero is unchecked.** `sdiv`/`udiv` by zero is UB in LLVM
  exactly as it is in C; the only guard is constant folding in the front end.

With no `[target] panic`, the compiler still emits the entry and the weak
`kelp_double_panic`, and the entry's first-panic branch calls a generated
infinite-loop handler. A check still stops the machine; it just prints nothing,
which is the pre-stage behaviour.

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
fun alloc(size: usize, align: usize).return: Ptr<u8>                                  // the null pointer on failure
fun dealloc(p: Ptr<u8>, size: usize, align: usize)
fun realloc(p: Ptr<u8>, old: usize, new: usize, align: usize).return: Ptr<u8>         // optional
```

A wrong signature is a compile error naming the expected one:

```text
error: the allocator function 'alloc' named by coral.toml's '[target]' has the wrong signature: it must be 'fun alloc(usize, usize).return: Ptr<u8>'
```

`alloc` and `dealloc` are required together; `realloc` needs the pair. With a
pair configured, `Box<T>`, `List<T>` and `Map<V>` are allowed whenever their
element types are allowed, and every allocation and free they make in the LLVM
output calls the project's functions instead of libc's `malloc`, `realloc` and
`free`. Without a `realloc`, growth is alloc + copy + dealloc. A failed
allocation (the project's `alloc` returns null) calls the project's panic
handler with `"out of memory"`, so it is a panic and never a null dereference.

`Thread` stays refused either way, because its operations reach the hosted
runtime. `View` is admitted: its accessors are byte loops lowered into the
module, and `View.to_string` is listed with the allocator-using operations, so
it is callable only with `[target] alloc`/`dealloc`.

### `String` and `Bytes` on the project allocator

With `alloc`/`dealloc` configured, `String` and `Bytes` are legal types wherever
an allowed type is: a local, a field, a parameter, a return and a container
element. Without the pair they stay refused by name, the same as `Box`/`List`/
`Map`:

```text
error: the binding 's' has type 'String', which is unavailable in a freestanding build without an allocator: set '[target] alloc' and '[target] dealloc' to the project's own functions
```

Both types are lowered as byte loops over the buffer the project's allocator
returned, so no `strlen`, `memcpy` or `realloc` symbol is emitted and
`llvm-nm -u` stays clean. `String` keeps `empty`, `from_str`, `len`, `is_empty`,
`as_str`, `clone`, `push`, `push_str`, `reserve`, `with_capacity` and `clear`;
`Bytes` keeps `empty`, `from_str`, `len`, `is_empty`, `get`, `set`, `push`,
`clone`, `reserve` and `clear`; and `std/str` keeps `concat`, `from_u64` and
`from_i64` beside the five raw operations, which is how a kernel builds text
(`str.concat` over `str.from_u64`, because `"${}"` is a print-only construct and
`print` needs `printf`). Every other method is refused at the call, by name,
with "needs the hosted runtime": `str.split`, `str.join`, `str.repeat`,
`str.to_upper`, `str.char_count`, the parsers, `str.from_f64`, `Bytes.append`,
`Bytes.as_str`'s UTF-8 validation, and every `String`/`Bytes` method not in
those lists. The refusal is in the front end, so `kelpc check` and `kelpc build`
give the same error and nothing reaches the linker.

Every allocation goes through the project's `alloc(size, align)` with `align =
1`, and every free through `dealloc(ptr, size, 1)` with `size = cap + 1`, the
exact byte count the matching allocation asked for (an empty buffer allocates
one byte so the terminating NUL always has a slot). Growth doubles the capacity
through the manifest's `realloc` when it names one, else alloc + copy + dealloc,
and a null from any of the three reaches the project's `[target] panic` handler
with `"out of memory"`, so a failed allocation is a panic and never a null
dereference. `Ptr.try_alloc` is the deliberate exception: the same pair admits
it, and it answers the null `Ptr<T>` instead of panicking (see
[Unsafe code and raw pointers](/language/unsafe)).

`examples/kernel0-string` is the idiom: the heap example's bump allocator with
the optional `realloc` named, `str.concat` and `str.from_u64` for text, a
`String` grown with `push_str`, and a `Bytes` grown through several doublings:

```text
s: hello kelp!
n: 12345
b: 300
balanced
```

`examples/kernel0-heap` is the same idiom for `List<i32>`: a bump allocator over
a `static mut` arena, a `List<i32>` of 1..=10, and a counting wrapper that
prints `balanced` when every allocation reached a matching free.

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
xzr, [x0], #8`. The x86-64 one cannot start in the entry's own mode: QEMU's x86
`-kernel` enters it through SeaBIOS' Xen PVH loader in 32-bit protected mode
with paging off, so the stub has to build long mode first (see [The x86-64
target](#the-x86-64-target)). `sp` is loaded first in the two word-at-a-time
stubs, and nothing between it and the entry call touches memory except the clear
loop itself, so a kernel's first instruction already has a stack and already has
zeroed statics.

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
model, because LLVM refuses `medium` on AArch64; x86-64 gets the `x86-64` CPU,
no extra features, the **static** relocation model and the **small** code model,
which is what links an image placed at 1 MiB (`kernel` assumes code in the top
2 GiB of the address space, and LLVM's x86-64 default, `medium`, is larger than
a 1 MiB image needs while `small` reaches code and data in the low 2 GiB with
the shortest addressing). The relocation model is static for all three, and the
module's triple and data layout are set from the machine. Every emitted function
is marked `noredzone` on x86-64: the System V ABI's 128-byte red zone below
`rsp` is clobbered by any interrupt, and a kernel that is about to take one must
not keep a live value there. SSE is not disabled; the stub enables it before the
entry call, so the compiler's `memcpy` and float lowering is safe.

### The x86-64 target

`[target] triple = "x86_64-unknown-none"` (the `-elf` spelling too) is the
third ISA. QEMU's x86 `-kernel` has no loader that starts an
ELF64 image in long mode the way its riscv64 and aarch64 `virt` machines do.
Instead SeaBIOS scans the image's `PT_NOTE` program headers for the
`XEN_ELFNOTE_PHYS32_ENTRY` note (type 18, owner `Xen`), loads the ELF's
segments, and jumps to the 32-bit physical address the note names, **in 32-bit
protected mode with paging off**. Before any Kelp code can run, the stub has to
reach long mode itself, which is bootstrapping rather than language work.

The compiler emits the x86-64 `_start` as module-level assembly, with one
section for the note, one for the 32-bit and 64-bit code, and one NOBITS section
for the boot page tables:

1. `.note.Xen` holds the note whose 4-byte description is the address of
   `_start`, in a `PT_NOTE` program header, which is where SeaBIOS looks.
2. `.code32`: load a three-entry GDT (null, a 64-bit code segment at selector
   `0x08`, data at `0x10`), zero the three boot page-table pages in
   `.boot_pt`, fill PML4[0] with the PDPT, PDPT[0] with one PD, and the PD with
   512 `2 MiB` present+rw+ps entries that identity-map the first 1 GiB, set
   `CR4.PAE`, set `EFER.LME` through `rdmsr`/`wrmsr`, load `CR3`, and set
   `CR0.PG|CR0.PE`.
3. A far jump (selector `0x08`) into `.code64` turns on `EFER.LMA`. The 64-bit
   half reloads the data segment registers, loads `rsp` from `__stack_top`,
   and zeroes `[__bss_start, __bss_end)` a word at a time. The tables live in
   `.boot_pt`, outside the clear range, so the clear never erases the tables it
   runs under even though paging is on.
4. It enables SSE (`CR0.EM` clear, `CR0.MP` set, `CR4.OSFXSR` and
   `CR4.OSXMMEXCPT` set), sets `MXCSR` to its reset value, and calls the entry
   `fun` (`kelp_kmain`). If the entry returns, it spins on `hlt`.

`__bss_start` and `__bss_end` are `.weak` exactly as the other two stubs
declare them, and the double-panic halt is `hlt` for this triple.

`examples/kernel0-x86_64` is the COM1 (port `0x3F8`) driver: poll the Line
Status Register at `0x3FD` for bit 5 (THR empty) through `in`, then write the
Transmit Holding Register at `0x3F8` through `out`, both inline `asm` in the
`uart` module the `[unsafe]` list names. Port I/O is not memory-mapped, so the
manifest needs no `mmio` grant: `in`/`out` name a port number, not a
`Ptr.from_addr`. `kmain` prints its greeting and halts:

```sh
examples/kernel0-x86_64/run.sh
```

```text
run.sh: booted .../examples/kernel0-x86_64 and the UART printed:
hello from kelp (x86_64)
```

SeaBIOS prints its own banner (and iPXE's prompt) on the same serial line before
the greeting; `run.sh` asserts the greeting line whole, as it does for every
example, and the greeting's leading `\n` separates it from the banner's
newline-less `Booting from ROM..` line.

`examples/kernel0-x86_64-lmode` is the long-mode proof. Its `kmain` reads `CR0`,
`CR4` and `EFER` through `asm`, prints `long mode on` only when `EFER.LMA`,
`CR0.PG` and `CR4.PAE` are all set, then loads a null IDT and executes `ud2`.
With no IDT the `#UD` is a triple fault, so the machine resets; the boot test
runs QEMU with `-no-reboot` and asserts the two lines came out first:

```sh
examples/kernel0-x86_64-lmode/run.sh
```

```text
run.sh: booted .../examples/kernel0-x86_64-lmode and the UART printed:
hello from kelp (x86_64)
long mode on
```

What is not there: the APIC (local and I/O), SMP and ACPI, a TSS or an IST
stack, `syscall`/`sysret` and x86 user mode. An IDT with four CPU exception
gates and the PIC+PIT timer does ship, `examples/kernel0-x86_64-idt`
([Kernel 0](/language/kernel#x86-64-interrupts-the-idt-the-exceptions-and-the-timer)),
so what a kernel still needs on x86-64 is the local and I/O APIC and ACPI
enumeration. The `interrupt` and calling-convention attributes are still open. `cpu_index()` has no x86-64 lowering yet, so a `percpu` static is
refused by name for this triple, and there is no second x86-64 boot path (a
Multiboot 1 header): SeaBIOS' PVH support accepts the ELF64 image on this
machine's QEMU, so the fallback is not carried.

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
