---
title: "Records, enums and ownership"
description: "datac records, enum types with payloads, methods, when for matching, and the ownership rules that decide who may use a value, with the real compiler errors."
isPublished: true
tags: "tutorial, language, data, ownership"
---
**You will learn:** how to group values into records and enums, how to match on an
enum, and how Kelp keeps track of who owns each value.

## Records and enums

```kelp
datac Point(val x: i32, val y: i32)

datac Counter(val name: String, var count: i32)

enum Shape {
    Circle(val r: f64)
    Rect(val w: f64, val h: f64)
    Empty
}

fun Point.shifted(dx: i32) => Point = Point(x = self.x + dx, y = self.y)

fun area(s: &Shape) => f64 = when s {
    Circle(r) -> 3.0 * r * r
    Rect(w, h) -> w * h
    Empty -> 0.0
}

fun bump(c: mut Counter) {
    c.count += 1
}

fun main() {
    val p = Point(x = 3, y = 4)
    print(p.x)
    val q = p.shifted(10)
    print("${q.x}, ${q.y}")

    var c = Counter(name = String.from_str(s = "clicks"), count = 0)
    bump(c)
    bump(c)
    print("${c.name}: ${c.count}")

    val shapes = [Shape.Circle(r = 1.0), Shape.Rect(w = 2.0, h = 3.5), Shape.Empty]
    for s in shapes {
        print(area(s))
    }
}
```

```text
3
13, 4
clicks: 2
3.000000
7.000000
0.000000
```

- `datac` declares a record. Each field is `val` (fixed) or `var` (can change).
  You build one by naming the fields: `Point(x = 3, y = 4)`.
- `enum` declares a value that is one of several variants. Each variant may carry
  data. `Shape.Circle(r = 1.0)` builds a circle.
- `fun Point.shifted(...)` is a method. Inside it, `self` is the value the method
  was called on, and its fields are read with `self.x`.
- `when s { ... }` picks the variant. It must cover every variant, or have an
  `else ->` arm. Each arm binds the data of its variant, here `r`, `w` and `h`.

To change a field, the record must be in a `var` and the field must be `var`.
`bump` takes `c` as `mut Counter`, which lets it change `count`. The next section
explains what `mut` means.

## Who owns a value

Every value in Kelp has exactly one owner at a time. When the owner goes out of
scope, the value's life ends: a resource is closed, and a value with a destructor runs
it. In a hosted build the collector reclaims the memory of a text or a list once no
path reaches it. The one-owner rule is what lets the compiler say which name a value
belongs to, and it has two effects you will see in every program.

**Passing a value to a function borrows it.** A parameter declared as a plain
type, such as `name: String`, is a borrow: the function can read the value, but
the caller still owns it afterwards. A `String` passed to such a parameter can
still be printed after the call.

**Assigning an owned value moves it.** Once moved, the old name cannot be used:

```kelp refused
fun main() {
    val a = String.from_str(s = "x")
    val b = a
    print(a)
    print(b)
}
```

```text
$ kelpc check moved.kp
error: use of moved value 'a'
  --> moved.kp:4:11
  help: pass &a to keep the value here, or do not use it after the move.
```

`val b = a` gave the `String` to `b`, so `a` is empty. If a function should keep
the value, give it the value with a `move` parameter. A `move` parameter takes
ownership at the call:

```kelp
fun keep(name: move String) => i32 = 1
```

Use a plain parameter when the function only reads the value, and `move` when it
needs to keep it. `mut` is the middle choice: the function may change the value,
and the caller gets it back afterwards.

## Mutability

A `val` binding can never change, not even its fields. Changing a field of a
`val` is refused:

```kelp refused
datac Counter(val name: String, var count: i32)

fun main() {
    val c = Counter(name = String.from_str(s = "clicks"), count = 0)
    c.count = 5
    print(c.count)
}
```

```text
$ kelpc check immut.kp
error: cannot assign to 'c': not declared 'var'
  --> immut.kp:5:5
```

Declare the binding `var`, or change the field through a `mut` parameter, as
`bump` does.

## Try it

1. Add a variant `Triangle(val base: f64, val height: f64)` to `Shape`. The
   `when` in `area` stops compiling. What does the error say?
2. Write `fun Counter.reset()` that sets `count` back to zero. Which parameter
   form does the method need, and does `Counter` need a `var` field?

Next: [Errors](/tutorial/07-errors).
