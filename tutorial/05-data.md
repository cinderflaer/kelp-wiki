---
title: "Tutorial 5: Records, enums and methods"
description: "Chapter 5 of the Kelp tutorial: datac records, enums with payloads, when and if let/elif let matching, receiver methods and the val/var path rule, with the real compiler errors for each mistake."
isPublished: true
tags: "tutorial, language, data"
---
Kelp has two ways to declare your own types: a **record** (`datac`), where every
field exists in every value, and a **tagged union** (`enum`), where exactly one
variant is live. The reference is [datac and enum](/language/data-types) and
[Methods and receivers](/language/methods).

## The program

```kelp
datac Point(val x: i32, var y: i32)

datac Counter(val id: i32, var count: i32)

fun Counter.total().R: i32 = id + count

fun mut Counter.bump() {
    count += 1
}

enum Shape {
    Circle(val r: f64)
    Rect(val w: f64, val h: f64)
    Empty
}

fun Shape.area().R: f64 = when self {
    Circle(r) -> 3.14159 * r * r
    Rect(w, h) -> w * h
    Empty -> 0.0
}

fun describe(s: &Shape) {
    if let Rect(w, h) = s {
        print("rect ${w} by ${h}")
    } elif let Circle(r) = s {
        print("circle of radius ${r}")
    } else {
        print("nothing")
    }
}

fun main() {
    var p = Point(x = 3, y = 4)
    p.y = 10
    print("point ${p.x},${p.y}")

    var c = Counter(id = 100, count = 0)
    c.bump()
    c.bump()
    print("total ${c.total()}")

    val shapes = [Shape.Circle(r = 2.0), Shape.Rect(w = 3.0, h = 4.0), Shape.Empty]
    for s in shapes {
        describe(s)
        print("area ${s.area()}")
    }
}
```

```text
point 3,10
total 102
circle of radius 2.000000
area 12.566360
rect 3.000000 by 4.000000
area 12.000000
nothing
area 0.000000
```

The same text came out of the LLVM backend and the C oracle.

## Records

`datac Point(val x: i32, var y: i32)` declares a record. Each field is `val` (set
once) or `var` (assignable). You construct one with the type's name and **named
arguments**, and read a field with a dot. A `datac` holds owned data only, so a text
field is a `String`, never a `str`, and a record that contains itself has to go through
a `Box` or a `List`.

Writing a field needs two things: the field is `var`, **and** the path to it is
mutable (a `var` binding, a `mut` parameter, or a field of one). Each failure has
its own message:

```kelp
datac Counter(val id: i32, var count: i32)

fun main() {
    var c = Counter(id = 1, count = 0)
    c.id = 5
    print(c.id)
}
```

```text
$ kelpc check c5bad2.kp
error: cannot write to 'id': declared 'val'
  --> c5bad2.kp:5:5
```

(The other half, assigning a field of a `val` binding, reports `cannot assign to
'c': not declared 'var'`, the same text as chapter 2's.)

## Enums and `when`

`enum Shape { ... }` lists variants, each with an optional payload in parentheses.
You build one with `Shape.Circle(r = 2.0)` or `Shape.Empty`. An enum value is owned
and not `Copy`; passing one moves it, unless the parameter is a borrow (`&Shape`).

`when s { ... }` with a scrutinee is how you take one apart. An arm names a
variant and one binding per payload field (`_` ignores one), then `->` and a
value. A `when` over an enum must be **exhaustive**, either with an arm for every
variant or with an `else ->` arm:

```kelp
enum Shape {
    Circle(val r: f64)
    Rect(val w: f64, val h: f64)
    Empty
}

fun area(s: &Shape).R: f64 = when s {
    Circle(r) -> 3.14159 * r * r
    Rect(w, h) -> w * h
}

fun main() {
    print(area(Shape.Empty))
}
```

```text
$ kelpc check c5bad3.kp
error: this 'when' is not exhaustive: 'Empty' of enum 'Shape' has no arm — add an arm, or an 'else' arm
  --> c5bad3.kp:7:30
```

When you care about one or two variants, use `if let`, with `elif let` for a second
pattern and an `else` as the catch-all. `describe` in the program does exactly
that. A payload binds as a copy when it is `Copy` (here the `f64`s), by value out
of an owned place, and as a shared borrow otherwise; `describe` took `&Shape`
and the floats are `Copy`, so nothing was moved.

There are no guards, no literal patterns and no nested patterns: an arm is a variant
name and its bindings, nothing more.

## Methods and receivers

A method is a function whose first parameter is a receiver, written `Type.name`:

- `fun Counter.total().R: i32 = id + count`: a **shared** receiver. Inside, fields
  are read by their bare names (`self` is the whole receiver, and the `Shape.area`
  method used it to `when` on itself).
- `fun mut Counter.bump() { count += 1 }`: an **exclusive** receiver. It needs a
  mutable path to call it.

A call is plain postfix, `c.bump()`. The receiver is always borrowed, never moved:
there is no `fun move Type.name()`. The `val` path rule applies to calls too:

```kelp
datac Counter(val id: i32, var count: i32)

fun mut Counter.bump() {
    count += 1
}

fun main() {
    val c = Counter(id = 1, count = 0)
    c.bump()
    print(c.count)
}
```

```text
$ kelpc check c5bad4.kp
error: cannot assign to 'c': not declared 'var'
  --> c5bad4.kp:9:5
```

A method on an `enum` is
called on a value, not on a variant path: bind `val s = Shape.Empty` first.

## Exercises

1. Replace `Rect` with `Triangle(val base: f64, val height: f64)` and give `Shape`
   an `area` method.
2. Write an `Account` record with an owned `String` owner and a `balance`, and a
   `mut` method `withdraw(amount: i64).R: bool` that refuses to overdraw.

<details>
<summary>Solutions</summary>

1.

```kelp
enum Shape {
    Circle(val r: f64)
    Triangle(val base: f64, val height: f64)
    Empty
}

fun Shape.area().R: f64 = when self {
    Circle(r) -> 3.14159 * r * r
    Triangle(b, h) -> b * h / 2.0
    Empty -> 0.0
}

fun main() {
    val t = Shape.Triangle(base = 6.0, height = 5.0)
    print("area ${t.area()}")
}
```

```text
area 15.000000
```

2.

```kelp
datac Account(val owner: String, var balance: i64)

fun mut Account.deposit(amount: i64) {
    balance += amount
}

fun mut Account.withdraw(amount: i64).R: bool {
    if amount > balance {
        return false
    }
    balance -= amount
    return true
}

fun main() {
    var a = Account(owner = "ada", balance = 100)
    a.deposit(50)
    print("${a.owner}: ${a.balance}")
    print("withdraw 500 ok? ${a.withdraw(500)}")
    print("withdraw 20 ok? ${a.withdraw(20)}")
    print("${a.owner}: ${a.balance}")
}
```

```text
ada: 150
withdraw 500 ok? false
withdraw 20 ok? true
ada: 130
```

</details>

Next: [Ownership, borrowing and moves](/tutorial/06-ownership).
