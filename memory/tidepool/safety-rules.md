---
title: "Tidepool: safety rules"
description: "The rules Tidepool enforces on hosted builds, grouped by where they are enforced: at compile time for what may enter the shared pool and cross a thread, and at run time in the collector, with the verify mode checks and the panic rules."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: safety rules

This page lists the rules that Tidepool enforces on hosted builds, grouped by where they
are enforced. The compile-time rules for manual blocks are on
[the boundary](/memory/tidepool/boundary). The rules for the owned values that the shared
pool holds are on [the rules of ownership](/memory/rules).

## Compile time: what may enter the shared pool

- **A resource never enters the collected heap.** A file, socket, process, thread handle,
  `Mutex`, `RwLock`, condition variable, channel end or pool is refused by name wherever
  it would be stored in shared-pool memory. The struct resources are listed in
  `STDLIB_RESOURCE_STRUCTS` in `kelpc/src/managed.rs`. The kinds `Thread`, `Mutex`,
  `RwLock` and `Condvar` are resources by the same file's classifier. The message is
  `'<type>' cannot be <where> in a hosted build: '<type>' is a resource, and a resource
  never enters the collected heap` (`managed.rs`).
- **A value that holds a resource is refused in the same place.** The places are a
  `List` or `Map` element, a `Box` payload, an array element, a field of a heap-resident
  `datac`, a closure environment and a thread's argument or result. See
  [common refusals](/memory/refusals).
- **A `static mut` of a heap type is refused by name**
  (`a_static_mut_of_a_heap_type_is_refused_by_name` in `kelpc/tests/tidepool_step0.rs`).

## Compile time: what may cross into a thread

Thread arguments and results are checked by `crosses` in `kelpc/src/managed.rs`.

- **A channel record crosses.** `Sender`, `Receiver`, `SendEnd` and `RecvEnd` are listed in
  `CROSSING_CHANNEL_RECORDS` (commit `c2503916`, decision 125). The rule reads their fields
  and ignores their destructor, so a worker that panics still closes its channel.
- **A `Mutex` or `RwLock` crosses only when its element is memory.** A lock holding a
  channel end is refused.
- **A `Condvar` crosses.** A thread handle crosses when its value does.
- **A `Pool`, a file, a socket and any other destructor type stay refused.**
- **A `fun` literal used as the entry of `thread.spawn` may capture a `Sender`.** The
  tests `a_closure_entry_may_capture_a_sender` and
  `a_closure_entry_that_panics_still_closes_its_sender` in
  `kelpc/tests/compile_and_run/atomics.rs` run such programs.
- **A block value may not be passed to a spawned thread** (see [the boundary](/memory/tidepool/boundary)).

## Run time: the collector

- **A thread must attach before its first allocation.** An unattached allocation is
  fatal (`gc: allocation on a thread that is not attached`).
- **Every thread must reach a safepoint in time.** A thread that runs a loop must reach a
  safepoint or enter the native state within `KELP_GC_STOP_TIMEOUT_MS` (default 10000 ms).
  If one does not, the collector names it and stops: `gc: thread <tid> did not reach a
  safepoint within <n> ms ... a loop must poll kelp_gc_safepoint or enter native state`
  (`kelpc/gc/src/threads.rs`). A thread blocked in `join`, a lock or a condition wait is
  marked native, so it does not hold up a clearing (commit `92884237`). The tests are
  `t61_a_join_does_not_stop_a_collection`, `t61_a_mutex_wait_does_not_stop_a_collection`
  and `t62_a_loop_over_caller_data_polls_the_collector` in `kelpc/tests/tidepool_step0.rs`.
- **Values held by a thread or a lock are roots.** Thread arguments and results, closure
  environments and lock values are roots (`kelpc/tests/tidepool_s1.rs`, the `t20`, `t21`
  and `t22` tests).
- **A block's element is a root too**, so a clearing marks through it.

## Verify mode

`KELP_GC_VERIFY=1` turns on two checks (`kelpc/gc/src/verify.rs` and `kelpc/gc/src/heap.rs`).
The variable is read at start-up.

- **After every collection, the heap verifier** walks every block and the run-space table,
  checks each object header and extent, and checks that each pointer slot of a survivor
  names a survivor's payload start.
- **At each sweep, dead objects are poisoned.** Every dead object, and every block that has
  no live line, is filled with the byte `0xA5` (`POISON` in `kelpc/gc/src/heap.rs`). A read
  through a dangling pointer then sees that pattern, not the old contents. The test
  `a_dead_object_is_poisoned_in_verify_mode` checks it (commit `da72af0b`).

The collector's own test suite runs with verify mode on. The measurement scripts unset it
(see [tooling and release](/memory/tidepool/tooling-release)).

## Panics

- **A worker that panics leaves the collector and detaches.** The test
  `t58_a_worker_that_panics_leaves_the_collector` in `kelpc/tests/tidepool_step0.rs` checks it.
- **A worker's owned locals are dropped on the way out.** A user `Drop` of each owned local
  runs, newest first, as the fixture `panic_drop_order.kp` shows. A temporary that the
  worker holds at the moment of the panic is not dropped. See [drop](/language/drop).
- **A panic on the main thread runs no drop of the values it holds.** The process exits at
  the panic (`t69_a_main_thread_panic_runs_no_drop`).

## Related

- [Safety tests](/memory/tidepool/safety-tests): the test for each rule.
- [The boundary](/memory/tidepool/boundary): the compile-time refusals for block values.
- [Failure and recovery](/memory/tidepool/failure-recovery): the messages a rule prints.
- [Concurrency in v1](/language/concurrency): the thread rules a program writes against.
- [Tidepool memory design](/memory/tidepool): the index.
