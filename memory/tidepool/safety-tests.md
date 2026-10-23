---
title: "Tidepool: safety tests"
description: "The tests that check each Tidepool safety rule, with the file and the test name for each, so a reader can find them. Test names are quoted from the files."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: safety tests

This page lists the tests that check the rules on
[safety rules](/memory/tidepool/safety-rules). Each entry gives the file and the test
name, quoted from the file.

## Collector tests

These are in `kelpc/tests/gc/`. `kelpc/tests/gc/mod.rs` includes the other modules, and
the collector's own tests run with `cargo test` in the `kelpc/gc` crate.

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
| the first clearing lands in the pool block the trigger names | `child_first.rs` (the 131041st object, block 97), `t40e_first_clearing_happens_at_the_manifest_trigger` and `t40f_first_clearing_lands_in_the_pool_block_of_the_trigger` | `child_first.rs`, `mod.rs` |

The verifier also runs after every collection of these tests, because the test suite turns
verify mode on (`kelpc/gc/src/verify.rs`).

## Step tests on the collector

`kelpc/tests/tidepool_step0.rs` and `kelpc/tests/tidepool_s1.rs` run programs against the
collector. Some need the collector archive: they are marked `#[ignore]`, and their header
comments say to set `KELP_GC_LIB` to `libkelp_gc.a` and run them with `--ignored`.

| Rule | Test | File |
| --- | --- | --- |
| a worker that panics leaves the collector | `t58_a_worker_that_panics_leaves_the_collector` | `tidepool_step0.rs` |
| a join does not stop a collection | `t61_a_join_does_not_stop_a_collection` | `tidepool_step0.rs` |
| a mutex wait does not stop a collection | `t61_a_mutex_wait_does_not_stop_a_collection` | `tidepool_step0.rs` |
| an rwlock wait does not stop a collection | `t61_an_rwlock_wait_does_not_stop_a_collection` | `tidepool_step0.rs` |
| a loop over caller data polls the collector | `t62_a_loop_over_caller_data_polls_the_collector` | `tidepool_step0.rs` |
| a main-thread panic runs no drop | `t69_a_main_thread_panic_runs_no_drop` | `tidepool_step0.rs` |
| a failed thread creation names the return code | `t60_a_failed_pthread_create_names_the_return_code` | `tidepool_step0.rs` |
| a spawn's environment and argument are roots | `t20_spawn_environment_and_argument_are_rooted` | `tidepool_s1.rs` |
| a spawn's result is a root until the join | `t21_spawn_result_is_rooted_until_join` | `tidepool_s1.rs` |
| a mutex or rwlock value is a root | `t22_a_mutex_value_is_rooted`, `t22_an_rwlock_value_is_rooted` | `tidepool_s1.rs` |
| the counter line is printed at exit | `t55_the_counter_line_is_printed_at_exit` | `tidepool_s1.rs` |
| the counter line comes before a fatal exit | `t80_a_fatal_exit_prints_the_counter_line_first` | `tidepool_s1.rs` |
| a bad `KELP_GC_*` value is noticed and ignored | `t77_a_bad_gc_value_prints_one_line_and_the_default_applies` | `tidepool_s1.rs` |

The projects these tests build are under `kelpc/tests/managed/tidepool_s0/` and
`kelpc/tests/managed/tidepool_s1/`.

## Compile-time tests

The refusal fixtures run on every `cargo test` in `kelpc`. The checks are in
`kelpc/tests/tidepool_step0.rs` and `kelpc/tests/compile_and_run/`:

| Rule | Test | File |
| --- | --- | --- |
| a `static mut` of a heap type is refused | `a_static_mut_of_a_heap_type_is_refused_by_name` | `tidepool_step0.rs` |
| a mutex of a struct of scalars checks clean | `a_mutex_holding_a_struct_of_scalars_checks_clean` | `tidepool_step0.rs` |
| a closure value is refused as a thread argument | `a_closure_value_is_refused_as_a_thread_argument` | `atomics.rs` |
| a closure entry may capture a sender | `a_closure_entry_may_capture_a_sender` | `atomics.rs` |
| a block box may not be stored in a shared list | `a_block_box_may_not_be_stored_in_a_shared_list` | `boxes_operators.rs` |
| a block box may not be captured by a closure, a scoped block or a thread | `a_closure_may_not_capture_a_block_box`, `a_scoped_block_may_not_capture_a_block_box`, `a_spawned_thread_may_not_capture_a_block_box` | `boxes_operators.rs` |
| a `List` or `String` made in a block is refused | `a_list_made_inside_a_block_is_refused_by_name`, `a_string_made_inside_a_block_is_refused_by_name` | `boxes_operators.rs` |
| a block box is read only through `get()` | `a_block_box_field_without_get_is_refused_by_name` | `boxes_operators.rs` |

The golden index `kelpc/tests/golden/index.tsv` records each fixture's expected outcome
and the message it prints. The manifest refusals are its `project_tidepool*` rows.

## Related

- [Safety rules](/memory/tidepool/safety-rules): the rules these tests check.
- [Test plan](/memory/tidepool/test-plan): how the test groups run.
- [The boundary](/memory/tidepool/boundary): the messages the block refusals print.
- [Tidepool memory design](/memory/tidepool): the index.
