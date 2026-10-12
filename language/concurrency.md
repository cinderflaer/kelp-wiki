---
title: "Concurrency in v1"
description: "The language's own memory model: why a data race does not compile, one ordering (SeqCst), the one borrow that may cross a thread, and the panic policy."
isPublished: true
tags: "language, concurrency"
---
This page defines the memory model: what a data race is, why one does not
compile, what a thread may share, and what happens when a thread panics.

The design record is [`plan/mk9-memory-model.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/mk9-memory-model.md). The syntax is in `syntax.md` §12.5 and §12.6.

v1 has one ordering and real threads. What ships is a memory model with a
single ordering, an atomic cell, a `Mutex<T>`, a fence, and
`thread.spawn`/`thread.join`: the cell and the mutex are what a worker and its
joiner **do** share, and the way they are shared is a rule of the checker
rather than a runtime instrument.

## Why a data race does not compile

A race needs four things at once: one location, two threads, at least one
write, and no ordering between them. v1 removes them one at a time, at compile
time, rather than catching one at run time or leaving the discipline to a
library type:

- **A `&mut T` never crosses a thread boundary.** A borrow's lifetime in v1 is
  lexical in the frame that made it, so the checker cannot prove the sender
  stays out of the value while the thread runs. A `thread.spawn` argument is
  therefore always an owned value, moved in, or the one shared shape below.
- **A shared borrow (`&T`) crosses in exactly one shape**: only from a `pd`
  whose pointee has no reachable `var` field. The first clause is checkable
  lexically, because a `pd` global's lifetime is the process and a frame
  local's is not. The second is the same rule `Sync` states: an `Atomic<T>`
  has no `&mut` path by construction, so a `&AtomicI64` may be shared across
  threads, and a `datac` with a reachable `var` field may not, because two
  threads could otherwise write it through the same shared borrow.
- **Everything else crosses by being moved**, the same rule that already
  governs a `move T` parameter: a value moved to a thread is owned by that
  thread for as long as it holds it.
- **A moved value may not contain an unrelated borrow.** A `datac` may contain a
  `str` or `View` only when construction moves its String/Bytes owner into an
  earlier field of that same value. References, borrowed trait objects, enum
  payloads, Lists and Maps still cannot store a borrow.

Three alternatives were considered and rejected, each for a reason worth
keeping on record:

- **Not a runtime race detector.** A ThreadSanitizer-shaped check turns a race
  into a failure at run time when the language's promise is that the *program
  does not compile*; it also needs a runtime that a freestanding target does
  not have, and it makes "correct" a property of the test run rather than of
  the source. A dynamic checker is still wanted as a *testing instrument*
  (a Miri-style checker) that gives evidence about the checker,
  not the enforcement mechanism.
- **Not channels-only.** A channel is a value type a program may use (it
  is in [`std/sync`](/stdlib/sync#channels), and it is refused on current `main`
  for now), but it cannot be *the*
  mechanism: a
  channel-only model still lets two threads hold a `&mut T` to one location if
  nothing refuses it. The rule above is what makes the race unwritable; a
  channel would be one of the ways to obey it.
- **Not `Mutex`-only, for the same reason.** A lock is a library type that
  needs the same checker rule to be sound underneath it, so the rule came
  first, and `Mutex<T>` is the convenience built on it.

[`std/sync`](/stdlib/sync) holds the locks the rule above makes sound
(`Mutex<T>`, `RwLock<T>`, `Condvar`), and a worker that needs to share more than
one scalar takes one. It also holds the channels, which move owned values
between threads instead of sharing a location, and [`std/pool`](/stdlib/pool)
is a fixed pool of workers over one queue. The limits of both are on their pages:
hosted only, an owned element, one thread created per pool job. On current `main`
both are refused until the step that scans thread and lock values lands, so a
program that uses them does not build yet.

## One ordering: `SeqCst`

`SeqCst` means what C11, C++11 and LLVM `seq_cst` mean: **one total order over
every sequentially consistent operation, with each operation ordered
consistently with that total order and with program order**, and with no data
race among the atomic operations themselves. v1 does not invent a new model
here: it takes the one three other systems already define and states it as
its own.

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

v1 has **exactly one** ordering, so `SeqCst` is the only value that argument
can take. The argument is not ceremony: it is the slot that reserves the
position for `Relaxed`, `Acquire` and `Release` later. Adding one widens the
`Ordering` enum and changes no signature, so no v1 program breaks and no call
site moves; naming one that does not exist yet is the ordinary unknown-variant
error. `Ordering` is a **builtin `enum`**, not a constant, so the exhaustiveness
check applies to it: the day a second variant exists, every `when` over an
ordering is re-checked, and the compiler names the missing arms instead of
silently falling into a default.

On x86-64, `SeqCst` costs extra only on a store, which compiles to an `XCHG` or
`MFENCE` instead of a plain `MOV`. A load or a read-modify-write such as
`fetch_add` or `compare_exchange` costs the same at any ordering. On ARM and
RISC-V the gap is larger, because even acquire and release need real barriers.

The weaker orderings exist for lock-free structures and spinlocks in kernel code.
That is not v1's target, so v1 ships the one ordering that everything else can be
checked against. The others are left to be added later, not designed around now.

## The cell two threads share

An [`Atomic<T>`](/stdlib/atomic) is one location every access to which is a
single atomic operation. A shared counter is declared **`pd val`**, because a
`val` passdown hands a function a shared borrow, which is the borrow a thread
argument may take. A `pd var` counter works as well, including a store followed
by a load in one function. An atomic's operations are shared borrows taken from
the passdown's hidden reference. What `var` adds is the exclusive borrow a
function takes when it assigns to the passdown itself, and that borrow may not
cross to a thread. This is the same rule that keeps a `&mut T` from being sent
anywhere ([Ownership and borrowing](/language/ownership)).

**A `Mutex<T>` is the second shape.** It also has no reachable `&mut` path,
because the lock is the only way to reach `T`, so a `&Mutex<T>` crosses the
same way and for the same reason. It is what a worker uses when the shared
value is bigger than one cell; [`std/sync`](/stdlib/sync) has the surface.

## The threads that exist

`thread.spawn(entry, arg)` starts a real OS thread and
`thread.join(handle)` waits for it, both in [`std/thread`](/stdlib/thread). The
race is removed at compile time rather than at run time, by the two rules the
checker applies to a `spawn` call:

- **an owned value is moved in**, so the worker owns it: a `&mut T` argument is
  refused, because the worker outlives the frame that made the borrow;
- **a shared borrow crosses only from a `pd` whose pointee has no reachable
  `var` field**, which an `Atomic<T>` and a `Mutex<T>` both satisfy by
  construction, since neither has an `&mut` path. That is the single borrow v1
  lets two threads hold at once, so
  `thread.spawn(bump, &counter)` with `pd val counter: AtomicI64` is the shared
  counter and a `datac` with a reachable `var` field is the refused case.

`thread.join` consumes the handle and hands back `Ok` with the value the worker
returned or `Err` with a [`ThreadErr`](/stdlib/thread) carrying the panic text.
A join is a barrier, so a worker's writes are visible to its joiner once its own
join has returned.

`thread.sleep_ms(ms)` and `thread.current_id()` sit beside `spawn`/`join` for a
worker pool to use: sleeping backs off between empty pulls, and the id names
which thread is running without the language handing out pool slots. Neither
one touches the ordering model above they order nothing and share no cell.

### The panic policy

**A panic ends the thread it happened in, and the process survives.** A worker
that panics is seen as `Err` by its joiner, carrying the panic text (which
already names the `.kp` line it died at), and every other worker keeps
running: one bad URL in a download pool does not take the other workers with
it. The main thread keeps the older behaviour, since nothing has changed for a
program that spawns nothing: a panic in `main`, or in a worker nothing joins
before the process ends, still ends the process with `exit(1)`.

**v1 has no unwinding, and the consequence is admitted rather than hidden.**
Kelp has no exceptions and no `catch`, so a panicking worker's frame is
abandoned: the owned values it held are never dropped. That
is a deliberate trade against the two alternatives, both worse here: real
unwinding needs a `Drop` story the language does not have, and aborting the
whole process is exactly what this policy removes. A handle nobody joins is
the same shape: dropping it detaches the worker, which keeps running, and its
result slot is leaked rather than freed out from under it. Until a panic can
unwind, a program that spawns threads accepts these leaks as the cost of
surviving a single worker's failure.

## A worked example: concurrent downloads

`examples/download_pool.kp` is the payoff of the rules above: N
paths fetched from one host by four worker threads, each holding its own
[`http.Pool`](/stdlib/http) and never sharing it with another thread. A pool's
`var idle` field is exactly the shared mutable state a `thread.spawn` argument
is refused for, so the only way to give a worker a keep-alive pool is to let it
build its own the moment it starts, which is what each of the four does with
`http.pool(host, port)`.

The path list is split across the four workers by a static round robin
*before* any of them is spawned, not pulled from a shared queue while they run:
`Thread<T>` cannot be a `List`, `Map`, `Box` or array element (a handle is
joined once, while a container's own routines copy and drop an element like a
plain location). [`std/sync`'s `Mutex`](/stdlib/sync) can guard a shared queue,
but the split here is done before the spawn so no lock is needed. Four workers
are therefore four named
`Thread<Outcome>` locals, joined in a fixed order, the same shape
[`std/thread`'s stress test](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/kelpc/tests/fixtures/thread_stress.kp)
uses for its eight.

No language or stdlib change was needed for this milestone: everything it
uses (`thread.spawn`/`thread.join`, an explicit `Pool`, `List`) already existed
once threads did.

## What is still open

Four questions were deliberately left for when they actually come up, rather
than decided speculatively; none of them blocks anything above:

- **`compare_exchange`, strong form only, or a `_weak` alongside it?** The weak
  form only helps inside a loop that retries anyway.
- **A `pd` atomic inside a capability-gated module** is a capability question
  as well as a memory-model one. It waits for the capability design to cover it.
- **`Relaxed`, `Acquire` and `Release`** are reserved argument values, not
  shipped: see "One ordering" above.
- **Channels and a pool are built on the rule above.** A channel is a
  `Mutex`-guarded queue whose two ends share one runtime record through
  `Mutex.share()`, and a pool is the same queue of closures
  ([`std/sync`](/stdlib/sync), [`std/pool`](/stdlib/pool)). On current `main` they are
  refused, with `select` and rendezvous channels, until the step that lets the
  collector see values that a thread or a lock holds.

## See also

- [`std/atomic`](/stdlib/atomic) for `Atomic<T>` and the `Ordering` enum
- [`std/thread`](/stdlib/thread) for `spawn`, `join`, `fence(order)`, `sleep_ms` and `current_id`
- [Limits in v1](/language/limits) for the concurrency that is not there yet
- [Ownership and borrowing](/language/ownership) for the borrow rules a thread argument has to obey
