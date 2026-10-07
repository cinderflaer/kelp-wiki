---
title: "Associated types"
description: "A trait may declare `type Item` and each impl binds it; a bounded type parameter reaches it as `I::Item` and a trait body as `Self::Item`. Resolved at every instantiation, so dispatch stays static. No defaults, consts, GATs or equality bounds."
isPublished: true
tags: "language"
---
Source section:
[`plan/traits.md` §10](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/traits.md).

A trait may name a **type** that each impl supplies, so the trait can promise
"I produce a `next` value" without promising what that value is. The trait
declares `type Item`, the impl binds it with `type Item = i32`, and generic code
that has the trait as a bound reaches the bound type as `I::Item`. Nothing about
dispatch changes: `I::Item` is a concrete type at every instantiation, exactly
as a type parameter is, so neither backend learned a new lowering and a
freestanding image may use one. The standard iterator protocol
([Iterators](/language/iterators)) is the main user.

## Declaring and binding

```kelp
trait Source {
    type Item
    fun mut Self.next().return: option.Option<Self::Item>
}
```

The trait body may declare one or more associated types, before, between or
after its methods. An associated type is a bare name, and a trait may not repeat
one. Each `impl` must bind **every** associated type its trait declares, as
`type Name = Type`, and may not bind one the trait does not declare. Inside the
trait, and inside an impl's own methods, `Self::Item` is the type the impl
bound.

This program has two impls of one trait that bind `Item` to different types, and
one generic function that returns whichever the argument's impl chose:

```kelp
impl "std/option"

trait Source {
    type Item
    fun mut Self.next().return: option.Option<Self::Item>
}

datac Countdown(var n: i32)

impl Source for Countdown {
    type Item = i32
    fun mut Self.next().return: option.Option<i32> {
        if self.n <= 0 {
            return option.Option.None
        }
        self.n -= 1
        return option.Option.Some(value = self.n + 1)
    }
}

datac Words(var left: i32)

impl Source for Words {
    type Item = String
    fun mut Self.next().return: option.Option<String> {
        if self.left <= 0 {
            return option.Option.None
        }
        self.left -= 1
        return option.Option.Some(value = "word")
    }
}

fun first_of<S: Source>(s: mut S).return: option.Option<S::Item> {
    return s.next()
}

fun main() {
    var c = Countdown(n = 3)
    var w = Words(left = 1)
    val a = first_of(&mut c)
    val b = first_of(&mut w)
    when a {
        Some(v) -> print(v)
        None -> print("empty")
    }
    when b {
        Some(s) -> print(s)
        None -> print("empty")
    }
}
```

It prints, on the LLVM backend and under `KELPC_ORACLE=c` alike:

```
3
word
```

`first_of<S: Source>` writes `S::Item` in its return type. For `Countdown` that
is `i32` and for `Words` it is `String`, so the two `when` arms bind an `i32`
and a `String`. The `S::Item` is resolved from the impl the concrete argument
names, once per instantiation.

## Where a projection may be written

- `Self::Item` in a trait method signature, in a default method's body, and in
  the signatures of an impl's own methods.
- `T::Item` wherever the type parameter `T` is in scope in a generic function:
  a parameter, a return type or a local.
- A projection needs a bound. `S::Item` needs `S` to carry a bound whose trait
  declares `Item`; a projection through a parameter with no such bound is
  refused where it is written:

  ```
  error: in 'pick<A>': 'I::Item' is not a known associated type: bind 'I' with a trait that carries 'type Item' ('trait ... { type Item }'), so the projection names the type an impl supplies
  ```

## A bound on the associated type

`type Item: Named` limits what an impl may bind. The bound is checked at every
impl, so an impl whose binding does not implement the named trait is refused:

```
error: 'type Entry = Item' in 'impl Repo for Store' does not satisfy the bound 'type Entry: Named': 'Item' does not implement 'Named', which the trait requires of every binding
```

Several bounds join with `+` (`type Item: Named + Other`). Because a generic
function's body is checked once per concrete type, a method of the bound is
callable on a `S::Item` value without any further machinery.

## Refusals

Each of these is a compile error where it is written:

- **A missing binding, an extra binding, a duplicate binding.** The message names
  the trait and the type:

  ```
  error: trait 'Src' declares 'type Out', and 'impl Src for A' does not bind it: add 'type Out = <concrete type>' to the block
  error: 'type Out' is not declared by trait 'Src': an 'impl' binds exactly the trait's associated types, so remove it or add 'type Out' to the trait
  ```

- **A default** (`type Item = i32` inside the trait). Every impl must bind it:

  ```
  error: a default associated type is not in this slice: write 'type Item' in the trait and bind it in every 'impl' ('type Item = i32'), because a default type would let an impl inherit a type it never names
  ```

- **An associated const** (`const N: i32` inside a trait):

  ```
  error: associated consts are not in this slice: a trait declares methods and associated types only
  ```

- **A generic associated type** (`type Item<T>`):

  ```
  error: a generic associated type is not in this slice: 'type Item' declares a plain type, so parameters wait for a later slice
  ```

- **An equality constraint in a bound** (`I: Iterator<Item = i64>`). Bound the
  parameter with the trait and name the concrete type where it is used:

  ```
  error: an equality constraint on an associated type ('iter.Iterator<Item = i32>') is not in this slice: bound the parameter with the trait ('iter.Iterator') and name the concrete type where it is used ('I::Item'), rather than fixing it in the bound
  ```

- **A trait object of a trait that declares an associated type** (`&dyn`,
  `Box<dyn>`). The erased value has no single `Item` to name, so such a trait is
  not object safe; use a bounded type parameter.
- **A generic trait that also declares an associated type** (`trait Name<T> { type
  Item }`), which is refused by name.

## What the compiler does not check

- An impl's binding is a type like any other. Nothing relates it to the types an
  impl's methods return beyond the signature check against the trait, so a trait
  whose method returns `Option<Self::Item>` is checked at that signature and no
  further.
- A bound on an associated type is checked at the impl and nowhere else, and a
  generic function that is never instantiated is never checked, exactly as a
  bound on a type parameter is not.
- Two impls of one trait bind their associated types independently.

## See also

- [Traits and static dispatch](/language/traits)
- [Iterators, `for` and `break`](/language/iterators)
- [Generic traits, `From` and `?` conversion](/language/generic-traits)
- [Generics and type parameters](/language/generics)
