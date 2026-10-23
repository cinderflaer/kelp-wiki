---
title: "Limits of the language"
description: "What Kelp leaves out on purpose, what is not built yet, and the fixed limits the compiler enforces. Each item links to the page that explains the rule."
isPublished: true
tags: "language"
---
Kelp leaves some things out on purpose. Other things are not built yet. This page
lists both, plus the fixed limits the compiler enforces. Each item links to the
page that explains the rule.

Source: [`syntax.md` §17](/design/syntax).
The [roadmap](/meta/roadmap)
tracks the items that are planned.

## Left out on purpose

These are design decisions. None of them is planned.

| Missing | Use instead |
| --- | --- |
| Exceptions and `try`/`catch` | `Option`, `Result`, `?`, and `panic` for failures with no way to recover ([Errors](/language/errors)) |
| A tracing collector for every value | Owners and drops for resources, and a collector only for memory values in a hosted build ([Ownership](/language/ownership), [Memory](/memory)) |
| Macros | Text substitution with `alias` ([Modules](/language/modules#aliases)) |
| `goto` | `break`, `continue`, labels and `return` ([Control flow](/language/control-flow)) |
| `derive` | Write the impl by hand ([Operator traits](/language/operator-traits)) |
| Operator overloading outside `std/ops` | Implement `std/ops` and `fmt.Display` ([Operator traits](/language/operator-traits)) |
| Overloading a user function name | Put the type in the name, as in `pick_i32` and `pick_f64` |
| Lifetime syntax (`'a`) | Borrows end at their last use, and a returned borrow must come from a parameter ([Ownership](/language/ownership)) |
| Undefined-behaviour escape hatch | `unsafe` marks code that the compiler cannot check. It does not allow undefined behaviour ([Unsafe](/language/unsafe)) |
| `async` and coroutines | Threads, with `thread.spawn` and `thread.join` ([Concurrency](/language/concurrency)) |

## Not built yet

These are not part of the language today.

### Traits and generics

- A trait object of a generic trait, such as `&dyn From<i32>`.
- A trait object of a trait with an associated type. A borrowed trait object cannot
  be stored in a field, a container, a return type or a `static`.
- An upcast from `&dyn B` to `&dyn A`.
- An impl for one instantiation, such as `impl Name for Pair<i32, String>`.
- A blanket impl of a trait that takes type arguments, such as `impl<T> Into<U> for T`.
- A bound on an associated type's own declaration, such as
  `type Item: Iterator<Item = i64>`.
- Default values for associated types, generic associated types, and associated
  constants.
- Type parameters on a trait method. A trait method cannot take `<T>`.
- `impl Trait` as a return type. Use a named type parameter or `Box<dyn Trait>`.
- Const parameters on a method, and arithmetic on a const parameter inside a type,
  such as `[T; N + 1]`.

See [Traits](/language/traits), [Generic traits](/language/generic-traits),
[Associated types](/language/associated-types) and
[Const generics](/language/const-generics).

### Ownership and borrows

- Explicit lifetimes, and borrows stored in struct fields or enum payloads.
- Closures that capture a borrow. A closure owns what it captures.
- A `&` stored in a `List`, `Map`, `Box` or array element.
- A scoped block that is stored, returned or put in a container. A block can
  only be passed as an argument to the call it was written in. See
  [Scoped blocks](/language/functions#trailing-blocks-and-scoped-parameters).
- A block that writes through an exclusive capture and returns a borrow. Return an
  owned value instead.

### Functions and names

- Named nested functions. Use a closure, which is a `fun` literal that captures
  bindings from its scope ([Functions](/language/functions#closures)).

### Concurrency

- A select case names its channel as a variable or a field
  ([`std/sync`](/stdlib/sync#select)).
- A panic does not unwind. A panicking worker drops its owned locals and its user
  `Drop` thread arguments, newest first, but not the temporaries it holds, and a
  thread handle that nobody joins leaks its result slot.
- Memory orders other than `SeqCst`. `Relaxed`, `Acquire` and `Release` are reserved.

See [Concurrency](/language/concurrency).

### Foreign code and unsafe

- An `extern "C"` block. Declare each function with `extern fun`
  ([User FFI](/language/externs)).
- Function-pointer types for user externs, and passing a `repr(C)` struct by value.
- `AtomicPtr` and `transmute`.
- Provenance and an address-space model. A range granted under `mmio` allows any
  address reachable from it by arithmetic ([Capabilities](/language/capabilities)).

### Libraries and text

- A borrowing `List.iter()` that yields `&T`. Use `iter.into_iter` or `iter.cloned`
  ([Iterators](/language/iterators)).
- Regular-expression literals. Use [`std/regex`](/stdlib/regex) with a pattern
  string.
- `str.to_upper` and `str.to_lower` change ASCII letters only.

### Networking

- A WebSocket server. [`std/ws`](/stdlib/ws) is a client only.
- WebSocket extensions and subprotocols, and automatic reconnect.

For what the networking and TLS modules support, see [`std/net`](/stdlib/net),
[`std/http`](/stdlib/http) and [`std/tls`](/stdlib/tls).

## Fixed limits

The compiler enforces these numbers. Written code is far from them.

| Limit | Value | Error |
| --- | --- | --- |
| Nesting of expressions, types, blocks and patterns | 200 levels | `... nests more than 200 levels deep` |
| Links in one operator or access chain | 800 | `... is longer than 800 links` |
| Steps while evaluating one `const` | 1,000,000 | `this constant expression did not finish within 1000000 steps` |
| Nested calls while evaluating one `const` | 64 | a diagnostic naming the call depth |
| `[target] cpus` in a freestanding build | 1 to 64 | `must be between 1 and 64` |

See [Front-end fuzzing and parser limits](/tooling/fuzzing) for the parser limits.

## Compile time

The compiler's scaling tests build large generated programs:
long method chains, deeply nested calls, 300-arm `elif` ladders, 200-field
`datac`s and 5,000-element list literals. A step that takes over 20 seconds fails
the test.

A very large array literal is fastest when it is bound directly to a `val`. A
literal passed to a call or returned keeps the slower form, so bind it first. See
[Collections](/language/collections#restriction-the-element-set).

## See also

- [Concurrency](/language/concurrency)
- [Pitfalls](/language/pitfalls)
- [Ownership and borrowing](/language/ownership)
- [Collections](/language/collections)
