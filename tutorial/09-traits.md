---
title: "Traits and generics"
description: "A trait names a behaviour that several types provide, a default method gives a shared body, and a bound lets one generic function work on any type that has the behaviour, with real output."
isPublished: true
tags: "tutorial, language, traits, generics"
---
**You will learn:** how a trait lets different types offer the same method, and how
a generic function accepts any type that implements a trait.

## The program

```kelp
impl "std/fmt"
impl "std/str"

trait Shape {
    fun Self.area().return: f64
    fun Self.describe().return: String {
        val text = fmt.float(self.area(), 1)
        return str.concat("a shape with area ", text.as_str())
    }
}

datac Square(val side: f64)

datac Circle(val r: f64)

impl Shape for Square {
    fun Self.area().return: f64 = self.side * self.side
}

impl Shape for Circle {
    fun Self.area().return: f64 = 3.0 * self.r * self.r
    fun Self.describe().return: String = "a circle"
}

fun total_area<T: Shape>(items: &List<T>).return: f64 {
    var sum = 0.0
    var i: usize = 0
    while i < items.len() {
        sum += items.get(i).area()
        i += 1
    }
    return sum
}

fun main() {
    val sq = Square(side = 2.0)
    val c = Circle(r = 1.0)
    print(sq.describe())
    print(c.describe())

    var squares: List<Square> = List.empty()
    squares.push(Square(side = 1.0))
    squares.push(Square(side = 3.0))
    print(total_area(squares))
}
```

```text
a shape with area 4.0
a circle
10.000000
```

## Declaring a trait

`trait Shape` lists the methods a shape must have. `area` has no body, so every
type that implements `Shape` must write it. `describe` has a body, which is its
default: a type gets that behaviour unless it writes its own.

`impl Shape for Square { ... }` says that `Square` provides the trait. A
`Circle` provides `area` and overrides `describe` with its own text. `Square` uses
the default.

## Using a trait

Methods from the trait are called on values like any other method: `sq.describe()`
and `c.describe()` above. Inside a default method, `self` is the value the method
was called on, so `self.area()` calls the type's own `area`.

## Generic functions with a bound

`fun total_area<T: Shape>(items: &List<T>)` says: `T` stands for any type, but it
must implement `Shape`. The body can call `area()` on each item because the
bound guarantees it. The compiler checks each call site: a `List` of a type that
does not implement `Shape` is a compile error that names the trait.

Each use of `total_area` is compiled for the type it is called with, so there is
no runtime lookup. This is called static dispatch.

## Try it

1. Add a third type, `datac Triangle(val base: f64, val height: f64)`, with an
   `impl Shape` whose `area` is `base * height / 2.0`. Does `describe` need to be
   written? Why?
2. Call `total_area` with a `List<Circle>` and print the result. Then try the same
   call with a `List<i32>` and read the error.

Next: [Closures and iterators](/tutorial/10-closures).
