---
title: "Tidepool: safety tests"
description: "The tests that check Tidepool's safety rules on main, grouped by the rule each one checks, with the file that holds it and how it is run."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: safety tests

This page lists the tests that check the rules on
[Tidepool: safety rules](/memory/tidepool/safety-rules). Each entry gives the file
and the test name, so a reader can find it. Test names are quoted from the files.

## Collector tests

These are in `kelpc/tests/gc/`, and `kelpc/tests/gc/mod.rs` includes the others.
The collector's own tests run with `cargo test` in the `kelpc` crate.

| Rule | Test | File |
| --- | --- | --- |
| a dead object is filled with `0xA5` in verify mode | `a_dead_object_is_poisoned_in_verify_mode` | `mod.rs` |
| a block is zeroed, rooted and charged until it is freed | `a_block_is_zeroed_rooted_and_charged_until_freed` | `mod.rs` |
| a block past `heap_max` runs one clearing, then fails | `a_block_past_heap_max_runs_a_clearing_then_fails` | `mod.rs` |
| live blocks keep their budget from the pool | `a_pool_run_past_heap_max_is_refused_while_blocks_hold_the_budget` | `mod.rs` |
| an allocation on an unattached thread fails loudly | `allocation_without_attach_fails_loudly` | `enum_tag.rs` |
| a thread that never reaches a safepoint is named | `stop_timeout_names_the_thread_that_did_not_stop` | `enum_tag.rs` |
| a cap with no room reports `out of memory` | `heap_cap_of_256_mib_fails_with_out_of_memory` | `enum_tag.rs` |
| the panic hook receives the out-of-memory message | `panic_hook_receives_the_out_of_memory_message` | `enum_tag.rs` |
| the first clearing lands in the pool block the trigger names | T40a in `child_first.rs`, T40e and T40f in the `trigger_t40` module | `child_first.rs`, `mod.rs` |

The verifier also runs after every collection of these tests, because the test
suite turns verify mode on.

## Compile-time tests

The refusal fixtures run on every `cargo test` in `kelpc`. The checks are in
`kelpc/tests/tidepool_step0.rs` and `kelpc/tests/compile_and_run/`:

| Rule | Test | File |
| --- | --- | --- |
| a `static mut` of a heap type is refused | `a_static_mut_of_a_heap_type_is_refused_by_name` | `tidepool_step0.rs` |
| a mutex of scalars or of a struct of scalars checks clean | `a_mutex_holding_a_struct_of_scalars_checks_clean` | `tidepool_step0.rs` |
| a closure value is refused as a thread argument | `a_closure_value_is_refused_as_a_thread_argument` | `atomics.rs` |
| a block box may not be stored in a shared List | `a_block_box_may_not_be_stored_in_a_shared_list` | `boxes_operators.rs` |
| a block box may not be captured by a closure, a scoped block or a thread | `a_closure_may_not_capture_a_block_box`, `a_scoped_block_may_not_capture_a_block_box`, `a_spawned_thread_may_not_capture_a_block_box` | `boxes_operators.rs` |
| a List or String made in a block is refused | `a_list_made_inside_a_block_is_refused_by_name`, `a_string_made_inside_a_block_is_refused_by_name` | `boxes_operators.rs` |
| a block box is read only through `get()` | `a_block_box_field_without_get_is_refused_by_name` | `boxes_operators.rs` |

The golden index `kelpc/tests/golden/index.tsv` records each fixture's expected
outcome and the message it prints.

## Run tests

Some tests build a managed program and need the collector archive. Those are marked
`#[ignore]` in `tidepool_step0.rs` and `tidepool_s1.rs`. Their header comments say
to set `KELP_GC_LIB` to `libkelp_gc.a` and to run them with `--ignored`.

The tests that check a worker's panic, a blocked join, a lock wait and a long
caller loop are in `tidepool_step0.rs`: `t58_a_worker_that_panics_leaves_the_collector`,
`t61_a_join_does_not_stop_a_collection`, `t61_a_mutex_wait_does_not_stop_a_collection`,
`t61_an_rwlock_wait_does_not_stop_a_collection` and
`t62_a_loop_over_caller_data_polls_the_collector`.
