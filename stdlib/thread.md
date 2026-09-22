---
title: "`std/thread`"
description: "`fence(order)`, the standalone fence, and where `spawn` and `join` will land. Ungated."
isPublished: true
tags: "stdlib, concurrency"
---
`fence(order)`, the standalone fence, and where `spawn` and `join` will land.
Ungated.

```kelp
impl "std/thread"
```

`std/thread` ships one name, and it is a **compiler builtin**:

```kelp
fun fence(order: Ordering)
```

There is no way to write a fence in Kelp, so
[`kelpc/std/thread.kp`](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/kelpc/std/thread.kp)
declares nothing: its header documents the surface, exactly as `std/atomic`
documents the atomic methods it declares nowhere. The compiler lowers the call
to one instruction, so the module needs no `.kp` body.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `thread.fence(order: Ordering)` | `Unit` | one instruction; no cell, no receiver |

## Why it is a free function

A fence orders **no location**: it joins the total order without naming an
atomic, so there is no cell for it to read or write. That is why it is
`thread.fence(order)`, free, rather than an `Atomic<T>` method: a method would
say the fence is an operation on that one cell. It also means the fence emits one
instruction and holds no cell of its own, `__atomic_thread_fence(__ATOMIC_SEQ_CST)`
on the C backend and `fence seq_cst` on the LLVM one, and a single-threaded
program cannot observe it at all.

The fence lives in this module rather than beside the atomic cell so that the
whole thread surface is one module: stage C1 of MK9-S3-M1 adds `spawn` and
`join` here instead of inventing a module around one function.

## The ordering comes from `std/atomic`

`fence` takes the `Ordering` of [`std/atomic`](/stdlib/atomic), so a call site
pays the same `impl "std/atomic"` line and the same module qualifier every
atomic call site pays:

```kelp
thread.fence(order = atomic.Ordering.SeqCst)
```

The qualifier is the **enum's** module, not this one, so `impl "std/thread"`
alone does not bring `Ordering` into scope: writing it unqualified is `undefined
variable 'Ordering'`, and reaching it without `impl "std/atomic"` is `undefined
variable 'atomic'`.

v1 has exactly one ordering, `SeqCst`, so `order` has exactly one legal value.
The argument is the slot that reserves the position for `Relaxed`, `Acquire` and
`Release`: naming one of those is the ordinary unknown-variant error until the
variant exists

```
error: 'Acquire' is not a variant of enum 'std.atomic.Ordering'
```

and adding it widens the enum instead of changing this signature. The model the
ordering means is [Concurrency in v1](/language/concurrency).

## Example

```kelp
impl "std/thread"
impl "std/atomic"

// A fence is the one operation that joins the total order without naming a
// location, so it has no receiver, takes nothing but the ordering, and returns
// `Unit`: there is nothing about it a program can print.
fun main() {
    thread.fence(order = atomic.Ordering.SeqCst)

    // The ordering is `std/atomic`'s enum, which is why the call site pays the
    // same `impl "std/atomic"` line and the same `atomic.` qualifier every
    // atomic call site pays.
    val cell: AtomicI64 = AtomicI64.new(0)
    cell.store(value = 1, order = atomic.Ordering.SeqCst)

    // A fence between two operations on one location changes neither of them
    // in a single-threaded program, and the argument position is what reserves
    // the slot for the orderings v1 does not have yet.
    thread.fence(atomic.Ordering.SeqCst)
    print(cell.load(order = atomic.Ordering.SeqCst))   // 1
}
```

## Notes

- **One instruction, no cell.** The fence is a compiler builtin with no `.kp`
  body and no storage: it lowers to a thread fence and nothing else. It is the
  one operation that joins the total order while naming no location, which is
  the difference between it and every operation of
  [`std/atomic`](/stdlib/atomic).
- **Threads do not exist yet.** v1 has no `thread.spawn` and no `thread.join`, so
  nothing shares a cell across threads today and nothing can race.
  `std/thread` is the module those names will land in, which makes `fence` this
  module's first name and not its last. [Limits in v1](/language/limits) records
  what concurrency does not exist yet.

## See also

- [`std/atomic`](/stdlib/atomic) for `Ordering` and the atomic cell a fence orders around
- [Concurrency in v1](/language/concurrency) for the model the fence is part of
- [Limits in v1](/language/limits) for the concurrency that is not there yet
