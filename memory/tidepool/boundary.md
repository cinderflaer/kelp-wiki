---
title: "Tidepool: the boundary"
description: "Where a manual block's value may and may not go: the compile-time refusals for a block box, a List or String made in a block, a closure or a spawned thread, each with its exact message and the test that pins it."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: the boundary

A manual block frees its element when the block ends, so nothing that outlives
the block may refer to the element or to memory the block cannot free. The
compiler enforces this at build time. This page lists the refusals, the message
each one prints, and the test that pins it. The rules are the ones in
[Tidepool: safety rules](/memory/tidepool/safety-rules).

The checks are in `kelpc/src/infer/generics.rs` (the messages for a block value)
and in `kelpc/src/borrowck.rs` (the manual block regions a function declares).
`kelpc/src/escape.rs` describes an escape analysis that no other module of
`kelpc/src` names, so the messages on this page do not come from it.

## A block value leaves its block

A block value is the element, or a `box()` of it, that a block made. It is
refused when it reaches a place outside its block:

| Refused form | Message (abridged) | Fixture |
| --- | --- | --- |
| moved into a binding, parameter or other value outside the block | `block value 'cell' cannot be moved out of block 'request' into 'copy'` | `block_box_escapes.kp` |
| stored in a variable declared outside the block | `block value 'cell' cannot be stored in 'keep', which is declared outside block 'request'` | `block_box_stored_outside.kp` |
| stored in a List, Map or Box that is shared-pool memory | `block value 'cell' cannot be stored in 'list', because 'list' is shared-pool memory that can outlive block 'request'` | `block_box_stored_in_list.kp` |
| returned as the block's own value | `block value 'cell' cannot leave block 'request' as the value of its block` | `block_box_returned_as_value.kp` |
| passed as a call argument | `block value 'cell' cannot be moved out of block 'request' into the parameter 'n'` | `block_box_moved_into_call.kp` |

Each message is produced in `kelpc/src/infer/generics.rs`, at the lines that
build the store, leave, move and call wordings.

## A closure, a scoped block or a thread captures a block value

| Refused form | Message (abridged) | Fixture |
| --- | --- | --- |
| a `fun` literal that captures the value | `this closure captures block value 'cell', so its environment would be shared-pool memory` | `block_box_captured_by_closure.kp` |
| a scoped block that captures it | `scoped block captures block value 'cell', which would leave block 'request'` | `block_box_captured_by_scoped.kp` |
| a spawned thread's entry that captures it | `block value 'cell' cannot be passed to a spawned thread` | `block_box_captured_by_spawn.kp` |

## Memory made inside a block

A `List` or a `String` made inside a block is shared-pool memory. The block cannot
free it, so it is refused where it is made:

- `a List made in block 'request' is shared-pool memory, so the block cannot free it`
  (`block_list_made_in_block.kp`);
- `a String made in block 'request' is shared-pool memory, so the block cannot free it`
  (`block_string_made_in_block.kp`).

The element of a block must be a scalar or a `datac` of scalars. A block that
would hold a `String` is refused: `the block 'request' cannot hold 'String': its
element must be a scalar or a datac of scalars` (`block_element_not_scalar.kp`).

## A box used outside the rules for boxes

| Refused form | Message (abridged) | Fixture |
| --- | --- | --- |
| `name.box()` outside its block | `'a.box()' is valid only inside the block 'a'` | `block_box_outside_its_block.kp` |
| a box not bound by `let` | `a block box from 'request.box()?' must be bound by a 'let' in its block` | `block_box_not_bound_by_let.kp` |
| a second box from one block | `the block 'request' already has a box: a second 'request.box()' would need a second slot` | `block_box_twice.kp` |
| a field read without `get()` | `block box 'cell' has no field 'value': its element is read through 'get()'` | `block_box_field_without_get.kp` |

## Names and results

| Refused form | Message (abridged) | Fixture |
| --- | --- | --- |
| two blocks with one name in a function | `the block 'a' is already declared in this function` | `block_name_twice.kp` |
| a `let` that shadows a block name | `the block 'a' shares its name with a 'let' in this function` | `block_name_shadowed_by_let.kp` |
| a block result used neither with `?` nor with `when` | `block 'request' can fail to start, and its result is not used` | `block_region_not_built.kp` |
| `?` inside a block in a function that returns `Unit` | `'?' has nowhere to send a failure, because 'main' returns Unit` | `block_try_in_unit_function.kp` |

## Tests

Each fixture above is listed in `kelpc/tests/golden/index.tsv`, and the matching
test is in `kelpc/tests/compile_and_run/boxes_operators.rs`. Tests with names such
as `a_block_box_may_not_be_stored_in_a_shared_list`, `a_closure_may_not_capture_a_block_box`
and `a_spawned_thread_may_not_capture_a_block_box` run the fixtures and check the
message text.
