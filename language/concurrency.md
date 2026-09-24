---
title: "Concurrency in v1"
description: "One ordering, SeqCst, real threads, and the single shared borrow that may cross one. The model is stated by syntax.md section 12.6."
isPublished: true
tags: "language, concurrency"
---
Source section:
[`syntax.md` §12.6](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

v1 has one ordering and real threads. What ships is a memory model with a single
ordering, an atomic cell, a fence, and `thread.spawn`/`thread.join`: the cell is
what a worker and its joiner **do** share, and the way it is shared is a rule of
the checker rather than a runtime instrument.

## One ordering: `SeqCst`

`SeqCst` means what C11, C++11 and LLVM `seq_cst` mean: **one total order over
every sequentially consistent operation, with each operation ordered
consistently with that total order and with program order**, and with no data
race among the atomic operations themselves. That is the whole claim: v1 does
not invent a model, it borrows one and names it.

Every atomic operation and the fence take the ordering as an argument:

```kelp
impl "std/atomic"
impl "std/thread"

pd val hits: AtomicI64 = AtomicI64.new(0)

fun main() {
    hits.store(value = 1, order = atomic.Ordering.SeqCst)
    thread.fence(order = atomic.Ordering.SeqCst)
    print(hits.load(order = atomic.Ordering.SeqCst))   // 1
}
```

v1 has **exactly one** ordering, so `SeqCst` is the only value that argument can
take. The argument is not ceremony: it is the slot that reserves the position
for `Relaxed`, `Acquire` and `Release` later. Adding one widens the `Ordering`
enum and changes no signature, so no v1 program breaks and no call site moves;
naming one that does not exist yet is the ordinary unknown-variant error.

## The cell two threads share

An [`Atomic<T>`](/stdlib/atomic) is one location every access to which is a
single atomic operation. A shared counter is declared **`pd val`**, because a
`val` passdown hands a function a shared borrow, which is the borrow a thread
argument may take. A `pd var` counter works as well, including a store followed
by a load in one function, because an atomic's operations are shared borrows
reborrowed from the passdown's hidden reference; what `var` adds is the exclusive
borrow a function takes when it assigns to the passdown itself, and that borrow
may not cross to a thread. That is the same rule that keeps a `&mut T` from being sent anywhere
([Ownership and borrowing](/language/ownership)).

## The threads that exist

`thread.spawn(entry, arg)` starts a real OS thread and
`thread.join(handle)` waits for it, both in [`std/thread`](/stdlib/thread). The
race is removed at compile time rather than at run time, by the two rules the
checker applies to a `spawn` call:

- **an owned value is moved in**, so the worker owns it: a `&mut T` argument is
  refused, because the worker outlives the frame that made the borrow;
- **a shared borrow crosses only from a `pd` whose pointee has no reachable
  `var` field**, which an `Atomic<T>` satisfies by construction, since it has no
  `&mut` path. That is the single borrow v1 lets two threads hold at once, so
  `thread.spawn(bump, &counter)` with `pd val counter: AtomicI64` is the shared
  counter and a `datac` with a reachable `var` field is the refused case.

`thread.join` consumes the handle and hands back `Ok` with the value the worker
returned or `Err` with a [`ThreadErr`](/stdlib/thread) carrying the panic text.
A join is a barrier, so a worker's writes are visible to its joiner once its own
join has returned. A panic ends the thread it happened in and the process
survives it; a panic in `main` still exits.

What a thread does **not** have in v1 is listed in
[Limits in v1](/language/limits): one ordering, no channels, no `Mutex`, no
thread-local storage, no async and no coroutines.

## Where the definition lives

The definition of the model on record is `plan/mk9-memory-model.md` section 3
until **MK9-S3-M2** states it as the language's own. `syntax.md` §12.6 is the
interim statement, and it borrows the definition by reference rather than
publishing it.

## See also

- [`std/atomic`](/stdlib/atomic) for `Atomic<T>` and the `Ordering` enum
- [`std/thread`](/stdlib/thread) for `spawn`, `join` and `fence(order)`
- [Limits in v1](/language/limits) for the concurrency that is not there yet
- [Ownership and borrowing](/language/ownership) for the borrow rules a thread argument has to obey
