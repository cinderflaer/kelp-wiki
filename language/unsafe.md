---
title: "Unsafe code and raw pointers"
description: "`unsafe` blocks and `unsafe fun` are the only way to dereference a `Ptr<T>`. A module may contain either only if coral.toml lists it under `[unsafe] modules`. Covers volatile access, `repr(...)`, layout queries and byte-order reads."
isPublished: true
tags: "language, unsafe, memory"
---
A raw pointer is a machine address, and the language cannot check what is at
one. `unsafe` is how a program says it will do that checking itself. It is
opt-in twice: a module may contain `unsafe` only if `coral.toml` lists that
module under `[unsafe] modules`, and the program author has to write the clause.
The design is [`plan/unsafe-and-pointers.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/unsafe-and-pointers.md),
and the catalogue of behaviour it does not check is
[`plan/kernel-ub-notes.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/kernel-ub-notes.md).

## The `[unsafe] modules` gate

A module is the path it is imported under, exactly as an `[extern."<module id>"]`
section names one: `"uart"` for `src/uart.kp`, and `"main"` for the entry module
`src/main.kp`. Only the listed modules may contain an `unsafe` block, an
`unsafe fun`, a `static mut` access or an `asm`. The list is short by design:
it is the set of modules allowed to leave the checked language, and a dependency
cannot grant itself the power.

```toml
# myproject/coral.toml
name = "myproject"
entry = "src/main.kp"

[unsafe]
modules = ["main", "uart"]
```

A project with no `[unsafe]` section behaves exactly as before: no module may
contain `unsafe`, and no `Ptr` operation is reachable at all. Naming a module
that is not listed is a compile error at the construct:

```text
error: module 'main' is not listed in coral.toml [unsafe] modules
```

An `unsafe` block or an `unsafe fun` counts as the module containing it, and
`kelpc check` enforces the rule exactly as `kelpc build` does. The audit also
reads the **default methods of a trait**, so an `unsafe` block in one is refused
in an unlisted module like any other.

## `unsafe` blocks and `unsafe fun`

`unsafe` is a contextual word, not a keyword: it introduces a block only when a
`{` follows, so a variable may still be called `unsafe`. The block is an
expression and a statement, so it can carry a value.

```kelp
fun main() {
    var x: i32 = 7
    val px: Ptr<i32> = Ptr.from_ref(&x)
    print(px.is_null())
    unsafe {
        px.write(42)
        print(px.read())
    }
    print(x)
}
```

```text
false
42
42
```

`unsafe fun name(...)` declares a function that only unsafe context may call.
Its body is itself an unsafe context, so it needs no block of its own.

```kelp
unsafe fun store(p: Ptr<i32>, v: i32) {
    p.write(v)
}

fun main() {
    unsafe {
        val cell: Ptr<i32> = Ptr.alloc<i32>(1)
        store(cell, 5)
        print(cell.read())
        cell.free()
    }
}
```

```text
5
```

Calling an `unsafe fun` outside unsafe, or writing `unsafe` in a module the
manifest did not list, is an error that names the operation or the module.

## `Ptr<T>`: the raw pointer

`Ptr<T>` is a builtin generic type, threaded exactly as `Atomic<T>` is. It is
`Copy`, owns nothing, needs no drop, carries no borrow tracking, and may be null.
The element `T` is any type with a C/LLVM layout: a scalar, `bool`, `char`, a
`datac`/`enum`, a fixed-size array, an `extern type` handle, or another `Ptr`.
`str`, `String`, `Bytes`, `List`, `Box`, `Map`, `View`, a borrow, a closure, a
function value and `Atomic<T>` are refused by name, because none of them is one
machine-level value:

```text
error: 'String' is an owned heap value, which is not one machine-level value a raw pointer can address
```

### Operations legal anywhere

| Operation | Returns | Notes |
| --- | --- | --- |
| `Ptr.null()` | `Ptr<T>` | the null pointer; write the element type at the binding or the call |
| `Ptr.from_addr(a)` | `Ptr<T>` | an address as an integer; the same typing note as `null` |
| `Ptr.from_ref(&x)` | `Ptr<T>` | a `val`'s address |
| `Ptr.from_mut(x)` | `Ptr<T>` | a `var`'s address |
| `Ptr.from_fn(f)` | `Ptr<u8>` | a declared `fun` or a non-capturing `fun` literal's address |
| `p.addr()` | `usize` | the address as an integer |
| `p.is_null()` | `bool` | |
| `p.offset(n)` | `Ptr<T>` | steps `n` elements, no bounds check |
| `p.byte_offset(n)` | `Ptr<T>` | steps `n` bytes, no bounds check |
| `p.cast<U>()` | `Ptr<U>` | the same address, another element type |
| `p == q`, `p != q` | `bool` | between two pointers of one type |

`offset` and `byte_offset` take an `isize`. Neither checks anything, which is
the point of a raw pointer. The typing of `null`/`from_addr` has no expression
to infer `T` from, so the compiler asks for it by name:

```text
error: cannot tell which type 'Ptr.from_addr' points at: write it in the call
('Ptr.from_addr<i32>(...)' where the operation takes a type argument) or on the
binding ('val p: Ptr<i32> = Ptr.null()')
```

### Operations that need `unsafe`

| Operation | Notes |
| --- | --- |
| `p.read()` | requires a `Copy` element, so a read cannot double-own a `String` |
| `p.write(v)` | |
| `p.read_volatile()` | never merged, reordered or elided |
| `p.write_volatile(v)` | never merged, reordered or elided |
| `p.read_unaligned()` | a `Copy` element at any alignment |
| `p.write_unaligned(v)` | a store at any alignment |
| `Ptr.alloc<T>(count)` | hosted `malloc`; unavailable in a freestanding build |
| `Ptr.try_alloc<T>(count)` | the same allocation without the panic: the null `Ptr<T>` on failure, the byte count checked for wrap on both backends; freestanding it needs an `[target] alloc`/`dealloc` pair |
| `p.free()` | hosted `free`; unavailable in a freestanding build |

```kelp
fun main() {
    unsafe {
        val base: Ptr<i32> = Ptr.alloc<i32>(3)
        base.offset(0).write(10)
        base.offset(1).write(20)
        base.offset(2).write(30)

        var sum: i32 = 0
        var i: isize = 0
        while i < 3 {
            sum = sum + base.offset(i).read()
            i = i + 1
        }
        print(sum)

        base.offset(0).write_volatile(99)
        print(base.offset(0).read_volatile())

        val raw: Ptr<u8> = base.cast<u8>()
        print(raw.read())

        base.free()
    }
}
```

```text
60
99
99
```

### Fallible allocation: `Ptr.try_alloc`

`Ptr.try_alloc<T>(count)` is `Ptr.alloc<T>` minus the panic. It is unsafe like
`alloc`, takes the same element set and makes the same alignment promise
("aligned for `T`"), but a failed allocation is the null `Ptr<T>` rather than a
call to the panic handler, so the null check `alloc` used to make for the
program is the program's own:

```kelp
fun main() {
    val max: usize = ~0
    unsafe {
        val p: Ptr<i32> = Ptr.try_alloc<i32>(4)
        print(p.is_null())
        p.write(42)
        print(p.read())
        p.free()

        val huge: Ptr<u64> = Ptr.try_alloc<u64>(max / 2)
        print(huge.is_null())

        val small: Ptr<u8> = Ptr.try_alloc<u8>(8)
        print(small.is_null())
        small.free()
    }
}
```

```text
false
42
true
false
```

Hosted it is libc's `malloc` on both backends. Freestanding it is the project's
own `[target] alloc`, admitted only when the manifest names `alloc`/`dealloc`;
without the pair the refusal is the same one `List` gets and names both keys:

```text
error: 'Ptr#try_alloc' is unavailable in a freestanding build: it needs an allocator: set '[target] alloc' and '[target] dealloc' to the project's own functions
```

On both backends the byte count `count * size_of::<T>()` is checked for wrap
before the call, so a request whose product would overflow `usize` answers the
null pointer instead of asking the allocator for a small block. That is the one
place `try_alloc` is deliberately stricter than `Ptr.alloc`, whose product can
still wrap. [`std/arena`](/stdlib/arena) is the other allocation tool a kernel
reaches for: a bump region the caller owns, no allocator and no libc.

### Volatile access

A volatile access is emitted as one: the C backend writes a `volatile`-qualified
access and the LLVM backend sets the instruction's volatile flag
(`LLVMSetVolatile`). The compiler never merges two volatile accesses, never
reorders one against another, and never elides one. That is what a device
register needs, and it is the whole promise: volatile says nothing about the
order of a volatile access against ordinary memory, and nothing about what the
address points at.

### The pointer does not carry the borrow

`Ptr.from_ref(&x)` and `Ptr.from_mut(x)` take a place's address, but the
resulting pointer does **not** extend the borrow. The borrow checker sees the
borrow the call takes and no more. Using the pointer after the place is gone, or
writing through it at all, is the caller's responsibility, which is exactly what
`unsafe` is for.

## Layout control: `repr(...)`

A `datac` may carry one clause before it. One clause per declaration; a second
one is a parse error.

| Clause | Meaning |
| --- | --- |
| `repr(c)` | declaration order, the C alignment and padding rules. This is also what a declaration with no clause already is; the point of the spelling is that it is now a guarantee rather than an accident |
| `repr(packed)` | every field at alignment 1, no padding anywhere, the whole type's alignment 1 |
| `repr(align(N))` | the C field layout with the type's own alignment raised to `N`, a power of two literal. The size rounds up to a multiple of `N`, and a type that embeds it places it at an `N`-aligned offset |

Both backends write the same layout byte for byte, and the C compiler is the
judge: `tests/projects/ffi_layout` builds a `repr(packed)` `datac` in Kelp, passes
its address through a user `extern fun` to a project-local C helper, and prints
C's `sizeof`/`_Alignof`/`offsetof` beside Kelp's own queries.

`repr(packed)` and `repr(align(N))` are refused **on an enum**: an enum's only
layout knob here is the tag's storage type.

```text
error: 'repr(packed)' and 'repr(align(N))' are not supported on an enum: an
enum's layout knob is the tag's integer type, written 'repr(u8)', 'repr(i16)', ...
```

`repr(...)` on a generic `datac`/`enum` is refused too: an instantiation takes
the default `repr(c)` layout.

### The layout queries

`size_of<T>()`, `align_of<T>()` and `offset_of<T>("field")` each fold to a
`usize`. `T` is a scalar, `bool`, `char`, an `extern type` handle, `Ptr<U>`, a
`datac` or an `enum`; a heap type is refused by name. They are ordinary
expressions, so they work in a body and also fold in a `const` initializer and
an array length. Canonical order puts every `const` before every `datac`, so a
`const` can only query a builtin; a query of a declared type belongs in a body.

```kelp
repr(packed) datac Wire(val kind: u8, val id: u32, val flags: u16)

repr(align(16)) datac Page(val tag: u8, val base: u64)

fun main() {
    print(size_of<Wire>())
    print(align_of<Wire>())
    print(offset_of<Wire>("kind"))
    print(offset_of<Wire>("id"))
    print(offset_of<Wire>("flags"))

    print(size_of<Page>())
    print(align_of<Page>())
    print(offset_of<Page>("base"))
}
```

```text
7
1
0
1
5
16
16
8
```

### Explicit enum discriminants

A **field-less** enum may give a variant an integer value. The values are unique
across the enum and each must fit the tag's storage type; an unwritten
discriminator continues from the previous value plus one, starting at 0.

```kelp
repr(u8) enum Mode {
    Off = 0
    On = 1
    Fast = 10
}
```

`repr(u8|u16|u32|u64|i8|i16|i32|i64)` picks the tag's storage width; the default
is `i32`. `m.to_int()` returns the variant's declared value as the tag's integer
type, and `Mode.from_int(n)` returns `Option<Mode>`, `None` when no variant holds
`n` (so the program imports `std/option`).

```kelp
impl "std/option"

repr(u8) enum Mode {
    Off = 0
    On = 1
    Fast = 10
}

fun main() {
    print(Mode.Fast.to_int())
    if let Some(m) = Mode.from_int(1) {
        print(m.to_int())
    }
}
```

```text
10
1
```

An enum with a payload may not have any explicit discriminant; it is refused by
name. Kelp has no `i8`/`i16` *value* type, so `repr(i8)`/`repr(i16)` store a one-
or two-byte tag but report it as `i32`, the narrowest Kelp integer that holds it.

## Data formats: byte order and unaligned access

### Integer byte-order conversion

Every integer wider than a byte has `x.swap_bytes()`, `x.to_be()` and `x.to_le()`,
plus the two static forms written on the type name, `u32.from_be(x)` and
`u32.from_le(x)`. The set is `u16`, `u32`, `u64`, `i32`, `i64`, `usize`, `isize`.
`u8` has none, deliberately: swapping one byte is the identity. `i16` is not a
Kelp type.

The direction is a property of the *target*, asked rather than assumed: the LLVM
backend reads the target's byte order from its data layout, and the C backend
compiles the direction through `__BYTE_ORDER__`. On a big-endian target
`to_le` swaps and `to_be` does not, on both backends, with no source change.

```kelp
impl "std/fmt"

fun main() {
    val w: u32 = 0x12345678
    print(fmt.hex(w.to_be().to_u64()))
    print(fmt.hex(w.to_le().to_u64()))
    print(fmt.hex(u32.from_be(w).to_u64()))
    print(fmt.hex(w.swap_bytes().to_u64()))
}
```

```text
78563412
12345678
78563412
78563412
```

### Byte-order readers and writers on `Bytes`

`b.read_u16_le(offset)`, `read_u16_be`, `read_u32_le/be`, `read_u64_le/be`,
`read_i32_le/be`, `read_i64_le/be`, and the matching `b.write_*(offset, value)`
for each. The receiver is `&Bytes` for a read and `mut Bytes` for a write, and
every offset is a `usize`.

- **Bounds-checked, with a clear panic.** The message names the method:
  `Bytes.read_u32_le: offset out of bounds`, the same shape `Bytes.get` uses.
  An offset near `usize`'s maximum cannot wrap under the length.
- **No alignment requirement.** The access is a `memcpy` on C and an `align 1`
  load or store on LLVM, so a field at offset 1 is as legal as one at offset 0.
- `u8` needs no reader (`Bytes.get`); `usize`/`isize` are deliberately absent,
  because a wire format fixes its field widths, not the host's pointer width.

```kelp
impl "std/fmt"

fun main() {
    var h = Bytes.empty()
    h.push(0x50)
    h.push(0x4B)
    h.push(0x01)
    h.push(0x02)
    print(fmt.hex(h.read_u16_le(0).to_u64()))
    print(fmt.hex(h.read_u16_be(0).to_u64()))
}
```

```text
4b50
504b
```

### Unaligned pointer access

`p.read_unaligned()` and `p.write_unaligned(v)` are unsafe operations like the
aligned pair, and have the same rules: `read_unaligned` only reads a `Copy`
element. Neither converts byte order. A raw pointer access to memory the program
already laid out is not a data format.

```kelp
fun main() {
    unsafe {
        val raw: Ptr<u8> = Ptr.alloc<u8>(16)
        val p: Ptr<u32> = raw.byte_offset(1).cast<u32>()
        p.write_unaligned(0x12345678)
        print(p.read_unaligned())
        raw.free()
    }
}
```

```text
305419896
```

## What the compiler does not check

`unsafe` is a marker, not a proof. The compiler checks the shape of every
operation (a `Copy` element for a read, a writable place for a write, the module
listing) and nothing about whether the address is valid, aligned, live, aliased
or correctly sized. Provenance and address-space control are not in this
release, so a pointer is a plain integer-shaped address and `from_addr` can name
any of them. `AtomicPtr`, `transmute` and non-`Copy` reads are not here either.
`Ptr.try_alloc`'s null check, the `base`/`cap` an arena is handed, and whether a
`free` is ever called are the caller's promises too.
[`plan/kernel-ub-notes.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/kernel-ub-notes.md)
is the growing catalogue of what that leaves to the program.

## See also

- [Freestanding mode](/language/freestanding): `Ptr` with no allocator, and the
  `mem*` routines the compiler supplies
- [Statics and `defer`](/language/statics-and-defer): `static mut` is the same
  audit rule as an `unsafe` block
- [Coral: the manifest](/tooling/coral#unsafe-modules-that-may-leave-the-checked-language):
  the `[unsafe]` section
