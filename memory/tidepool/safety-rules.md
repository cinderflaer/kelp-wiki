---
title: "Tidepool: safety rules"
description: "The rules that keep a hosted program's memory safe under Tidepool on main: what may cross into a thread, what may enter the shared pool, and what the collector checks at run time. Each rule names the code or test that enforces it."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: safety rules

This page lists the rules that Tidepool enforces on `main`, grouped by where
they are enforced. The compile-time rules for manual blocks are on
[Tidepool: the boundary](/memory/tidepool/boundary). The rules for the owned
values that the shared pool holds are on [The rules of ownership](/memory/rules).

## Compile time: what may enter the shared pool

- A resource never enters the collected heap. A file, socket, process, thread
  handle, `Mutex` or `RwLock` record, condition variable, channel end or pool is
  refused by name wherever it would be stored in shared-pool memory. The list of
  resource types is `STDLIB_RESOURCE_STRUCTS` in `kelpc/src/managed.rs`. The
  refusal text is `'<type>' cannot be <where> in a hosted build: '<type>' is a
  resource, and a resource never enters the collected heap` (`managed.rs`).
- A value that holds a resource is refused in the same place. The places are a
  `List` or `Map` element, a `Box` payload, an array element and a closure
  environment ([Common refusals](/memory/refusals)).
- A `static mut` of a heap type is refused by name
  (`a_static_mut_of_a_heap_type_is_refused_by_name` in
  `kelpc/tests/tidepool_step0.rs`).

## Compile time: what may cross into a thread

Thread arguments and results are checked by `crosses` in `kelpc/src/managed.rs`:

- A channel record crosses as a thread argument or result: `Sender`, `Receiver`,
  `SendEnd` and `RecvEnd` are listed in `CROSSING_CHANNEL_RECORDS`, which the
  commit `c2503916` added (decision 125). The rule reads their fields and ignores
  their destructor, so a worker that panics still closes its channel.
- A `Mutex` or `RwLock` crosses only when its element is memory. A lock holding a
  channel end is refused.
- A `Pool`, a file, a socket and any other destructor type stay refused.
- A `fun` literal used as the entry of `thread.spawn` may capture a `Sender`. The
  tests `a_closure_entry_may_capture_a_sender` and
  `a_closure_entry_that_panics_still_closes_its_sender` in
  `kelpc/tests/compile_and_run/atomics.rs` run such programs.
- A block value may not be passed to a spawned thread (see the boundary page).

## Run time: the collector

- A thread must attach before its first allocation. An unattached allocation is
  fatal (`gc: allocation on a thread that is not attached`).
- Every thread that runs a loop must reach a safepoint or enter the native state
  within `KELP_GC_STOP_TIMEOUT_MS` (default 10000 ms). If one does not, the
  collector names it and stops: `gc: thread <tid> did not reach a safepoint within
  <n> ms ... a loop must poll kelp_gc_safepoint or enter native state`
  (`kelpc/gc/src/threads.rs`). A thread blocked in `join`, a lock or a condition
  wait is marked native, so it does not hold up a clearing (commit `92884237`).
- Values held by a thread or a lock are roots: thread arguments and results,
  closure environments and lock values (Tidepool step 1, `kelpc/tests/tidepool_s1.rs`).
- A block's element is a root too, so a clearing marks through it.

## Verify mode

`KELP_GC_VERIFY=1` turns on two checks (`kelpc/gc/src/verify.rs` and
`kelpc/gc/src/heap.rs`):

- After every collection, the heap verifier walks every block and the run-space
  table, checks each object header, and checks that every pointer slot of a
  survivor names a survivor's payload start.
- At the sweep, every dead object is filled with the byte `0xA5` (`POISON`). A
  read through a dangling pointer then sees that pattern, not the old contents. The
  test `a_dead_object_is_poisoned_in_verify_mode` checks it (commit `da72af0b`).

The verifier is always on in the collector's own test suite. It is off in the
measurement runs of `bench/gc-clear`, because that script sets the environment
variables to unset.

## Panics

- A worker that panics leaves the collector and detaches, and its values are
  dropped on the way out (`t58_a_worker_that_panics_leaves_the_collector` in
  `kelpc/tests/tidepool_step0.rs`).
- A panic on the main thread runs no drop of the values it holds
  (`t69_a_main_thread_panic_runs_no_drop`). The process exits at the panic.
