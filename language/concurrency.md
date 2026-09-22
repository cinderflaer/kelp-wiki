---
title: "Concurrency in v1"
description: "One ordering, SeqCst, and no threads yet. The model is stated by syntax.md section 12.6."
isPublished: true
tags: "language, concurrency"
---
Source section:
[`syntax.md` §12.6](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

v1 has one ordering and no threads. What ships today is a memory model with a
single ordering and an atomic cell: the cell is what two threads **would**
share, and there is no second thread for anything to race with yet.

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

## The cell two threads would share

An [`Atomic<T>`](/stdlib/atomic) is one location every access to which is a
single atomic operation. A shared counter is declared **`pd val`**, because a
`val` passdown hands a function a shared borrow, which is the borrow a thread
argument may take. A `pd var` counter works as well, including a store followed
by a load in one function, because an atomic's operations are shared borrows
reborrowed from the passdown's hidden reference; what `var` adds is the exclusive
borrow a function takes when it assigns to the passdown itself, and that borrow
may not cross to a thread. That is the same rule that keeps a `&mut T` from being sent anywhere
([Ownership and borrowing](/language/ownership)).

## No threads yet, so nothing can race

v1 has no `thread.spawn` and no `thread.join`: [`std/thread`](/stdlib/thread)
holds only the standalone fence, `thread.fence(order)`. Nothing shares a cell
across threads, so nothing can race, and until a second thread exists the model
above has no observable difference from no model at all. The fence is worth
having on its own anyway: it is one instruction, and it is where the
cross-thread ordering story will attach.

What v1 does not have is listed in [Limits in v1](/language/limits): no threads,
no async, no coroutines.

## Where the definition lives

The definition of the model on record is `plan/mk9-memory-model.md` section 3
until **MK9-S3-M2** states it as the language's own. `syntax.md` §12.6 is the
interim statement, and it borrows the definition by reference rather than
publishing it.

## See also

- [`std/atomic`](/stdlib/atomic) for `Atomic<T>` and the `Ordering` enum
- [`std/thread`](/stdlib/thread) for `fence(order)`
- [Limits in v1](/language/limits) for the concurrency that does not exist yet
- [Ownership and borrowing](/language/ownership) for the borrow rules a thread argument has to obey
