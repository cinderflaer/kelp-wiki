---
title: "Methods and receivers"
description: "Source section - syntax.md \u00a78."
isPublished: true
tags: "language"
---
Source section:
[`syntax.md` §8](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

A method is a function whose first parameter is a receiver, written
`Type.name`:

```kelp
datac Counter(val id: i32, var count: i32)

fun Counter.total().R: i32 = id + count          // shared receiver
fun mut Counter.bump() {                          // exclusive receiver
    count += 1
}
```

Calling is ordinary postfix syntax:

```kelp
var c = Counter(id = 1, count = 0)
print(c.total())
c.bump()
print(c.total())
```

## Rules

- Inside the method, fields are read and written **by their bare names**. `self`
  also works as the whole receiver, for the rare method that needs to hand the
  value on (`self` is an ordinary identifier, not a keyword).
- `fun Type.name()` takes a **shared** borrow of the receiver, so it may be
  called on a `val` binding.
- `fun mut Type.name()` takes an **exclusive** borrow, so the receiver must be
  reachable mutably: a `var` binding, a `mut` parameter, or a field of one.
  Calling it on a `val` binding fails with `cannot borrow 'c' as exclusive`.
- Passing a receiver to a method does not move it: the receiver is always
  borrowed, which is why there is no `fun move Type.name()`.
- `self` inside `fun mut T.m()` is a `&mut T`: a pointer, and `Copy`, so naming a
  field and then calling another method on `self` is legal.

## Return types that borrow

A function whose `.R: T` is a borrow must return something derived from its
**first reference parameter**. For a method that means the receiver, which is why
accessors like these are written as methods:

```kelp
fun Row.get(i: usize).R: &str = fields.get(i).as_str()
fun Json.as_str().R: &str {
    if let Str(s) = self {
        return s.as_str()
    }
    panic("json.as_str: value is not a string")
}
```

A *payload bound by a pattern* counts as derived from the scrutinee it came out
of, which is why the second function above type-checks.

One consequence to know about: **a call that returns a borrow of its receiver
cannot be made on a temporary**, because the temporary would be freed before the
borrow could be used.

```kelp
// error: this call returns a borrow of its parameter 'self'
print(set.union(a, b).len())

val u = set.union(a, b)     // bind it first
print(u.len())
```

## Builtin methods

`String`, `Bytes`, `View`, `List`, `Map` and `Box` have compiler-provided
methods: `String.push_str`, `List.push`, `n.to_u64` and so on. They are listed in
[Text](/language/text), [Collections](/language/collections) and
[Standard library](/stdlib).

## Generic receivers

A receiver method on a generic type writes the type's own parameters, in order:

```kelp
datac Pair<A, B>(val first: A, var second: B)

fun Pair<A, B>.first_of().R: A = first
fun mut Pair<A, B>.replace_second(v: B) { second = v }
```

- The parameters must be exactly the type's, in order: a rename would make the
  body's `T` mean something the declaration does not say.
- The type arguments are the receiver's own instantiation, so `p.first_of()` on a
  `Pair<i32, String>` is instantiated once for `A = i32, B = String`.
- A method cannot add type parameters of its own beyond the type's.
- **An `enum` carries no methods in v1**, generic or not. Write a free function
  over the instantiation instead, as `std/option` does:

  ```kelp
  fun is_some<T>(o: &Option<T>).R: bool = when o {
      Some(_) -> true
      None -> false
  }
  ```

## Free functions versus methods

A method is sugar for a function whose first parameter is the receiver, so the
two are interchangeable at the call site's convenience. The standard library is
deliberately mixed: `str.len(s)` and `str.eq(a, b)` are free functions (they read
as operators), while `List.push(v)` and `String.push_str(s)` are methods (they
mutate their receiver).

## See also

- [datac and enum](/language/data-types)
- [Return types and `return`](/language/returns)
- [Generics and type parameters](/language/generics)
- [Ownership and borrowing](/language/ownership)
- [Functions](/language/functions)
