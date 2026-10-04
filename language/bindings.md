---
title: "Bindings and assignment"
description: "Source section - syntax.md \u00a74. `val` and `var`, where the type comes from, what an assignment does to an owned value, and which paths may be written."
isPublished: true
tags: "language, ownership"
---
Source section:
[`syntax.md` §4](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

A `val` or `var` statement binds a name inside a function body. Top-level names are
`const` and `pd` instead ([Constants and passdowns](/language/passdowns)), because
the parser allows only `impl`, `const`, `pd`, `datac`, `enum` and `fun` at file
scope.

```kelp
val n = 10               // immutable binding, type inferred
var total: i64 = 0       // mutable binding, explicit type
total += n               // compound assignment: total = total + n
val (lo, hi) = min_max(xs)   // destructuring: one binding per tuple position
```

## Which one

- `val` cannot be assigned after the declaration.
- `var` can.
- Both require an initializer: the grammar for an ordinary binding is
  `val`/`var` `name` [`: type`] `= expr`. A binding whose name is replaced by a
  parenthesized pattern takes one tuple apart instead (see below).

Mutability is a property of the *path*, and a `var` binding is only the first
step. A `datac` field is assignable only when both of these hold:

1. the field is declared `var` in the `datac`, and
2. the path to it is mutable, which means a `var` binding, a `mut` parameter, or
   a field of one.

Failing either condition is its own error. The same rule decides which methods may
be called: `fun mut Type.name()` needs a mutable path, so it fails with
`cannot assign to 'c': not declared 'var'` on a `val` binding
([Methods and receivers](/language/methods)).

```kelp
datac Counter(val id: i32, var count: i32)

val a = Counter(id = 1, count = 0)
a.count = 5              // error: the binding `a` is not a var

var b = Counter(id = 1, count = 0)
b.count = 5              // ok: var binding and var field

var c = Counter(id = 1, count = 0)
c.id = 5                 // error: the field `id` is declared val
```

## Where the type comes from

- The type is inferred from the initializer, or written after `:`.
- An empty container takes its element type from the first operation that has to
  know it: `var xs = List.empty()` followed by `xs.push(1)` is a `List<i32>`, a
  `Map` takes its key and its value from the first `insert`, and a `Box` its
  element from `set`. Write the type on the binding
  (`var xs: List<i32> = List.empty()`) when nothing decides it, which is what a
  container that is only ever measured (`xs.len()`) hits
  ([Collections](/language/collections)).
- An integer literal takes the type its context requires, and `i32` when nothing
  determines it ([Lexical structure](/language/lexical)). There is no implicit
  numeric conversion afterwards, so the annotation is a real decision and not a
  formatting choice.
- A **character** literal follows the same rule (and is `char` when nothing asks
  for an integer), while a **byte** literal is a `u8` whatever the context asks
  for: `val nl = b'\n'` needs no annotation, and `val n: i64 = b'x'` is refused
  rather than widened ([Lexical structure](/language/lexical)).

## Assignment

Assignment to an owned binding moves the new value in and drops the old one:

```kelp
var name = String.from_str(s = "first")
name = String.from_str(s = "second")   // the first String is freed here
```

That is how a recursive structure is rebuilt in a loop, and it is also why the
left side must be mutable: the old value has to be dropped
([Ownership and borrowing](/language/ownership)).

Compound assignment exists for `+`, `-`, `*`, `/` and `%`. It desugars to a read,
the operation, and a write, so it obeys the same mutability and borrow rules as
those three steps written out.

```kelp
var total: i64 = 0
total += 7          // total = total + 7
total %= 3          // total = total % 3
```

There are no compound forms for the bitwise operators. `~`, `&`, `|`, `^`, `<<`
and `>>` are expressions only
([Operators and expressions](/language/expressions)).

## Destructuring a tuple

A binding may take one tuple value apart in the same statement
([Types](/language/types) has the type):

```kelp
val (lo, hi) = min_max(xs)      // one binding per position
var (a, b) = (1, 2)             // every position is a `var`
val (_, text) = read_pair()     // `_` ignores a position
val ((x, y), z) = corners()     // a nested tuple takes a nested pattern
```

- The number of positions the pattern writes has to equal the number of
  elements the tuple has; a pattern written for another arity is refused with
  both counts.
- `_` ignores a position instead of binding it. What it holds stays in the value
  that was destructured, so an owned element an `_` ignores is freed by that
  value's own drop.
- `val` and `var` mean what they mean on an ordinary binding, for every
  position: `var (a, b) = ...` makes both `a` and `b` assignable.
- **A destructuring binding takes no written type.** `val (a, b): (i32, i32) = ...`
  is refused, because one written type for several positions could not be checked
  against the positions it names. Bind the whole value first when its type needs
  writing: `val p: (i32, i32) = ...`, then `val (a, b) = p`.
- The initializer is moved into the binding, exactly as `val p = place` takes a
  place, and each position is then read out of that value. The whole value is
  bound once, so a second binding of the same place is a use of a moved value,
  and two positions that write one name are ordinary shadowing. That is the
  partial move [Ownership and borrowing](/language/ownership) states.
- An initializer that is a borrow of a tuple binds every `Copy` position and
  refuses an owned one; that is the rule a field of a borrow already follows. The
  initializer has to be a tuple at all: `val (a, b) = 7` is refused by name.

## See also

- [Types](/language/types)
- [Ownership and borrowing](/language/ownership)
- [Constants and passdowns](/language/passdowns)
- [Pitfalls](/language/pitfalls)
