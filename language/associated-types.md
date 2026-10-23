---
title: "Associated types"
description: "A trait declares a type name such as Item, each impl binds it, and generic code reaches it as I::Item. The type is fixed at every instantiation, so dispatch stays static."
isPublished: true
tags: "language"
---
A trait can name a **type** that each impl supplies. The trait can promise "I
produce a `next` value" without saying what that value is. The impl binds the
type, and generic code reaches it through the bound as `I::Item`.

Source: [`design/traits` §10](/design/traits).

Dispatch does not change. `I::Item` is a concrete type at every instantiation,
just as a type parameter is, so nothing new is lowered and a freestanding image
can use it too. The standard iterator protocol ([Iterators](/language/iterators))
is the main user.

## Declaring and binding

```kelp
trait Source {
    type Item
    fun mut Self.next() => option.Option<Self::Item>
}
```

- A trait may declare one or more associated types, placed anywhere among its
  methods. Each name appears once.
- Each `impl` binds **every** associated type its trait declares, as
  `type Name = Type`. Binding one the trait does not declare is an error.
- Inside the trait, and inside an impl's own methods, `Self::Item` is the type the
  impl bound.

## Example

This program has two impls that bind `Item` to different types. One generic
function returns whichever type the argument's impl chose.

```kelp
impl "std/option"

trait Source {
    type Item
    fun mut Self.next() => option.Option<Self::Item>
}

datac Countdown(var n: i32)

impl Source for Countdown {
    type Item = i32
    fun mut Self.next() => option.Option<i32> {
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
    fun mut Self.next() => option.Option<String> {
        if self.left <= 0 {
            return option.Option.None
        }
        self.left -= 1
        return option.Option.Some(value = "word")
    }
}

fun first_of<S: Source>(s: mut S) => option.Option<S::Item> {
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

It prints:

```
3
word
```

`first_of<S: Source>` returns `S::Item`. For `Countdown` that is `i32`, and for
`Words` it is `String`, so the two `when` arms bind an `i32` and a `String`. The
compiler resolves `S::Item` from the impl of the concrete argument, once per
instantiation.

## Where a projection may be written

- `Self::Item` in a trait method signature, in a default method's body, and in
  the signatures of an impl's own methods.
- `T::Item` wherever the type parameter `T` is in scope in a generic function: in
  a parameter, a return type or a local.
- A projection needs a bound. `S::Item` requires `S` to carry a bound whose trait
  declares `Item`. Without one, the projection is refused where it is written:

  ```
  error: in 'pick<A>': 'I::Item' is not a known associated type: bind 'I' with a trait that carries 'type Item' ('trait ... { type Item }'), so the projection names the type an impl supplies
  ```

## A bound on the associated type

`type Item: Named` limits what an impl may bind. The bound is checked at every
impl. An impl that binds a type which does not implement the named trait is
refused:

```
error: 'type Entry = Item' in 'impl Repo for Store' does not satisfy the bound 'type Entry: Named': 'Item' does not implement 'Named', which the trait requires of every binding
```

Several bounds join with `+` (`type Item: Named + Other`). A generic function's
body is checked once per concrete type, so a method of the bound can be called on
a `S::Item` value without any extra machinery.

## Equality constraints

An equality constraint pins an associated type in a bound on a **function's** or
an **impl's** type parameter:

```kelp
fun total<I: iter.Iterator<Item = i64>>(it: I) => i64 { ... }
```

It is refused on a supertrait and on an associated type's own bound, where it is
written, with a message that names the site.

## Refusals

Each of these is a compile error where it is written:

- **A missing, extra or duplicate binding.** The message names the trait and the
  type:

  ```
  error: trait 'Src' declares 'type Out', and 'impl Src for A' does not bind it: add 'type Out = <concrete type>' to the block
  error: 'type Out' is not declared by trait 'Src': an 'impl' binds exactly the trait's associated types, so remove it or add 'type Out' to the trait
  ```

- **A default**, such as `type Item = i32` inside the trait. Every impl must bind
  it:

  ```
  error: a default associated type is not in this slice: write 'type Item' in the trait and bind it in every 'impl' ('type Item = i32'), because a default type would let an impl inherit a type it never names
  ```

- **An associated const**, such as `const N: i32` inside a trait:

  ```
  error: associated consts are not in this slice: a trait declares methods and associated types only
  ```

- **A generic associated type**, such as `type Item<T>`:

  ```
  error: a generic associated type is not in this slice: 'type Item' declares a plain type, so parameters wait for a later slice
  ```

- **A trait object of a trait that declares an associated type**, such as
  `&dyn Src` or `Box<dyn Src>`. The erased value has no single `Item` to name. Use
  a bounded type parameter (`<T: Src>`) instead.

- **A generic trait that also declares an associated type**, such as
  `trait Name<T> { type Item }`.

## What the compiler does not check

- An impl's binding is an ordinary type. The compiler checks the impl's methods
  against the trait's signatures and nothing further. A trait method that returns
  `Option<Self::Item>` is checked at that signature only.
- A bound on an associated type is checked at the impl and nowhere else. A
  generic function that is never called is never checked, the same as any bound
  on a type parameter.
- Two impls of one trait bind their associated types independently.

## See also

- [Traits and static dispatch](/language/traits)
- [Iterators, `for` and `break`](/language/iterators)
- [Generic traits, `From` and `?` conversion](/language/generic-traits)
- [Generics and type parameters](/language/generics)
