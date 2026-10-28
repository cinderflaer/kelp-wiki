---
title: "Owned trait objects: `Box<dyn Trait>`"
description: "Box<dyn Name> is an owned trait object. A Box<T> coerces to it, calls go through a vtable, get() borrows a &dyn. There are no upcasts or take()."
isPublished: true
tags: "language"
---
[Traits](/language/traits) gave a trait object a *borrowed* spelling, `&dyn Name`.
`Box<dyn Name>` is the owned one: a value that owns a heap allocation, knows
which trait's methods it can answer, and knows how to drop what it points at. It
is the way to keep several different types behind one trait in a `List`, a field
or a return value.

Source: [`design/traits` §12](/design/traits).

## An example

```kelp
trait Shape {
    fun Self.area() => i64
    fun Self.name() => str
    fun mut Self.grow(by: i64)
}

datac Square(var side: i64)
datac Rect(var w: i64, var h: i64)

impl Shape for Square {
    fun Self.area() => i64 = self.side * self.side
    fun Self.name() => str = "square"
    fun mut Self.grow(by: i64) {
        self.side += by
    }
}

impl Shape for Rect {
    fun Self.area() => i64 = self.w * self.h
    fun Self.name() => str = "rect"
    fun mut Self.grow(by: i64) {
        self.w += by
        self.h += by
    }
}

fun make(square: bool) => Box<dyn Shape> {
    if square {
        return Box.of(Square(side = 3))
    }
    return Box.of(Rect(w = 2, h = 5))
}

fun describe(s: &dyn Shape) {
    print("${s.name()} ${s.area()}")
}

fun main() {
    var shapes: List<Box<dyn Shape>> = List.empty()
    shapes.push(make(square = true))
    shapes.push(make(square = false))
    var total: i64 = 0
    var i: int = 0
    while i < shapes.len() {
        total += shapes.get(i).area()
        i += 1
    }
    print(total)
    describe(shapes.get(1).get())
    var one = make(square = false)
    one.grow(1)
    describe(one.get())
    print("end")
}
```

It prints:

```
19
rect 10
rect 18
end
```

- `Box.of(Square(side = 3))` builds a `Box<Square>`, and **returning it where a
  `Box<dyn Shape>` is expected coerces it**. The coercion moves the box: the
  allocation `Box.of` made becomes the trait object's allocation, with no copy.
- `shapes.get(i).area()` calls through the vtable. `19` is `9 + 10`.
- `shapes.get(1).get()` borrows a `&dyn Shape` out of the box, which is how a
  boxed shape is passed to a function taking `&dyn Shape`.
- `one.grow(1)` is a `mut Self` method, so the receiver has to be a writable
  place: here a `var`.
- `Rect` has no user [`drop`](/language/drop). A type with a drop is a resource,
  and a resource cannot be the payload of a `Box` in a hosted build, so the
  boxed types here have none. See [Common refusals](/memory/refusals).

## Where the coercion happens

A `Box<T>` coerces to `Box<dyn Name>` wherever the compiler knows the expected
type: a call argument, a typed `val` or `var`, a `return`, a `datac` or `enum`
field initializer, and a container's element argument (`shapes.push(...)`). The
operand must be a `Box<T>` whose `T` implements `Name`:

```
error: expected 'Box<dyn Shape>', found 'Box<i32>': 'i32' does not implement 'Shape', so write 'impl Shape for i32' first
```

A `Box<dyn Name>` coerces only to the same `Box<dyn Name>`; there is no upcast to
a supertrait object.

## The methods a `Box<dyn Name>` has

- Every method of the trait, through the vtable, including `mut Self` methods on
  a writable place. A call through a `&Box<dyn Name>` or `&mut Box<dyn Name>`
  works too.
- `get()`, which yields a `&dyn Name` borrowed from the box (a second view, not a
  second owner).
- `is_empty()`, and `Box.empty()` for a box that holds nothing. `get()` on an
  empty one panics, as it does for a `Box<T>`.

`take` and `set` are refused, because they would have to move an unsized value in
or out:

```
error: 'Box<dyn Shape>.take' is not allowed: the concrete type behind an owned trait object is erased, so no sized value can be moved in or out; borrow the trait with 'get()' and call its methods, or keep the boxed type concrete
```

## Representation and drop

A `Box<dyn Name>` is two machine words: the address of the heap value and the
address of the same read-only vtable a `&dyn Name` carries, extended with a drop
entry and the type's size and alignment. It is **not `Copy`**: it owns the
allocation. It is a legal field, `List` element, by-move parameter, return type
and local, and the ordinary drop points apply (block end, before a `return`,
reassignment of a `var`, a container's element drop). There is no runtime type
tag: the box carries a method set and the ownership of the storage, not a dynamic
type.

**Status on current `main`.** The checker classifies a `Box<dyn Name>` as declared, not as
memory, so a `Box<dyn Name>` is refused in a `List` element, a `Map` key or value, and a
thread argument or result. The message has the form `'Box<dyn Shape>' cannot be a List
element in a hosted build: its declaration was not found, so it cannot be classified as
memory`. A concrete type with a destructor is a resource, so it is refused as the payload
of a `Box`, in the form `'Circle' cannot be the payload of a Box in a hosted build:
'Circle' is a resource, ...`. The examples on this page that put a boxed trait object in a
`List`, or that box a type with a destructor, do not build on `main`.

## Threads

A `Box<dyn Name>` is an owned value with no borrow in it. On current `main`, however,
the checker refuses it as a thread argument (see the status note above), so a worker
cannot receive one yet. A `&dyn Name` is a borrow of a frame local and is
refused:

```
error: 'thread.spawn' cannot send '&dyn Shape': a borrowed trait object points at a value the frame owns, and the worker outlives that frame; move an owned 'Box<dyn Shape>' in instead, or share a 'pd' value
```

## Refusals

- **Object-unsafe traits**, the same set `&dyn` refuses: a method returning
  `Self`, a parameter other than the receiver that mentions `Self`, two methods
  of one name.

  ```
  error: 'Box<dyn Maker>' is not allowed: method 'make' returns 'Self', and a trait object does not know the concrete type it would build
  ```

- **A generic trait** and **a trait with an associated type**
  ([Generic traits](/language/generic-traits), [Associated types](/language/associated-types)).
- **`Box<dyn A + B>`.** A trait object names one trait; declare a trait that has
  `A` and `B` as supertraits.

  ```
  error: `dyn` names one trait: write `dyn A`, and make a trait that combines them (`trait Both: A + B { ... }`) when both sets of methods are wanted
  ```

- **A bare `dyn Name`** outside `Box<...>` and `&`.
- **Upcasting** to a supertrait object.
- **Printing, comparing, hashing, or using a `Box<dyn>` as a `Map` key.**
- Moving a box's contents out piecemeal is the ordinary partial-move refusal, and
  reading a moved box is `use of moved value`.

## What the compiler does not check

Nothing checks that two vtables of one trait agree beyond the single routine that
lays them out, and nothing checks that a concrete type's methods match the
trait's intent. The recorded size and alignment entries are emitted but only a
freestanding allocator hook reads them; a freestanding image may use
`Box<dyn>` with the allocator pair the project supplies
([Freestanding mode](/language/freestanding)).

## See also

- [Traits and static dispatch](/language/traits)
- [Ownership and borrowing](/language/ownership)
- [User `Drop`](/language/drop)
- [Collections](/language/collections) for `Box<T>`
