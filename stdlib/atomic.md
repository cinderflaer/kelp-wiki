---
title: "`std/atomic`"
description: "`Atomic<T>` and the one ordering v1 has. Ungated."
isPublished: true
tags: "stdlib, concurrency"
---
`Atomic<T>` and the one ordering v1 has. Ungated.

```kelp
impl "std/atomic"
```

`Atomic<T>` is a compiler builtin in the shape `List<T>`/`Box<T>`/`Map<K, V>`
have: monomorphized per element type, **not `Copy`**, and needing no drop. It is
one location every access to which is a single atomic operation. The
[Types](/language/types) table carries it with the other builtins. Nothing about
an atomic is written in Kelp, because there is no way to write an atomic access
in the language; that is the whole reason the type is a builtin.

`std/atomic` declares the one thing in the surface that is a plain Kelp type
rather than a builtin:

```kelp
enum Ordering {
    SeqCst
}
```

`Ordering` has **exactly one variant, `SeqCst`**, reached through the module
alias as `atomic.Ordering.SeqCst`. Every operation that touches the cell takes
it as its last argument, and that argument position is what reserves the slot:
`Relaxed`, `Acquire` and `Release` are not in v1, so naming one is the ordinary
unknown-variant error, not a special refusal.

```
error: 'Acquire' is not a variant of enum 'std.atomic.Ordering'
```

Adding a variant later widens the enum and changes no signature, which is why
the argument is there from the first release. Because `Ordering` is an ordinary
`enum`, a `when` over an ordering is exhaustiveness-checked.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `Atomic<T>.new(value: T)` | `Atomic<T>` | the one operation with no ordering argument |
| `Atomic<T>.load(order: Ordering)` | `T` | |
| `Atomic<T>.store(value: T, order: Ordering)` | `Unit` | |
| `Atomic<T>.swap(value: T, order: Ordering)` | `T` | the value that was there |
| `Atomic<T>.compare_exchange(current: T, new: T, order: Ordering)` | `Result<T, T>` | `Ok` the value it replaced, `Err` the value that was actually there |
| `Atomic<T>.fetch_add(value: T, order: Ordering)` | `T` | integers only; the value that was there |
| `Atomic<T>.fetch_sub(value: T, order: Ordering)` | `T` | integers only |
| `Atomic<T>.fetch_and(value: T, order: Ordering)` | `T` | integers only |
| `Atomic<T>.fetch_or(value: T, order: Ordering)` | `T` | integers only |
| `Atomic<T>.fetch_xor(value: T, order: Ordering)` | `T` | integers only |

`AtomicBool` has **no arithmetic at all**: the five `fetch_*` operations are
refused on it, because there is no atomic add for a flag and a `fetch_or` would
be a way to write `true` without saying so.

The element set is `bool` and the integer types, so the type is spelled with one
of these names, each of which is one instantiation of `Atomic<T>`:

| Name | Element |
| --- | --- |
| `AtomicBool` | `bool` |
| `AtomicU8` `AtomicU16` `AtomicU32` `AtomicU64` `AtomicUsize` | `u8` `u16` `u32` `u64` `usize` |
| `AtomicI32` `AtomicI64` `AtomicIsize` | `i32` `i64` `isize` |

There is no `AtomicI8` and no `AtomicI16`, because v1 has no `i8`/`i16` for them
to mean: `AtomicI8` is `unknown type 'AtomicI8'`. There is no float atomic
either, and `Atomic<f64>` is refused as an element. `Atomic<i64>` and
`AtomicI64` are the same type; the name is also the only thing an associated
constructor can be written on, so a fresh cell is `AtomicI64.new(0)`.

## Example

```kelp
impl "std/atomic"
impl "std/result"

// A `pd val` is the shape a shared counter takes: a passdown declared `val`
// hands a function a shared borrow, which is the borrow an atomic mutates
// through, and the borrow a second thread may hold too.
pd val hits: AtomicI64 = AtomicI64.new(0)

fun bump() {
    var done: i64 = 0
    while done < 3 {
        val seen = hits.load(order = atomic.Ordering.SeqCst)
        val r = hits.compare_exchange(current = seen, new = seen + 1, order = atomic.Ordering.SeqCst)
        when r {
            Ok(_) -> { done = done + 1 }
            Err(_) -> {}
        }
    }
}

fun main() {
    val flag: AtomicBool = AtomicBool.new(false)
    flag.store(value = true, order = atomic.Ordering.SeqCst)
    print(flag.swap(value = false, order = atomic.Ordering.SeqCst))   // true

    // The cell holds false, so the exchange fails and `Err` carries what was
    // actually there.
    val failed = flag.compare_exchange(current = true, new = false, order = atomic.Ordering.SeqCst)
    when failed {
        Ok(previous) -> print(previous)
        Err(actual) -> print(actual)      // false
    }

    // This one succeeds, and `Ok` carries the value it replaced.
    val replaced = flag.compare_exchange(current = false, new = true, order = atomic.Ordering.SeqCst)
    when replaced {
        Ok(previous) -> print(previous)   // false
        Err(actual) -> print(actual)
    }
    print(flag.load(order = atomic.Ordering.SeqCst))                  // true

    val c: AtomicU32 = AtomicU32.new(10)
    print(c.fetch_add(value = 5, order = atomic.Ordering.SeqCst))     // 10
    print(c.load(order = atomic.Ordering.SeqCst))                     // 15

    bump()
    print(hits.load(order = atomic.Ordering.SeqCst))                  // 3
}
```

## Notes

- **Every receiver is shared, `store`'s included.** An atomic mutates *through*
  a shared borrow, which is what leaves the type **no `&mut` path**: a
  `&Atomic<T>` is the borrow that may be held by a second thread, and a
  `pd val` is the declaration a shared counter wants, since a passdown declared
  `val` hands a function a shared borrow. A `pd var` counter works too,
  including a store followed by a load in one function; what `var` adds is the
  exclusive borrow a function takes when it assigns to the passdown itself.
- **Not `Copy`, and needing no drop.** Not `Copy` because a copy would be a
  second handle to one location, and every rule about an atomic is about the
  location rather than the handle. No drop because it owns nothing, which is
  what lets a `pd val` atomic exist with no cleanup story.
- **`compare_exchange` hands back `Result<T, T>`** so a retry loop runs off the
  value it saw instead of reloading. A failed exchange leaves the cell alone and
  reports what was actually there in `Err`; a successful one reports the value
  it replaced in `Ok`. A call site needs `impl "std/result"` in the program, and
  the compiler names that module when it is missing.
- **An atomic is a location of its own.** It is refused as a `List`, `Map`, `Box`
  or array element, because the container's own routines read and write an
  element as a plain location and every access to an atomic has to be one atomic
  operation. A `datac` field of atomic type is accepted.
- **An atomic carries no thread by itself.** v1 has no `thread.spawn` and no
  `thread.join`, so nothing shares the cell across threads today; the standalone
  fence, [`thread.fence(order)`](/stdlib/thread), orders no location of its own.
  [Limits in v1](/language/limits) and [Concurrency in v1](/language/concurrency)
  record what does not exist yet.

## See also

- [`std/result`](/stdlib/result) for the `Result<T, T>` `compare_exchange` hands back
- [Types](/language/types) for the builtin type table
- [Limits in v1](/language/limits) for the concurrency that is not there yet
