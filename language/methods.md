---
title: "Methods and receivers"
description: "How methods are declared with Type.name, when a receiver is shared or mut, how self works, and the rules for returning borrows from methods."
isPublished: true
tags: "language"
---
Source: [`syntax.md` §8](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

A method is a function whose first parameter is its receiver. You write it as
`Type.name`:

```kelp
datac Counter(val id: i32, var count: i32)

fun Counter.total().return: i32 = id + count   // shared receiver
fun mut Counter.bump() {                   // exclusive receiver
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
  is the whole receiver, for a method that needs to pass the value on.
- `fun Type.name()` takes a **shared** borrow of the receiver, so it may be
  called on a `val` binding.
- `fun mut Type.name()` takes an **exclusive** borrow, so the receiver must be
  reachable mutably: a `var` binding, a `mut` parameter, or a field of one.
  Calling it on a `val` binding fails with `cannot assign to 'c': not declared
  'var'`, where `c` is the binding's name.
- Passing a receiver to a method does not move it: the receiver is always
  borrowed, which is why there is no `fun move Type.name()`.
- An **exclusive receiver's borrow starts after its own arguments are checked**,
  so an argument may read the same container:

  ```kelp
  counts.insert(key = k, v = counts.get_or(key = k, fallback = 0) + 1)
  xs.insert(0, xs.get(0) + 1)
  ```

  Before this rule, each of these needed a temporary. The deferral allows reading
  and shared-borrowing the receiver. Moving it, or borrowing it exclusively again
  inside the argument list, is still a conflict. A shared borrow of the receiver
  that is still live when the exclusive borrow starts is refused. For example,
  `p.copy_from(p)` fails with `cannot borrow 'p' as exclusive: already borrowed as
  shared`.
- Inside `fun mut T.m()`, `self` is a `&mut T`. It is a pointer and it is `Copy`,
  so you can name a field and then call another method on `self`.
- A **concrete `enum`** may declare a receiver method too, and a call on a value of
  the enum type resolves it: `val s = Shape.Empty`, then `s.label()`. A receiver
  that builds the variant names a type rather than a value, so `Shape.Empty.label()`
  is refused with `an 'enum' method is called on a value, not on a variant path`:
  bind the variant first.
- A method declared in a `trait`, and the method that implements it in an `impl`
  block, write the receiver as `Self`, as in `fun Self.area()`. Everywhere else,
  the receiver names its type ([Traits and static dispatch](/language/traits)).

## Return types that borrow

A function whose `.return: T` is a borrow must return something derived from its
**first reference parameter**. For a method that means the receiver, which is why
accessors like these are written as methods:

```kelp
fun Row.get(i: usize).return: &str = fields.get(i).as_str()
fun Json.as_str().return: &str {
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

The same case appears one projection deeper, and there it is not an error: a field
of a call's result (`mkName().name`) has no storage of its own either, but the
compiler stages the temporary for the length of one call, so reading it or
passing it as a borrow works (`print(mkName().name.len())`, `take(mkName().name)`).
What it cannot do is hand the borrow back (`mkName().name.as_str()` needs the same
binding) or have its address taken (`val r = &mkName().name` is `cannot borrow a
temporary value`).

## Builtin methods

`String`, `Bytes`, `View`, `List`, `Map` and `Box` have compiler-provided
methods: `String.push_str`, `List.push`, `n.to_u64` and so on. They are listed in
[Text](/language/text), [Collections](/language/collections) and
[Standard library](/stdlib).

## Generic receivers

A receiver method on a generic type writes the type's own parameters, in order:

```kelp
datac Pair<A, B>(val first: A, var second: B)

fun Pair<A, B>.first_of().return: A = first
fun mut Pair<A, B>.replace_second(v: B) { second = v }
```

- The parameters must be exactly the type's, in order: a rename would make the
  body's `T` mean something the declaration does not say.
- The type arguments are the receiver's own instantiation, so `p.first_of()` on a
  `Pair<i32, String>` is instantiated once for `A = i32, B = String`.
- A method may add type parameters of its own, after its name
  (`fun Pair<A, B>.map_first<C>(...)`). A method may also be declared on a generic
  `enum` (`fun Opt<T>.is_has()`). Both are inferred at the call
  ([Generics](/language/generics)).

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
- [Traits and static dispatch](/language/traits)
- [Ownership and borrowing](/language/ownership)
- [Functions](/language/functions)
