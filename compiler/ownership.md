---
title: "Ownership and drops"
description: "How kelpc lowers defer, checks moves and borrows, and builds the drop plan. Covers the last-use rule for borrows and the open question about break inside a nested block."
isPublished: true
tags: "compiler"
---
Three parts of the compiler handle ownership.
`defer.rs` lowers `defer` statements into ordinary code before type checking.
`borrowck.rs` checks moves and borrows over the typed IR, and builds the drop plan.
The code generators then read that plan at each point where a value can be dropped.

The language rules are on the [Ownership](/language/ownership) and [Drop](/language/drop) pages.

## Lowering `defer` (`defer.rs`)

`defer::lower` (`defer.rs:35`) runs on each module after it is parsed (`resolve.rs:1709`).
It removes every `defer` statement, so the later passes see only plain code.

Each block keeps its pending actions in a list of `Cleanup` values (`defer.rs:58`).
At the end of the block, the actions run last in, first out.
An exit copies them in ahead of itself:

- a `return` runs the actions of every enclosing block (`Chain::exit`, `defer.rs:74`, and `push_return`, `defer.rs:312`).
  The return value is bound to a temporary first, so the value is computed before the actions run;
- a `break` or `continue` runs only the actions of the current block (`defer.rs:259` to `266`, `push_exit_actions`, `defer.rs:296`).

The lowering refuses these cases with a diagnostic:

- a `?` in the same block as a `defer` (`defer.rs:119` to `138`);
- a `return` inside an action (`defer.rs:161` to `172`);
- a `break` or `continue` inside an action (`defer.rs:174` to `185`);
- a local declared after the `defer` that the action could use (`defer.rs:173`, `refuse_later_locals`).

Because the copies are ordinary statements, a use of a moved value inside an action is reported by the borrow checker at the `defer` line.

### Open question: `break` inside a nested block

A `break` inside an `if` that is inside a loop body does not run the body's `defer` actions.
The `if` block is lowered with the enclosing chain, and a `return` uses that chain.
A `break` uses only the actions of its own block, which is empty for the nested `if` (`defer.rs:259` to `262`).

This follows from reading the code.
No fixture pairs a `defer` with a `break` or `continue`, so it has not been confirmed by a test.
`plan/defer.md` says `break` and `continue` are not statements yet, which is out of date.

## Moves (`borrowck.rs`)

`check_program` (`borrowck.rs:2114`) checks each function (`check_function`, `borrowck.rs:2170`) and returns a `DropPlan` (`borrowck.rs:219`).

- A type is `Copy` when `is_copy` says so (`types.rs:368`).
  Scalars and `&str` are `Copy`. A `datac` or an `enum` is not.
- A bare read of a non-`Copy` local is a move (`use_value_moving`, `borrowck.rs:1154`).
- A field read off an owned local moves that field out, and the local keeps the rest.
  The `Projection` values (`borrowck.rs:163` to `180`) record which parts moved.
- A local that is moved on some paths and kept on others is `MaybeMoved`.
  The moving path clears its slot, so the drop at the end of the block is safe (`codegen_c.rs:2853` to `2875`).

## Borrows

A borrow state is `None`, `Shared(n)` or `Exclusive` (`BorrowKind`, `borrowck.rs:401`).
`start_borrow` (`borrowck.rs:1217` to `1276`) allows any number of shared borrows, or one exclusive borrow with no others.

There are two kinds of borrow:

- **Call-scoped borrows** are arguments of a call.
  `check_call` (`borrowck.rs:3302`) starts all of them before it releases any, so `f(&mut c, &c)` is refused.
  They end when the call returns (`borrowck.rs:3559`).
- **Scope borrows** are bound to a name, for example `val p = &c`, or come from a call that returns a borrow.
  `hold` (`borrowck.rs:1396`) attaches the borrow to the name.

A reference binding records the owners it may borrow from (`set_roots`, `borrowck.rs:843`).
A cursor therefore keeps its owner pinned.

### Last use

A scope borrow ends after the last statement that mentions its name, not at the end of its scope.
`last_use_index` (`borrowck.rs:2411`) finds that statement.
A use inside a loop or an `if` counts as the whole enclosing statement, so the borrow lasts for the loop.
`release_expired` (`borrowck.rs:1610`) releases borrows after each statement.

The effect is that `val first = names.get(0)` followed by `names.push(...)` is accepted once `first` is no longer used.

### Messages

Each conflict is a `BorrowError` with a span.
The main messages are:

- `use of moved value 'x'`
- `cannot move 'x' while it is borrowed`
- `cannot assign to 'x' while it is borrowed`
- `cannot borrow 'x': value was moved`
- `cannot borrow 'x': already borrowed exclusively`
- `cannot borrow 'x' as exclusive: already borrowed as shared`
- `cannot mutate 'path' while iterating over it`
- `cannot return a borrow of 'x': ...`

## The drop plan

An owned local is a binding whose type needs a drop.
`define_owned` (`borrowck.rs:872`) registers it.
Owned `move T` parameters are registered too.
The plan records, for each block, return, `?`, `break`, `continue` and assignment, which owned values must be dropped at that point.

- **Block end.** `pop_scope` (`borrowck.rs:719`) records the live locals of the block.
  A block that always leaves (ends in `return`, `break` or `continue`) records nothing.
  The function body also drops its locals before its parameters.
- **`return`** (`borrowck.rs:2347`) drops the live locals of every enclosing scope, innermost first.
  A returned local is already moved, so it is not dropped.
- **`?`** (`borrowck.rs:2963`) records the same list for the early exit.
- **`break` and `continue`** (`borrowck.rs:2363` to `2376`) drop only the scopes inside the innermost loop.
- **Assignment** to an owned `var` drops the old value after the new value is read and before it is stored (`at_assign`, about `borrowck.rs:3085` to `3131`).

The plan is keyed by span (`borrowck.rs:268` to `277`).
The code generators ask it at each point, through `drops_at_block_end`, `at_return`, `at_assign`, `at_try`, `at_break`, `at_continue` and `moves_at`.
The C backend reads it in `codegen_c.rs` and the LLVM backend in `codegen_llvm.rs`.

### Open question: span keys and copied defers

`defer.rs` copies one action into several exits, and each copy keeps the span of the `defer` statement.
The plan is keyed by span, so the copies share one key.
This page has not confirmed that the copies always get the same drops.

## Tests

- `tests/compile_and_run.rs` covers moves, borrows and defer. Its fixtures are under `tests/fixtures/` with the names `borrow_*`, `nll_*`, `cursor_*`, `defer_*`, `drop_*`, `owned_*` and `move_*`.
- `tests/memory_gate.rs` runs valgrind over the drop fixtures. It is ignored by default.
- `tests/run-sanitizers.sh` runs the drop fixtures under the sanitizers.

## See also

- [Types](/compiler/types)
- [Backends](/compiler/backends)
- [Ownership](/language/ownership)
- [Drop](/language/drop)
- [Statics and defer](/language/statics-and-defer)
