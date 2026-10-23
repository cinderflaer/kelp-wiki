---
title: "Tidepool: failure and recovery"
description: "What a hosted program sees when memory runs out or a thread misbehaves: a manual block that cannot be made returns Err(BlockError.Full), and every other failure stops the process with a named message, with the counter line first when KELP_GC_STATS is set."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: failure and recovery

Tidepool has two kinds of failure. A manual block that cannot be made returns a value,
`Err(BlockError.Full)`, and the program goes on. Every other failure stops the process
with a fatal message. This page lists both kinds. The sizing rules that decide when they
happen are on [the budget](/memory/tidepool/budget).

## Failures that return a value

| Situation | What the program gets | Source |
| --- | --- | --- |
| a manual block does not fit under `heap_max`, even after one clearing | `Err(BlockError.Full)` | `BLOCK_OVER_BUDGET` in `block::alloc` (`kelpc/gc/src/block.rs`) |
| the root table cannot take another slot for a block | `Err(BlockError.Full)` | `BLOCK_ROOT_FULL`, same file |
| a block's chunk cannot be mapped | `Err(BlockError.Full)` | `BLOCK_NO_MEMORY`, same file |

Every status other than `BLOCK_OK` becomes `Full` in `emit_block_box`
(`kelpc/src/codegen_llvm/frame.rs`). A failed block leaves nothing charged and nothing
registered: the collector undoes the mapping and the charge before it returns the
status. A program therefore handles the failure with `when`, as in the fixture
`block_end_to_end.kp`, or passes it on with `?`.

## Failures that stop the process

| Situation | Message | Source |
| --- | --- | --- |
| a shared-pool allocation fails after a clearing | `out of shared-pool memory: heap_max is <n> MiB, <n> MiB was live at the last clearing, and <n> MiB is charged to live blocks`, then `note: keep less data live, or raise heap_max in coral.toml's [target] section` | `out_of_shared_pool` in `kelpc/gc/src/lib.rs` |
| the operating system refuses a mapping | `out of memory` | `map` in `lib.rs` |
| an array's count is above 4294967295 | `array of <n> elements is too large: a shared-pool array holds at most 4294967295 elements` | `array_too_large` in `lib.rs` |
| an array's byte size overflows | `array size overflows: <n> elements of <n> bytes each` | `array_overflows` in `lib.rs` |
| a thread allocates without attaching | `gc: allocation on a thread that is not attached (call kelp_gc_thread_attach before the first allocation)` | `alloc_common` in `lib.rs` |
| a type's alignment is above 8 | `gc: type alignment above 8 is not supported in v1` | `alloc_common` in `lib.rs` |
| a thread does not reach a safepoint in time | `gc: thread <tid> did not reach a safepoint within <n> ms (registry slot <n>); a loop must poll kelp_gc_safepoint or enter native state` | `threads.rs` |
| a collecting thread is not attached | `gc: collecting thread is not attached (call kelp_gc_thread_attach)` | `threads.rs` |

The out-of-memory message is the one a program sees most. Its first number is the cap.
A program that needs more room raises `heap_max` in `[target]`, or keeps less data
live. The cap is set in [settings](/memory/tidepool/settings).

### The counter line

When `KELP_GC_STATS=1` is set, every fatal exit prints the counter line before its
message. `fatal` in `kelpc/gc/src/sys.rs` calls `print_stats_once`, which prints at
most once per process:

```text
kelp-gc-stats: collections=<n> pause_total_us=<n> pause_max_us=<n> roots=<n> charged_bytes=<n>
```

The test `t80_a_fatal_exit_prints_the_counter_line_first` in `kelpc/tests/tidepool_s1.rs`
builds `kelpc/tests/managed/tidepool_s1/t80_fatal_stats_and_oom`, which exhausts the
pool, and checks that the line comes before the panic.

### The out-of-memory hook

A fatal exit calls the hook set through `oom_hook` before it exits (`fatal` in
`sys.rs`). The test `panic_hook_receives_the_out_of_memory_message` in
`kelpc/tests/gc/enum_tag.rs` checks that the hook receives the text.

## Bad settings

A collector variable whose value is not a whole number is ignored with a notice, and the
program goes on:

```text
gc: ignored KELP_GC_STRESS='abc': expected a whole number
```

The notice is printed by `env_usize` in `kelpc/gc/src/lib.rs`. The test
`t77_a_bad_gc_value_prints_one_line_and_the_default_applies` in `kelpc/tests/tidepool_s1.rs`
checks it with the project `kelpc/tests/managed/tidepool_s1/t77_bad_gc_env`.

`KELP_GC_STOP_TIMEOUT_MS=0` is replaced by the default, and the notice is
`gc: KELP_GC_STOP_TIMEOUT_MS must be at least 1`. The default timeout is 10000 ms
(`DEFAULT_STOP_TIMEOUT_MS` in `kelpc/gc/src/state.rs`).

A bad `heap_max` or `[tidepool]` value is not a run-time failure. The compiler refuses it
when it reads `coral.toml`, as [settings](/memory/tidepool/settings) lists.

## Threads

- A worker that panics leaves the collector and detaches
  (`t58_a_worker_that_panics_leaves_the_collector` in `kelpc/tests/tidepool_step0.rs`).
  Its owned locals are dropped on the way out, as the fixture `panic_drop_order.kp` shows.
- A `thread.spawn` that cannot start the thread names the return code
  (`t60_a_failed_pthread_create_names_the_return_code` in the same file).
- A panic on the main thread runs no drop, and the process ends at the panic
  (`t69_a_main_thread_panic_runs_no_drop`). See [drop](/language/drop).

## Tests

The fatal paths are covered by the `enum_tag.rs` tests named above, and by the managed
projects in `kelpc/tests/managed/tidepool_s0/` and `kelpc/tests/managed/tidepool_s1/`.
Each project's `expected.txt` gives the output it must print.

## Related

- [The budget](/memory/tidepool/budget): when the cap is reached.
- [Blocks at runtime](/memory/tidepool/blocks): the status codes of a block.
- [Tooling and release](/memory/tidepool/tooling-release): the environment variables.
- [Common refusals](/memory/refusals): the messages a build prints.
