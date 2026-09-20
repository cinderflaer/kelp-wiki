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
```

## Which one

- `val` cannot be assigned after the declaration.
- `var` can.
- Both require an initializer: the grammar is `val`/`var` `name` [`: type`] `=`
  `expr`.

Mutability is a property of the *path*, and a `var` binding is only the first
step. A `datac` field is assignable only when both of these hold:

1. the field is declared `var` in the `datac`, and
2. the path to it is mutable, which means a `var` binding, a `mut` parameter, or
   a field of one.

Failing either condition is its own error. The same rule decides which methods may
be called: `fun mut Type.name()` needs a mutable path, so it fails with
`cannot borrow 'c' as exclusive` on a `val` binding
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
- Nothing infers through an empty container. `List.empty()` and `Map.new()` need
  the element or key type on the binding:
  `var xs: List<i32> = List.empty()` ([Collections](/language/collections)).
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

## See also

- [Types](/language/types)
- [Ownership and borrowing](/language/ownership)
- [Constants and passdowns](/language/passdowns)
- [Pitfalls](/language/pitfalls)
