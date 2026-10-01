---
title: "Statics and `defer`"
description: "`static`/`static mut`/`pub static` with a constant initializer, `Atomic<T>` statics, and `section(...)`; `defer`, whose action runs last-in-first-out on every ordinary exit of its block. A panic does not run it, and `?` in the same block is refused."
isPublished: true
tags: "language, memory"
---
Two things a kernel needs before anything else runs: storage with a stable
address, and cleanup on the way out of a block. `static` is the first;
`defer` is the second. The designs are
[`plan/statics.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/statics.md)
and
[`plan/defer.md`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/defer.md).

## `static`

```kelp
static MAGIC: u32 = 0x2B1D
static mut CURSOR: usize = 0
pub static NAMES: [u8; 4] = [0x4B, 0x45, 0x4C, 0x50]
section(".data.boot") static mut BOOT: u32 = 1
```

`static NAME: T = INIT` is one object with a stable address for the whole
program. `static mut` is the mutable form. `pub` and the existing
`section("...")` clause apply to both, and the declaration sits in the canonical
order next to `const`: after `impl`, before `datac`/`enum`/`fun`.

### The allowed types

`T` is closed:

- a `Copy` scalar (`bool`, `char`, every integer, `f32`/`f64`),
- `[T; N]` where `T` is one of the allowed scalars,
- a `datac` whose fields are all of the allowed types, recursively,
- `Atomic<T>`.

A heap type (`String`, `Bytes`, `List`, `Box`, `Map`), a borrow, a `View`, a
function value, an `extern type` handle and a `Ptr<T>` are all refused by name.
Nothing that needs a drop can be a static, so a static never owes cleanup and
never joins the drop plan.

### The initializer

`INIT` must be a constant expression: a literal, an array literal (`[1, 2, 3]`)
or repeat (`[0; 4096]`), a `datac` constructor with constant arguments,
`Atomic.new(<const>)` (and the `AtomicI64.new(...)` alias), or another `const`.
Anything else is refused with "the initializer is not constant", rather than
being run at startup:

```text
error: the initializer is not constant: a 'i32' static is initialized with a literal, an array literal or repeat, a datac constructor with constant arguments, 'Atomic.new(<const>)', or another const
```

### Where a static lives

A static initialised to all zero goes to `.bss` (LLVM `zeroinitializer`, the
section default); any other value goes to `.data`; a `section("...")` clause
overrides both. An immutable static with a nonzero value is emitted `constant`
(read-only), except one that holds an `Atomic`, which is emitted mutable so its
methods can write through the shared borrow.

### Reading and writing one

- A read of a `static` is a load; the address is `&NAME`, and
  `Ptr.from_ref(&NAME)` / `Ptr.from_mut(NAME)` work on one.
- `static NAME` is read-only. Reading one and taking its address are legal
  everywhere (a shared borrow). Assigning one is refused.

```text
error: cannot assign to 'static X': it is not declared 'static mut'
```
- `static mut NAME` is mutable, and **every** read, write, field access and
  address-taking of it is `unsafe`: legal only inside `unsafe { ... }` or an
  `unsafe fun`, so only in a module `coral.toml` lists under `[unsafe] modules`.
  The check fires where the name is resolved, so a read, a write, a field, a
  method receiver and an address are all covered by the one gate.

```text
error: 'static mut C' is an unsafe operation: reading, writing or taking its address can only be done inside 'unsafe { ... }' or in a function declared 'unsafe fun'
```

- An `Atomic<T>` static is the safe shared mutable: `COUNTER.fetch_add(1,
  order = SeqCst)` needs no `unsafe`, because every `Atomic` operation takes a
  shared borrow. This is the shape a kernel's per-CPU counter or a shared flag
  wants without an audit entry.

```kelp
impl "std/atomic"

static MAGIC: u32 = 0x2B1D
static mut CURSOR: usize = 0
pub static NAMES: [u8; 4] = [0x4B, 0x45, 0x4C, 0x50]
static COUNT: AtomicI64 = Atomic.new(0)

fun main() {
    print(MAGIC)
    unsafe {
        CURSOR = CURSOR + 4
        print(CURSOR)
    }
    print(NAMES.get(i = 0))
    print(COUNT.fetch_add(value = 1, order = atomic.Ordering.SeqCst))
    print(COUNT.load(order = atomic.Ordering.SeqCst))
}
```

```text
11037
4
75
0
1
```

A static of the allowed types is accepted in a freestanding build by
construction, since a heap type cannot appear in one. `section(...)` places a
`const` (a fixed-size integer array) in a named read-only section, and a `fun` in
a named text section:

```kelp
section(".kelp.data") const STEPS: [i32; 4] = [1, 2, 3, 4]

section(".kelp.text") fun add(a: i32, b: i32).R: i32 = a + b

fun main() {
    print(add(STEPS.get(i = 0), 40))
}
```

```text
41
```

A `percpu static mut` is the per-CPU variant of the same storage class: the
compiler lays out `[target] cpus` copies of one value. See
[Per-CPU storage](/language/percpu).

### What the compiler does not check

The address of a static is stable, but `Ptr.from_mut(NAME)` still hands out a
raw pointer with no provenance, exactly as [`unsafe`](/language/unsafe)
describes, and `static mut` is the program's own promise that its `unsafe` code
sequences the access. Two threads that touch the same `static mut` without an
`Atomic` or a fence are a data race the compiler does not see.

## `defer`

```kelp
fun with_lock().R: bool {
    defer LOCK.store(value = false, order = atomic.Ordering.SeqCst)
    LOCK.store(value = true, order = atomic.Ordering.SeqCst)
    ...
    return true
}
```

`defer EXPR` is a statement. `EXPR` is one expression (a block counts: `defer
{ ... }`), and it is checked and emitted exactly as if it were written at every
exit of the block it is written in; the value of `EXPR` is discarded. `defer`
is a keyword, so no program that named a variable `defer` changes meaning.

### Semantics

- A deferred action runs when the **block** that contains the `defer` is left.
- Which actions run is *positional*: an action runs only if control reached its
  `defer` statement, so a `defer` written after an early `return` does not run
  on that path.
- Actions of one block run last-in-first-out; an inner block's actions run
  before the outer block's.
- Every ordinary exit is covered: falling off the end of the block, a `return`
  in the block, and a `return` nested in the block's inner blocks, `if`s and
  loops.
- The deferred code runs with the locals that were in scope at the `defer`
  statement, still alive and unmoved. A local moved out before the block exits
  and then named by the deferred code is the ordinary "use of moved value"
  error. A `defer` that names a local declared *after* it is refused, because
  that local is not in scope where the `defer` is written.
- A deferred action may not contain `return` (it has no caller to return to).
  `break` and `continue` are not Kelp statements at all, so there is nothing to
  lower at a loop exit.

```kelp
fun note(tag: &str) {
    defer print(tag)
    print("body")
    return
}

fun main() {
    defer print("first")
    defer print("second")
    print("start")
    note("in-note")
    defer {
        print("third-a")
        print("third-b")
    }
    print("end")
}
```

```text
start
body
in-note
end
third-a
third-b
second
first
```

`note`'s `defer` runs on its `return` (printing `in-note` before `main`'s
statements after the call), and `main`'s three run at the end of `main`, inner
block first, then last-in-first-out.

### A panic does not run a deferred action

A panic never returns, and the compiler's panic path is a call that ends the
process. A resource held by a `defer` at a panic leaks, exactly as every other
frame value does.

```kelp
fun boom() {
    defer print("cleanup")
    print("before panic")
    panic("fired")
}

fun main() {
    boom()
    print("never")
}
```

Standard output is `before panic` and the panic message goes to standard error;
the run exits with status 1 and never prints `cleanup`:

```text
before panic
```

### `defer` and `?` cannot share a block

The `?` operator leaves the enclosing *function*, which would skip the deferred
actions of every block between it and the function body. That is refused by name
rather than silently skipped.

```text
error: defer with an early `?` exit is not supported yet
  note: this `?` leaves the function, which would skip the deferred action
```

### How it is implemented

`defer` is a small pass that runs on the parsed program before name resolution
and type checking. Every deferred action is re-materialised at each exit as an
ordinary expression in an ordinary block, so inference, move checking, drop
placement and both code generators apply unchanged. A block in *value* position
(`val v = { defer d(); x }`) is lowered through a synthesized binding, which is
the nested-block form the language already has.

## See also

- [User `Drop`](/language/drop): the destructor a value runs at every drop
  point
- [Per-CPU storage](/language/percpu): one copy of a static per CPU
- [Unsafe code and raw pointers](/language/unsafe): the `[unsafe]` gate
  `static mut` shares
- [Freestanding mode](/language/freestanding): statics and `defer` in a
  bare-metal image
- [Concurrency in v1](/language/concurrency): `Atomic<T>`, the ordering and the
  fence
