---
title: "Tidepool: failure and recovery"
description: "What a hosted program sees when Tidepool cannot allocate, cannot stop a thread or is misconfigured: which failures return a value, which stop the process, the exact messages and the counter line that prints first. Each entry names its source."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: failure and recovery

Tidepool has two kinds of failure. A manual block that cannot be made returns a
value, `Err(BlockError.Full)`, and the program goes on. Every other failure stops
the process with a fatal message. This page lists both kinds. The sizing rules
that decide when they happen are on [Tidepool: the budget](/memory/tidepool/budget).

## Failures that return a value

| Situation | What the program gets | Source |
| --- | --- | --- |
| a manual block does not fit under `heap_max`, even after one clearing | `Err(BlockError.Full)` | `block::alloc` in `kelpc/gc/src/block.rs`, `emit_block_box` in `kelpc/src/codegen_llvm/frame.rs` |
| the root table cannot take another slot for a block | `Err(BlockError.Full)` | `BLOCK_ROOT_FULL`, same files |
| a block's chunk cannot be mapped | `Err(BlockError.Full)` | `BLOCK_NO_MEMORY`, same files |

A failed block leaves nothing charged and nothing registered. The collector undoes
the mapping and the charge before it returns the status (`block::alloc`).

## Failures that stop the process

| Situation | Message | Source |
| --- | --- | --- |
| a shared-pool allocation fails after a clearing | `out of shared-pool memory: heap_max is <n> MiB, <n> MiB was live at the last clearing, and <n> MiB is charged to live blocks`, then a note to keep less data live or raise `heap_max` | `out_of_shared_pool` in `kelpc/gc/src/lib.rs` |
| the operating system refuses a mapping | `out of memory` | `map` in `kelpc/gc/src/lib.rs` |
| an array's count is above 4294967295 | `array of <n> elements is too large: a shared-pool array holds at most 4294967295 elements` | `array_too_large` in `lib.rs` |
| an array's byte size overflows | `array size overflows: <n> elements of <n> bytes each` | `array_overflows` in `lib.rs` |
| a thread allocates without attaching | `gc: allocation on a thread that is not attached (call kelp_gc_thread_attach before the first allocation)` | `alloc_common` in `lib.rs` |
| a type's alignment is above 8 | `gc: type alignment above 8 is not supported in v1` | `alloc_common` in `lib.rs` |
| a thread does not reach a safepoint in time | `gc: thread <tid> did not reach a safepoint within <n> ms (registry slot <n>); a loop must poll kelp_gc_safepoint or enter native state` | `threads.rs` |
| a collecting thread is not attached | `gc: collecting thread is not attached (call kelp_gc_thread_attach)` | `threads.rs` |

A panic hook can see the out-of-memory message. The hook is set through the
collector's `oom_hook`, and the test `panic_hook_receives_the_out_of_memory_message`
in `kelpc/tests/gc/enum_tag.rs` checks that the hook gets the text and that the exit
status is kept.

## The counter line first

When `KELP_GC_STATS=1` is set, every fatal exit prints the counter line before
its message. `fatal` in `kelpc/gc/src/sys.rs` calls `print_stats_once`, which
prints at most once per process:

```text
kelp-gc-stats: collections=<n> pause_total_us=<n> pause_max_us=<n> roots=<n> charged_bytes=<n>
```

The test `t80_fatal_stats_and_oom` in `kelpc/tests/managed/tidepool_s1/` runs a
program that exhausts the pool, and checks that the line is printed before the
panic.

## Bad settings

A collector variable whose value is not a whole number is ignored with a notice:
`gc: ignored <NAME>='<value>': expected a whole number` (`env_usize` in `lib.rs`;
test `t77_bad_gc_env`). The notice does not stop the program.

`KELP_GC_STOP_TIMEOUT_MS=0` is replaced by the default with the notice `gc:
KELP_GC_STOP_TIMEOUT_MS must be at least 1`. The default timeout is 10000 ms
(`DEFAULT_STOP_TIMEOUT_MS` in `kelpc/gc/src/state.rs`).

A bad `heap_max` or `[tidepool]` value is not a run-time failure. The compiler
refuses it when it reads `coral.toml` (see [settings](/memory/tidepool/settings)).

## Threads

- A worker that panics leaves the collector and detaches. Its drops run on the way
  out (`t58_a_worker_that_panics_leaves_the_collector`).
- A `thread.spawn` that cannot start the thread names the return code, and frees
  the spawn (`t60_a_failed_pthread_create_names_the_return_code`).
- A panic on the main thread runs no drop, and the process ends at the panic
  (`t69_a_main_thread_panic_runs_no_drop`).

## Tests

The fatal paths are covered by the `enum_tag.rs` tests named above, and by the
managed fixtures in `kelpc/tests/managed/tidepool_s0/` and
`kelpc/tests/managed/tidepool_s1/`. Their `expected.txt` files give the output each
one must print.
