---
title: "`std/thread`"
description: "`spawn`, `join`, `fence(order)`, `sleep_ms` and `current_id`: real threads, the panic policy, and the two calls a worker pool needs. Ungated."
isPublished: true
tags: "stdlib, concurrency"
---
`spawn`, `join`, `fence(order)`, `sleep_ms` and `current_id`: real threads, the
shared borrow that may cross one, and the per-thread panic policy. Ungated.

```kelp
impl "std/thread"
```

`std/thread` ships six names: three **compiler builtins**, two ordinary
functions, and one `datac`.

```kelp
fun spawn(entry: <a declared `fun`, a `fun` literal, or a capturing closure, taking one parameter>, arg: move A).return: Thread<T>
fun join(handle: move Thread<T>).return: Result<T, ThreadErr>
fun fence(order: Ordering)
fun sleep_ms(ms: u64)
fun current_id().return: u64

datac ThreadErr(val message: String)
```

`spawn` and `join` are not in the builtin signature table: what crosses the
thread boundary decides their types, so the checker builds the signature at each
call site. Neither call, and not the fence either, can be written in Kelp, so
[`kelpc/std/thread.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/kelpc/std/thread.kp)
declares none of them: its header documents the surface, exactly as
`std/atomic` documents the atomic methods it declares nowhere. The compiler
lowers `spawn` and `join` through the pthread machinery of
`kelpc/runtime/kelp_rt.c` and one generated worker body per call signature.

`ThreadErr` is the module's **only `.kp` declaration**: a plain `datac` with one
owned `String` field, built by the worker's panic and read by whoever joins it.

`sleep_ms` and `current_id` are **ordinary functions**, not checker builtins:
unlike `spawn`, `join` and `fence`, neither one's type depends on what crosses
the thread boundary, so each has a plain `.kp` signature over an `extern fun`
body, the way [`std/time`](/stdlib/time) and [`std/rand`](/stdlib/rand) work.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `thread.spawn(entry, arg)` | `Thread<T>` | starts a worker; `entry` takes exactly one parameter, `arg` is moved into it, and `T` is `entry`'s **return** type |
| `thread.join(handle: move Thread<T>)` | `Result<T, ThreadErr>` | waits for the worker and consumes the handle |
| `thread.fence(order: Ordering)` | `Unit` | one instruction; no cell, no receiver |
| `thread.sleep_ms(ms: u64)` | `Unit` | sleeps the calling thread; takes no capability |
| `thread.current_id()` | `u64` | a stable id for the calling thread, main or worker |

## Starting a worker

`entry` is an ordinary function value or closure: a declared `fun`, a `fun`
literal and a capturing closure all work, and a plain function value is widened
where a closure is expected, so the three spellings are one value. Its single
parameter's type is the type of `arg`.

```kelp
impl "std/thread"
impl "std/atomic"
impl "std/result"

pd val counter: AtomicI64 = AtomicI64.new(0)

fun bump(c: &AtomicI64).return: i64 {
    c.fetch_add(value = 1, order = atomic.Ordering.SeqCst)
    0
}

fun main() {
    val h = thread.spawn(bump, &counter)      // Thread<i64>
    when thread.join(h) {
        Ok(v) -> print(v)                     // the value the worker returned
        Err(e) -> print(e.message)            // why it ended without one
    }
}
```

`arg` is **moved** into the worker, so the worker owns it for as long as it
holds it: a `&mut T` argument is refused, because an exclusive borrow promises
that no other path reaches the value and the worker outlives the frame that made
the borrow.

A worker that returns nothing gives `Thread<unit>`, and joining one hands back
`Result<unit, ThreadErr>` whose `Ok` carries nothing: an `Ok` (or `Some`)
instantiated with `unit` lays out payload-less, the same shape `None` already
has, so the join succeeds and `Ok(v) -> ...` binds `v` to a value with nothing
in it.

## Joining it

`thread.join` waits for the worker and **consumes the handle**: a handle is
joined once. `Ok` carries the value the worker returned, and `Err` carries a
`ThreadErr`, this module's failure type (below), whose `message` is the panic
text the worker died with. A join is a barrier: what the worker wrote to an
atomic is visible to the joiner once its own join has returned.

A join hands back `Result<T, ThreadErr>`, so a program that writes one also
needs `impl "std/result"`, exactly as `Atomic.compare_exchange`'s `Result<T, T>`
does ([`std/result`](/stdlib/result)).

## The one borrow that may cross

**A shared borrow crosses only from a `pd` whose pointee has no reachable `var`
field.** That is the whole of v1's thread-shared data, and both clauses are
structural and builtin: there is no `Send`/`Sync` marker, and each refusal names
its own reason.

- The first clause is checkable because a `pd` global's lifetime is the process
  and a frame local's is not.
- The second is the `Sync`-shaped rule: a `&mut` path reachable from the borrow
  would let two threads write one location through the same borrow.

An [`Atomic<T>`](/stdlib/atomic) satisfies both by construction, because every
access to one is an atomic operation through a shared borrow, which leaves the
type **no `&mut` path**. That is what makes `thread.spawn(bump, &counter)` with
`pd val counter: AtomicI64` the shared counter.

Refused, each with its own reason:

- a `&mut T` argument, and a `&T` borrow of a frame local: the lifetime is the
  sending frame's, and the thread outlives it;
- a `&T` borrow of a `datac` with a reachable `var` field: two threads could
  write it through the same borrow;
- a `str` or a `View` argument: borrowed text with no place of its own.

## The panic policy

**A panic ends the thread it happened in.** A worker that panics is seen as
`Err` by its joiner and the process survives, so one worker's failure does not
take the other workers with it.

The main thread keeps the older behaviour: a panic in `main`, or in a worker
nothing joins before the process ends, still ends the process with `exit(1)`.
The rule is "a panic ends the thread it happened in", and the process ends when
`main` ends.

## The two admitted leaks

v1 has no unwinding, no user `Drop` and no `must_use`, and two leaks follow from
that. Both are deliberate, and both are recorded in
[`plan/mk9-memory-model.md`](https://homelabone.xenoo.dev/gittea/Lilly/kelp/src/branch/main/plan/mk9-memory-model.md)
section 5:

- **A panicking worker's frame is abandoned.** A panic ends the worker by
  `pthread_exit`, so the owned values the abandoned frame held are never
  dropped. Unwinding needs the `Drop` story the language does not have, and
  aborting the process is what the panic policy removes.
- **A handle nobody joins is detached.** Dropping a handle whose worker is
  still running cannot free the worker record, the argument slot or the result
  slot, because the worker writes through them, so the drop detaches the worker,
  which keeps running, and **leaks its record** rather than freeing it under the
  worker. That is one record per handle a program drops without joining.
  Refusing to drop a handle is a rule the language does not have, and blocking
  the drop on the worker would turn a scope exit into a join nobody asked for.
  MK9-S6-M1 (user `Drop`, `defer`, panic-path cleanup) is where the leak is
  closed.

A handle that **is** joined is freed properly by the join itself.

## `ThreadErr`

The module's only `.kp` declaration, and the failure a join hands back:

```kelp
datac ThreadErr(val message: String)
```

One owned `String` field carrying the panic text the worker died with. The panic
text already names the `.kp` line, so the joiner can report where the worker
died, and the compiler names `ThreadErr` through this module's key exactly as an
`Atomic<T>` signature names `Ordering` through `std/atomic`:

```kelp
impl "std/thread"
impl "std/result"

when thread.join(h) {
    Ok(v) -> print(v)
    Err(e) -> print(e.message)   // the panic text, which already names the line
}
```

`Thread<T>` itself is the builtin type the handle takes, in the shape
`Atomic<T>` has ([Types](/language/types)).

## Why it is a free function

A fence orders **no location**: it joins the total order without naming an
atomic, so there is no cell for it to read or write. That is why it is
`thread.fence(order)`, free, rather than an `Atomic<T>` method: a method would
say the fence is an operation on that one cell. It also means the fence emits one
instruction and holds no cell of its own, `__atomic_thread_fence(__ATOMIC_SEQ_CST)`
on the C backend and `fence seq_cst` on the LLVM one, and a single-threaded
program cannot observe it at all.

The fence lives in this module rather than beside the atomic cell so that the
whole thread surface is one module: `spawn` and `join` were added here beside
it, rather than a second module invented around them.

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

## Sleeping and naming a thread

`thread.sleep_ms(ms)` sleeps the calling thread, main or a worker, for at least
`ms` milliseconds. Sleeping takes no capability here for the same reason it
takes none in [`std/time`](/stdlib/time): it is authority over nothing shared.
`std/thread` carries its own copy rather than re-exporting `time.sleep_ms`, so a
worker pool's backoff between empty pulls from a queue does not need
`impl "std/time"`, a namespace named for a wall clock the pool never reads.

```kelp
impl "std/thread"

fun poll_worker(queue_id: move i64) {
    // ... try to pull work, then, if there was none:
    thread.sleep_ms(10)
}
```

`thread.current_id()` returns a `u64` that identifies the calling thread: stable
across every call made from inside one thread, for that thread's whole
lifetime, and distinct between the main thread and any worker `thread.spawn`
starts. It names *which thread this is*, not *which Nth worker was spawned*
nothing in v1 hands out sequential pool slots, and a detached, unjoined
worker's id does not change either. It is backed by `pthread_self`, one
instruction with no syscall behind it.

## Example

```kelp
impl "std/thread"
impl "std/atomic"
impl "std/result"

fun work(x: move i64).return: i64 = x + 1

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

    // A fence exists beside the two calls that do start and join a worker.
    // `thread.spawn(entry, arg)` starts one and `thread.join(handle)` waits for
    // it, consuming the handle; both are detailed above.
    val h = thread.spawn(work, 41)

    // Sleeping and naming a thread work from either side of the join: the
    // main thread's id here differs from `work`'s if it printed its own.
    thread.sleep_ms(1)
    print(thread.current_id() == thread.current_id())   // true

    when thread.join(h) {
        Ok(v) -> print(v)                              // 42
        Err(e) -> print(e.message)
    }
}
```

## Notes

- **Three builtins, two ordinary functions, one declaration.** `fence`, `spawn`
  and `join` are compiler builtins with no `.kp` body: their signatures are
  generic in what crosses the thread boundary, so the compiler builds each
  signature at the call site. `sleep_ms` and `current_id` are plain `.kp`
  signatures over an `extern fun` body, because neither one's type depends on
  the boundary. The module's only declared `datac` is `ThreadErr`.
- **A worker is a real OS thread.** `thread.spawn` starts one and `thread.join`
  waits for it; nothing here is green, pooled or scheduled by the language.
  [Limits in v1](/language/limits) records what the thread surface still does
  not have: no `Relaxed`/`Acquire`/`Release`, no thread-local storage, and no
  async or coroutines. `Mutex<T>`, `RwLock<T>`, `Condvar` and channels are in
  [`std/sync`](/stdlib/sync), and a thread pool is [`std/pool`](/stdlib/pool).
- **The thread pool is a module of its own.** [`std/pool`](/stdlib/pool)
  (`pool.new`, `Pool.spawn`, `Pool.join`) is built on `thread.spawn`, but a
  module cannot call its own builtins by name, so it is not part of
  `std/thread`. A program that wants a handle to each worker still spawns and
  joins them itself, as `examples/download_pool.kp` does. `spawn` takes one
  argument, so a worker that needs several values (a channel's `Sender` and a
  number, say) is handed a `datac` that holds them.
- **`current_id` names a thread, not a pool slot.** v1 hands out no sequential
  worker numbers; a program that wants "worker 3 of 8" has to track that itself,
  keyed by the id if it needs a stable key.
- **`SeqCst` orders the atomics, not the threads.** A worker's writes are
  visible to its joiner because `thread.join` is a barrier, and nothing else
  orders two threads' ordinary memory without an atomic operation or a fence
  between them.

## See also

- [`std/pool`](/stdlib/pool) for a fixed pool of workers over one job queue
- [`std/atomic`](/stdlib/atomic) for `Ordering`, `Atomic<T>` and the shared cell a worker and its joiner both reach
- [Concurrency in v1](/language/concurrency) for the model `spawn`, `join` and the fence are part of
- [Types](/language/types) for `Thread<T>` in the builtin type table
- [Limits in v1](/language/limits) for the concurrency that is not there yet
