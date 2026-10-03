---
title: "`std/sync`"
description: "`Mutex<T>`, `RwLock<T>` and `Condvar` through scoped blocks, plus bounded and unbounded channels (`sync.bounded`, `Sender`, `Receiver`, `for v in rx`) and `Mutex.share`/`swap`. Hosted only. The thread pool is `std/pool`."
isPublished: true
tags: "stdlib, concurrency"
---
`Mutex<T>`, `RwLock<T>` and `Condvar`: guarded access through scoped blocks,
released on every exit and poisoned by a panic, and a condition wait that
releases the lock around the sleep. On top of them sit channels
(`sync.bounded`, `sync.unbounded`, `Sender<T>`, `Receiver<T>`) and the two
small operations they are built from, `share` and `swap`. A thread pool is
[`std/pool`](/stdlib/pool). Hosted only.

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

`Mutex<T>` also has `wait_while` and `wait_while_timeout`, which pair it with a
[`Condvar`](#condvar-and-wait_while) below. `RwLock<T>` follows right after.

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
  and the unlock still runs. A `break` or `continue` inside the block cannot leave a loop outside the block: a `break` written there is refused as having no enclosing loop.

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

## `RwLock<T>`

A reader/writer lock in the same shape as `Mutex<T>`: a compiler builtin, not
`Copy`, reachable without the import, guarding one owned borrow-free value that
is reached only through a scoped block.

```
fun RwLock.new(value: move T).R: RwLock<T>
fun RwLock<T>.read(block: scoped fun(&T).R: R).R: R
fun RwLock<T>.write(block: scoped fun(mut T).R: R).R: R
fun RwLock<T>.try_read(block: scoped fun(&T).R: R).R: Option<R>
fun RwLock<T>.try_write(block: scoped fun(mut T).R: R).R: Option<R>
fun RwLock<T>.into_inner().R: T
```

| Call | Returns | Notes |
| --- | --- | --- |
| `RwLock.new(value: move T)` | `RwLock<T>` | takes the guarded value by move |
| `read(block)` | `R` | the block gets a shared `&T`; many readers run at once |
| `write(block)` | `R` | the block gets `mut T`; one writer runs alone |
| `try_read(block)` / `try_write(block)` | `Option<R>` | the block runs only if the lock was free; `None` means it was busy and the block did not run |
| `into_inner()` | `T` | consumes the lock |

This program shares one lock between the main thread and a worker. It prints, on
the LLVM backend and under `KELPC_ORACLE=c` alike:

```kelp
impl "std/thread"
impl "std/result"
impl "std/option"

pd val config: RwLock<i64> = RwLock.new(10)

fun bump(c: &RwLock<i64>).R: i64 {
    c.write { v -> *v += 5 }
    c.read { v -> *v }
}

fun probe(c: &RwLock<i64>) {
    c.read { v ->
        val w = c.try_write { x -> *x = 0 }
        print(option.is_none(o = w))
    }
}

fun main() {
    print(config.read { v -> *v })
    val t = thread.spawn(bump, &config)
    when thread.join(t) {
        Ok(v) -> print(v)
        Err(e) -> print(e.message)
    }
    print(config.read { v -> *v * 2 })
    // a read is busy for a writer, and a write is busy for everyone
    probe(&config)
    val last = config.try_write { v ->
        *v += 1
        *v
    }
    print(option.unwrap(o = last))
}
```

```
10
15
30
true
16
```

- The worker adds 5 under `write` and reads back 15; the main thread reads 15
  and doubles it to 30.
- Inside `probe`'s `read`, `try_write` finds the lock busy (`true` for
  `is_none`). A `read` block cannot name the passdown directly, so the lock is
  passed to `probe` as a parameter, the same rule every `pd` follows in a `fun`
  literal.
- After the reads end, `try_write` gets the lock and the block's value, 16, comes
  back as `Some`.

**Policy.** The lock is **writer-preferring**: a waiting writer blocks new
readers, so a stream of readers cannot starve it, and a busy `try_read` also
fails while a writer is waiting. It is a runtime built from a mutex, two
condition variables and three counters rather than `pthread_rwlock_t`, whose
policy is unspecified.

**Poisoning.** A panic inside `write` releases the lock and **poisons** it: every
later `read` or `write` panics with `rwlock poisoned`. A panic inside `read`
releases the read and does **not** poison, because a reader never changes the
value. `try_read` and `try_write` never poison. This worker panics inside
`write`:

```kelp
impl "std/thread"
impl "std/result"

pd val rw: RwLock<i64> = RwLock.new(0)

fun boom(r: &RwLock<i64>).R: i64 {
    r.write { v ->
        *v = 99
        panic("writer exploded")
    }
}

fun main() {
    val t = thread.spawn(boom, &rw)
    when thread.join(t) {
        Ok(_) -> print("joined")
        Err(e) -> print(e.message)
    }
    print(rw.read { v -> *v })
}
```

Standard output carries the worker's panic text, standard error carries the
second panic, and the exit status is 1, on both backends:

```
writer exploded
panic: rwlock poisoned
```

`RwLock<T>` crosses a thread boundary the same way `Mutex<T>` does (a `&RwLock<T>`
in a `pd`, as above), and `T` is held to the same element rule as `Mutex`.

## `Condvar` and `wait_while`

A condition variable. A wait has to release the mutex's own lock around the
sleep, which a scoped guard cannot express, so the wait is a method **on the
mutex** that takes the `Condvar`:

```
fun Condvar.new().R: Condvar
fun Condvar.notify_one()
fun Condvar.notify_all()
fun Mutex<T>.wait_while(cv: &Condvar, pred: fun(&T).R: bool, block: scoped fun(mut T).R: R).R: R
fun Mutex<T>.wait_while_timeout(cv: &Condvar, pred: fun(&T).R: bool, millis: i64, block: scoped fun(mut T).R: R).R: Option<R>
```

`m.wait_while(&cv, pred) { v -> ... }` sleeps while `pred(&v)` is true, re-tests
it after every wakeup, and then runs the block with the lock held. A spurious
wakeup is invisible to the caller, and there is no bare `wait`. A panic in the
predicate or the block releases and poisons the mutex like a panic in `lock`.

```kelp
impl "std/thread"
impl "std/result"

pd val shared: Shared = Shared(
    box = Mutex.new(Mailbox(ready = false, value = 0)),
    cv = Condvar.new(),
)

datac Mailbox(var ready: bool, var value: i64)
datac Shared(val box: Mutex<Mailbox>, val cv: Condvar)

fun not_ready(m: &Mailbox).R: bool = !m.ready

fun consumer(s: &Shared).R: i64 {
    s.box.wait_while(&s.cv, not_ready) { m -> m.value }
}

fun main() {
    val t = thread.spawn(consumer, &shared)
    shared.box.lock { m ->
        m.value = 42
        m.ready = true
    }
    shared.cv.notify_all()
    when thread.join(t) {
        Ok(v) -> print(v)
        Err(e) -> print(e.message)
    }
}
```

It prints `42` on both backends:

```
42
```

The consumer waits until `ready` is set; the main thread sets it under `lock` and
calls `notify_all`. Whichever side runs first, the wakeup cannot be missed,
because the predicate is tested under the lock before sleeping. The mutex and the
condition variable travel together as one shared borrow of a `pd`.

`wait_while_timeout` also gives up after `millis` milliseconds. It shares `try_*`'s
shape: `None` means the deadline passed with the predicate still true and the
block did not run.

```kelp
impl "std/option"

fun not_ready(v: &i64).R: bool = v == 0

fun main() {
    val m: Mutex<i64> = Mutex.new(0)
    val cv: Condvar = Condvar.new()
    val first = m.wait_while_timeout(&cv, not_ready, 30) { v -> *v }
    print(option.is_none(o = first))
    m.lock { v -> *v = 7 }
    val second = m.wait_while_timeout(&cv, not_ready, 30) { v -> *v }
    print(option.unwrap(o = second))
}
```

```
true
7
```

Nothing notifies, so the first wait times out (`is_none` is `true`); after the
value changes the predicate is already false and the second returns `Some(7)`.

## `Mutex.share` and `Mutex.swap`

Two small builtin operations carry everything a channel or a pool needs.

```
fun Mutex<T>.share().R: Mutex<T>
fun Condvar.share().R: Condvar
fun Mutex<T>.swap(value: move T).R: T
```

- `share()` returns **another owned handle to the same runtime record**. The
  record has a reference count, and the last handle's drop frees it. It is how
  two threads each own a mutex without a `pd`. `into_inner` on a mutex whose
  record is still shared panics, because the value is still reachable through
  the other handle.
- `swap(value)` moves an owned value in and the old one out in one locked step.
  It exists because a scoped block captures an owned value by borrow only, so a
  block cannot move a value across by itself.

```kelp
impl "std/sync"

fun bump(m: move Mutex<i64>) {
    m.lock { v -> *v = *v + 1 }
}

fun main() {
    val m: Mutex<i64> = Mutex.new(5)
    val other = m.share()
    bump(m.share())
    print(other.lock { v -> *v })
    val old = other.swap(40)
    print(old)
    print(m.lock { v -> *v })
}
```

`bump` takes a handle by `move` and drops it on return; the other two handles
still see the value. It prints, on the LLVM backend and under `KELPC_ORACLE=c`
alike:

```
6
6
40
```

## Channels

A channel moves **owned values** between threads instead of sharing a location.
Both ends are ordinary Kelp values written in `std/sync` over `Mutex`, `Condvar`,
`share` and `swap`; there is no new runtime record.

```
fun sync.bounded<T>(cap: usize).R: (Sender<T>, Receiver<T>)
fun sync.unbounded<T>().R: (Sender<T>, Receiver<T>)
fun Sender<T>.send(value: move T).R: option.Option<T>
fun Sender<T>.clone().R: Sender<T>
fun Receiver<T>.recv().R: result.Result<T, RecvErr>
fun Receiver<T>.try_recv().R: option.Option<T>
fun Receiver<T>.recv_timeout(millis: i64).R: result.Result<T, RecvTimeout>
for v in rx { ... }
```

| Call | Returns | Notes |
| --- | --- | --- |
| `sync.bounded<T>(cap)` | `(Sender<T>, Receiver<T>)` | at most `cap` queued values; `send` waits while it is full. `cap` of 0 panics |
| `sync.unbounded<T>()` | `(Sender<T>, Receiver<T>)` | no limit; `send` never waits |
| `tx.send(value)` | `Option<T>` | `None` means it was queued; `Some(value)` hands the value back because the receiver is gone |
| `tx.clone()` | `Sender<T>` | another sender on the same channel |
| `rx.recv()` | `Result<T, RecvErr>` | waits while the queue is empty and a sender is alive; `Err(RecvErr.Closed)` once it is empty and every sender is gone |
| `rx.try_recv()` | `Option<T>` | the oldest value now; never waits |
| `rx.recv_timeout(ms)` | `Result<T, RecvTimeout>` | `Err(Timeout)` when the wait ran out with a sender still alive, `Err(Closed)` when every sender is gone |
| `for v in rx` | one value per pass | ends when the channel is closed and drained |

The pair is a tuple, so it is taken apart with a destructuring binding. Write
`var (tx, rx) = ...` when a `for` over `rx` needs a mutable place, and `val`
otherwise. `thread.spawn` takes one argument, so a worker that needs a sender
gets it inside a `datac`. Two producers and one consumer, the producers
`send`ing three values each through a channel of capacity 2:

```kelp
impl "std/thread"
impl "std/result"
impl "std/sync"

datac Job(val tx: sync.Sender<i64>, val base: i64)

fun produce(job: move Job) {
    val tx = job.tx
    val base = job.base
    var i: i64 = 0
    while i < 3 {
        val back = tx.send(base + i)
        i += 1
    }
}

fun main() {
    var (tx, rx) = sync.bounded<i64>(2)
    val a = thread.spawn(produce, Job(tx = tx.clone(), base = 10))
    val b = thread.spawn(produce, Job(tx = tx, base = 20))
    var total: i64 = 0
    var n = 0
    for v in rx {
        total += v
        n += 1
    }
    print(n)
    print(total)
    when thread.join(a) {
        Ok(_) -> {}
        Err(e) -> print(e.message)
    }
    when thread.join(b) {
        Ok(_) -> {}
        Err(e) -> print(e.message)
    }
}
```

The loop ends by itself: `main`'s own `tx` was moved into the second job, so
the channel closes when both workers have returned and dropped their senders.
Both backends print:

```
6
96
```

The six values sum to 10 + 11 + 12 + 20 + 21 + 22 = 96; their order depends on
the threads, so the program prints only the count and the sum.

### `try_recv` and `recv_timeout`

```kelp
impl "std/result"
impl "std/option"
impl "std/sync"

fun show(o: move option.Option<i64>).R: i64 = when o {
    Some(v) -> v
    None -> -1
}

fun main() {
    val (tx, rx) = sync.unbounded<i64>()
    val none = tx.send(5)
    val none2 = tx.send(6)
    print(show(rx.try_recv()))
    when rx.recv_timeout(10) {
        Ok(v) -> print(v)
        Err(e) -> when e {
            Timeout -> print("timeout")
            Closed -> print("closed")
        }
    }
    when rx.recv_timeout(10) {
        Ok(v) -> print(v)
        Err(e) -> when e {
            Timeout -> print("timeout")
            Closed -> print("closed")
        }
    }
    print(show(rx.try_recv()))
}
```

```
5
6
timeout
-1
```

The queue is first-in first-out. The third call times out because `tx` is still
alive; with the sender gone it would answer `closed`.

### Closing

A channel closes when **every sender has dropped**, or when **the receiver has
dropped**. Closing is the drop of a hidden non-generic end each handle owns, so
it needs no call.

- With every sender gone, `recv` first drains what is queued and then answers
  `Err(RecvErr.Closed)`; `for v in rx` ends at that point.
- With the receiver gone, `send` returns `Some(value)`: the value comes back to
  the sender instead of being lost.

```kelp
impl "std/result"
impl "std/option"
impl "std/sync"

fun fill(tx: move sync.Sender<i64>) {
    val a = tx.send(1)
    val b = tx.send(2)
}

fun hang_up(rx: move sync.Receiver<String>) {
}

fun main() {
    // every sender gone: queued values drain, then recv answers Err
    val (tx, rx) = sync.unbounded<i64>()
    fill(tx)
    var total: i64 = 0
    var open = true
    while open {
        when rx.recv() {
            Ok(v) -> total += v
            Err(_) -> open = false
        }
    }
    print(total)

    // receiver gone: send hands the value back
    val (tx3, rx3) = sync.bounded<String>(1)
    hang_up(rx3)
    when tx3.send(String.from_str("back")) {
        Some(s) -> print(s)
        None -> print("lost")
    }
}
```

```
3
back
```

### Limits of channels

- **The element must be an owned, borrow-free value.** A `str` or `View` would be
  a thread reading text another frame owns, and a `Mutex`, `RwLock` or `Condvar`
  is reached by borrowing it, never by moving it through a queue. Both are
  refused when the channel is made. `sync.bounded<str>(2)` says:

  ```
  error: in 'std.sync.bounded<str>': in 'std.sync.Sender<str>': 'str' is a borrowed view: a 'List' element is owned by the list, so it has to outlive it (v1 has no lifetime syntax to say otherwise); use a scalar, 'String', 'Bytes', a 'datac', an 'enum', another 'List', or a 'Box'
  ```

  and `sync.bounded<Mutex<i64>>(2)` says:

  ```
  error: in 'std.sync.bounded<Mutex<i64>>': in 'std.sync.Sender<Mutex<i64>>': 'Mutex<i64>' cannot be a 'List' element: a mutex owns a runtime record and is reached by borrowing it, while a container's own routines move and drop an element like a plain location. Keep the mutex in a local or a field ('val m = Mutex.new(0)') and lock it there
  ```

- **No zero-capacity (rendezvous) channel.** `sync.bounded<i64>(0)` panics with
  `sync.bounded: the capacity must be at least 1`.
- **`send` returns `Option<T>`, not `Result<(), E>`**, because no expression
  produces `unit` to put in an `Ok`. `None` is success. The compiler does **not**
  force you to look at the result (v1 has no `must_use`), so `tx.send(1)` on its
  own line compiles and silently drops the value that comes back when the
  receiver is gone. The examples bind it (`val back = tx.send(v)`) to say so.
- **No `select`** over several channels, no `try_send`, and no receive with a
  deadline on more than one channel. A receiver has one owner: it is not
  cloneable, so there is no multi-consumer queue (use a [pool](/stdlib/pool)).
- **`for v in rx` needs a mutable place**, so bind the pair with `var`. A trait
  impl cannot name a generic instantiation, so `Receiver<T>` is not an
  `Iterator` implementor: the compiler's `for` accepts a generic `datac` whose
  template declares `fun mut Receiver<T>.next().R: option.Option<T>`, which is
  an ordinary `next()` call underneath.
- **Hosted only.** `std/sync` is a hosted module, so a freestanding build names
  the module:

  ```
  error: the module 'std/sync' is unavailable in a freestanding build: it needs a hosted runtime (libc or the 'kelp_rt' helpers); the std modules a freestanding project may implement are std/arena, std/atomic, std/convert, std/frame, std/irq, std/iter, std/list, std/math, std/ops, std/option, std/regex, std/result, std/str
  ```

  The same program passes on the LLVM backend and under `KELPC_ORACLE=c`; the
  tests are `chan_bounded_mpsc` (four producers, one consumer, sum 124500),
  `chan_close`, `chan_recv_timeout`, `chan_zero_capacity`, `chan_non_sendable`
  and `chan_send_a_lock`.

## The thread pool

A worker pool is its own module, [`std/pool`](/stdlib/pool), built from
`Mutex`, `Condvar` and `thread.spawn`.

## Hosted only

The runtime half is libc's pthread primitives, so a freestanding manifest refuses
`Mutex<T>`, `RwLock<T>` and `Condvar` by name. The `Mutex` message, for
example:

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

- A try-lock or timed lock on `Mutex<T>` itself (`RwLock<T>` has `try_read` and
  `try_write`), and an ordering slot.
- A `select` over several channels, a rendezvous (capacity 0) channel and a
  multi-consumer receiver (see [Limits of channels](#limits-of-channels)).
- A `lock` that returns a guard value: the scoped block is the whole reason the
  borrow cannot escape, and a returned guard would reintroduce the escape.
- A blocking `Condvar.wait` that hands back a guard; `wait_while` is the shape.
- Cross-process semaphores, and a `select` over several waits.
- A spin-lock `Mutex` for freestanding (named in the refusal, not built).

## See also

- [`std/atomic`](/stdlib/atomic)
- [`std/thread`](/stdlib/thread)
- [`std/pool`](/stdlib/pool)
- [Concurrency in v1](/language/concurrency)
- [Limits in v1](/language/limits)
