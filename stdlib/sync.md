---
title: "`std/sync`"
description: "`Mutex<T>`: guarded access through a scoped `lock` block, released on every exit and poisoned by a panic. Hosted only."
isPublished: true
tags: "stdlib, concurrency"
---
`Mutex<T>`: guarded access through a scoped `lock` block, released on every
exit and poisoned by a panic. Hosted only.

```kelp
impl "std/sync"
```

`Mutex<T>` is a compiler builtin in the shape `Atomic<T>`/`Thread<T>` have: one
monomorphized type per element, **not `Copy`**, with a drop. `T` is any owned,
borrow-free value, so `Mutex<i64>`, `Mutex<String>` and `Mutex<List<i32>>` all
work. The type is reachable without the import; naming `std/sync` is how a
program declares the module's surface it is using. It is ungated, like
`std/atomic`.

## Surface

```
fun Mutex.new(value: move T).R: Mutex<T>
fun Mutex<T>.lock(block: scoped fun(mut T).R: R).R: R
fun Mutex<T>.into_inner().R: T
```

| Call | Returns | Notes |
| --- | --- | --- |
| `Mutex.new(value: move T)` | `Mutex<T>` | takes the guarded value by move |
| `Mutex<T>.lock(block: scoped fun(mut T).R: R)` | `R` | runs the block while the lock is held; the block's tail is the call's value |
| `Mutex<T>.into_inner()` | `T` | consumes the mutex and hands the value out |

## Example

This program compiles and runs with the output shown:

```kelp
fun take_then_return(c: &Mutex<i64>) {
    c.lock { v ->
        *v = *v + 1
        return
    }
}

fun main() {
    val m: Mutex<i64> = Mutex.new(7)
    print(m.lock { v -> *v + 1 })
    take_then_return(&m)
    print(m.lock { v -> *v })
    print(m.into_inner())
}
```

```
8
8
8
```

The second call's `return` ends the block, the lock is released, and the later
`lock` works: it would deadlock if the first block had left the mutex held.

## The scoped lock block

- `m.lock { v -> ... }` passes `v: mut T` to a `scoped fun(mut T).R: R`, so the
  mutable borrow is the existing non-escaping one: it cannot be stored in a
  `datac`, returned, put in a container, or captured by an ordinary closure,
  because those are all ordinary type mismatches. The block's tail is the call's
  value.
- The block's return type is inferred from the block. `R` is not known before
  the block is checked (`m.lock { v -> *v }` writes no type), so the literal is
  checked with its parameter types from the expected `scoped fun(mut T).R: R`
  and its return from the body's tail. When the call site names a type
  (`return m.lock { v -> ... }` in a function returning `Result<_, _>`), that
  type is used instead, which is what lets a `?` inside the block propagate the
  block's return.
- A `return` inside the block returns from the **block literal**, and a `?`
  returns the failure from the block literal, so the runtime call still returns
  and the unlock still runs. There is no `break` in the language.

## Release and poisoning

- `lock` lowers to the runtime's `kelp_mutex_run(record, body, code, env, out)`,
  which acquires the lock, checks the poison flag, calls the generated block
  body with the `&mut T`, and releases the lock on the normal way out.
- A panic inside the block is the one exit the ordinary call cannot see. The
  block body calls `kelp_panic`, which in a worker ends the thread with
  `pthread_exit`. The runtime registers a cleanup handler before the body runs,
  so `pthread_exit` runs it: the lock is released and the mutex is marked
  **POISONED**. A later `lock` panics with `mutex poisoned`. There is no
  unwinding, so the panicking frame's owned values are still abandoned; the
  mutex itself is not, which is the point of the cleanup handler.
- `into_inner` is the only other way out, and it consumes the whole mutex.

## Crossing a thread boundary

A `&Mutex<T>` is a shared borrow whose pointee has no reachable `&mut` path: the
only way to reach `T` is the lock, which the runtime serializes. The crossing
rule therefore accepts it for the same reason it accepts `&Atomic<T>`, so a
`pd val` mutex can be handed to `thread.spawn` exactly as a `pd val` atomic can.
That holds whatever `T` is, including a `datac` with a `var` field, because the
field is unreachable without the lock. The element predicate keeps a borrow,
`str` or `View` out of the slot in the first place.

```kelp
impl "std/thread"
impl "std/result"

pd val counter: Mutex<i64> = Mutex.new(0)

fun bump(c: &Mutex<i64>).R: i64 {
    c.lock { v -> *v = *v + 1 }
    0
}

fun main() {
    val t = thread.spawn(bump, &counter)
    val r = thread.join(t)
    print(counter.lock { v -> *v })   // 1
}
```

## Hosted only

The runtime half is libc's pthread mutex, so a freestanding manifest refuses
`Mutex<T>`:

```
error: the binding 'm' has type 'Mutex', whose runtime half is a pthread mutex: a freestanding program has no threads and no libc, so a kernel would use a spin lock over an `Atomic<T>` instead
```

The message names the alternative a kernel would use. Freestanding is LLVM-only
by design, and neither backend can lower a mutex without the hosted runtime.

## Refusals

- The slot holds any owned, borrow-free value. `unit` and a borrowed type are
  refused by name:

  ```
  error: 'Mutex.new' needs a value to guard, found 'unit'
  error: 'str' cannot be a 'Mutex' element: a mutex is shared across threads, and a borrow, a 'str' or a 'View' in the slot would be a thread reading data another frame owns. Guard an owned value instead
  ```

- The borrow cannot escape the block. Returning `v` from a function with no
  declared return type is `return type mismatch: expected 'unit', found 'mut
  i64'`, and a `fun` literal that tries to capture `v` is refused because the
  environment it would be stored in outlives the frame the borrow points into.

## What is deliberately out of scope

- Try-lock, timed lock and an ordering slot: v1's surface is `lock` and
  `into_inner`.
- A `lock` that returns a guard value: the scoped block is the whole reason the
  borrow cannot escape, and a returned guard would reintroduce the escape.
- Reader/writer locks, condition variables and cross-process semaphores.
- A spin-lock `Mutex` for freestanding (named in the refusal, not built).

## See also

- [`std/atomic`](/stdlib/atomic)
- [`std/thread`](/stdlib/thread)
- [Concurrency in v1](/language/concurrency)
- [Limits in v1](/language/limits)
