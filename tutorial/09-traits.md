---
title: "Tutorial 9: Traits and generics"
description: "Chapter 9 of the Kelp tutorial: traits with default methods, static dispatch through bounds, &dyn and Box<dyn> for dynamic dispatch, operator and Display traits, generic records and const generics, with real errors."
isPublished: true
tags: "tutorial, language, traits, generics"
---
A trait is a named set of methods that a type opts into with `impl Trait for Type`.
This chapter covers the whole trait story in two programs: traits, defaults and the
two kinds of dispatch, then operators, `Display` and generics. Reference pages:
[Traits](/language/traits), [Owned trait objects](/language/box-dyn),
[Associated types](/language/associated-types),
[Operator traits and Display](/language/operator-traits),
[Generics](/language/generics) and [Const generics](/language/const-generics).

## Part 1: traits and dispatch

```kelp
impl "std/str"

trait Shape {
    fun Self.area().return: f64
    fun Self.name().return: str
    fun Self.describe().return: String {
        return str.concat("a shape called ", self.name())
    }
    fun mut Self.scale(f: f64)
}

datac Circle(var r: f64)
datac Rect(var w: f64, var h: f64)

impl Shape for Circle {
    fun Self.area().return: f64 = self.r * self.r * 3.14159
    fun Self.name().return: str = "circle"
    fun mut Self.scale(f: f64) {
        self.r = self.r * f
    }
}

impl Shape for Rect {
    fun Self.area().return: f64 = self.w * self.h
    fun Self.name().return: str = "rect"
    fun Self.describe().return: String {
        return String.from_str("a rectangle that overrides describe")
    }
    fun mut Self.scale(f: f64) {
        self.w = self.w * f
        self.h = self.h * f
    }
}

// static dispatch: one copy of the function per concrete type
fun area_of<T: Shape>(s: &T).return: f64 = s.area()

// dynamic dispatch through a borrowed trait object
fun report(s: &dyn Shape) {
    print("${s.name()}: area ${s.area()}")
}

fun main() {
    var c = Circle(r = 1.0)
    val rect = Rect(w = 2.0, h = 3.0)
    print(area_of(c))
    c.scale(f = 2.0)
    print(area_of(c))
    print(c.describe())
    print(rect.describe())
    report(&c)
    report(&rect)

    // owned trait objects: different types in one list
    var shapes: List<Box<dyn Shape>> = List.empty()
    shapes.push(Box.of(Circle(r = 1.0)))
    shapes.push(Box.of(Rect(w = 4.0, h = 5.0)))
    var total = 0.0
    for s in shapes {
        total += s.area()
    }
    print("total ${total}")
    report(shapes.get(1).get())
}
```

```text
3.141590
12.566360
a shape called circle
a rectangle that overrides describe
circle: area 12.566360
rect: area 6.000000
total 23.141590
rect: area 20.000000
```

Same on both backends.

**Declaring and implementing.** A trait body is methods whose receiver is written
`Self`. A method with no body is a signature that every impl must provide; a method
with a body is a **default** that an impl may use or override. `Circle` took the
default `describe`; `Rect` overrode it. The impl has to match the declared signature
exactly (same receiver, same parameter names and types, same return type).
`impl Shape for Circle` must sit in the trait's module or the type's, and a type
gets at most one impl of a trait. A trait may name **supertraits**
(`trait Named: Shape`).

Forgetting a method is an error that tells you what to add:

```kelp
trait Shape {
    fun Self.area().return: f64
    fun Self.name().return: str
}

datac Circle(var r: f64)

impl Shape for Circle {
    fun Self.area().return: f64 = self.r * self.r * 3.14159
}

fun main() {
    print("never")
}
```

```text
$ kelpc check c9bad2.kp
error: trait 'Shape' declares 'fun Self.name().return: str', and 'impl Shape for Circle' does not implement it: add 'fun Self.name().return: str { ... }' to the block
  --> c9bad2.kp:8:1
```

**Static dispatch.** `fun area_of<T: Shape>(s: &T)` is a generic function whose
type parameter must implement `Shape`. The compiler produces one copy per concrete
type and calls the method directly, with no vtable. Calling it with a type that has
no impl is caught at the call:

```kelp
trait Shape {
    fun Self.area().return: f64
}

datac Circle(var r: f64)
datac Point(var x: f64)

impl Shape for Circle {
    fun Self.area().return: f64 = self.r * self.r * 3.14159
}

fun area_of<T: Shape>(s: &T).return: f64 = s.area()

fun main() {
    print(area_of(Point(x = 1.0)))
}
```

```text
$ kelpc check c9bad1.kp
error: the call to 'area_of' needs 'Point' to implement the trait 'Shape', and it does not: write 'impl Shape for Point { ... }' in the trait's module or in the type's
  --> c9bad1.kp:15:11
```

**Dynamic dispatch.** `&dyn Shape` is a borrowed trait object: a pointer to the
value plus a vtable. `report(&c)` and `report(&rect)` pass two different types to
one function that is compiled once. The `&T` coerces to `&dyn Shape` at a call
argument or a typed binding. `&mut dyn Shape` allows the `mut Self` methods.

**Owned trait objects.** `Box<dyn Shape>` owns its heap value, remembers the vtable
and drops through it. That is what lets one `List<Box<dyn Shape>>` hold a `Circle`
and a `Rect`. `s.area()` calls straight through the box, and `shapes.get(1).get()`
borrows the contents back as a `&dyn Shape`.

**Associated types.** A trait may declare `type Item` that each impl binds, the way
the `Iterator` of chapter 3 does (`type Item = i64`). Generic code reaches it as
`I::Item`. Chapter 3's `Countdown` is exactly that, and the
[reference](/language/associated-types) has more.

## Part 2: operators, Display, generics

```kelp
impl "std/ops"
impl "std/fmt"

datac Money(val cents: i64)

impl ops.Add for Money {
    fun Self.add(rhs: &Money).return: Money = Money(cents = self.cents + rhs.cents)
}

impl ops.Ord for Money {
    fun Self.cmp(other: &Money).return: i32 {
        if self.cents < other.cents {
            return -1
        }
        if self.cents > other.cents {
            return 1
        }
        return 0
    }
}

impl fmt.Display for Money {
    fun Self.to_text().return: String {
        var out = String.from_str("$")
        val dollars = fmt.int(self.cents / 100)
        val rest = fmt.int(self.cents % 100)
        out.push_str(dollars.as_str())
        out.push_str(".")
        if self.cents % 100 < 10 {
            out.push_str("0")
        }
        out.push_str(rest.as_str())
        return out
    }
}

// a generic record and a bounded generic function
datac Pair<A, B>(val first: A, val second: B)

fun sum_three<T: ops.Add>(a: T, b: T, c: T).return: T = a + b + c

// a const generic: the capacity is part of the type
datac Ring<const N: usize>(var items: [i32; N], var len: usize)

fun mut Ring<const N: usize>.push(v: i32).return: bool {
    if self.len >= N {
        return false
    }
    self.items.set(i = self.len, v = v)
    self.len += 1
    return true
}

fun Ring<const N: usize>.capacity().return: usize = N

fun main() {
    val a = Money(cents = 1250)
    val b = Money(cents = 705)
    print(a + b)
    print("sum of three: ${sum_three(a, b, Money(cents = 5))}")
    print("a < b: ${a < b}, a >= b: ${a >= b}")

    val p: Pair<i32, String> = Pair(first = 1, second = "one")
    print("${p.first} ${p.second}")

    var ring = Ring(items = [0; 2], len = 0)
    print("capacity ${ring.capacity()}")
    print("push 1: ${ring.push(1)}")
    print("push 2: ${ring.push(2)}")
    print("push 3: ${ring.push(3)}")
}
```

```text
$19.55
sum of three: $19.60
a < b: false, a >= b: true
1 one
capacity 2
push 1: true
push 2: true
push 3: false
```

**Operators are traits.** `std/ops` declares `Add`, `Sub`, `Mul`, `Div`, `Rem`,
`Neg` and `Ord`. A user type gets `+` by implementing `ops.Add`; the front end turns
`a + b` into a call of `a.add(&b)`. `Ord` has one method, `cmp`, returning a
negative, zero or positive `i32`, and gives you `<`, `<=`, `>` and `>=`. `fmt.Display`
has one method, `to_text`, returning a `String`, and it is what makes `print(x)` and
`"${x}"` work for your type. (The `$19.55` line is `print(a + b)` with a `Money`.)

**Generics.** `datac Pair<A, B>(val first: A, val second: B)` is generic; the type
arguments are inferred at a construction or written where a type is written
(`Pair<i32, String>`). `fun sum_three<T: ops.Add>(...)` shows that a bound can be an
operator trait, and the function body just uses `+`. Two instantiations of a generic
type are different types.

**Const generics.** `Ring<const N: usize>` takes a *value* as a type argument: the
capacity is part of the type, and the `[0; 2]` array literal it was built from
decides `N = 2`, so `capacity()` returned 2 and the third `push` was refused. The
allowed const types are `usize`, `u8` to `u64`, `i32`, `i64` and `bool`.

## Exercises

1. Declare `trait Named` with a required `name` and a defaulted `greet`, implement it
   for two types, one overriding `greet`, and print both from a
   `List<Box<dyn Named>>`.
2. Give `Money` subtraction through `ops.Sub`.

<details>
<summary>Solutions</summary>

1.

```kelp
trait Named {
    fun Self.name().return: str
    fun Self.greet().return: String {
        return String.from_str("hi")
    }
}

datac Dog(val age: i32)
datac Cat(val age: i32)

impl Named for Dog {
    fun Self.name().return: str = "dog"
}

impl Named for Cat {
    fun Self.name().return: str = "cat"
    fun Self.greet().return: String {
        return String.from_str("meow")
    }
}

fun main() {
    var pets: List<Box<dyn Named>> = List.empty()
    pets.push(Box.of(Dog(age = 3)))
    pets.push(Box.of(Cat(age = 5)))
    for p in pets {
        print("${p.name()} says ${p.greet()}")
    }
}
```

```text
dog says hi
cat says meow
```

2.

```kelp
impl "std/ops"

datac Money(val cents: i64)

impl ops.Sub for Money {
    fun Self.sub(rhs: &Money).return: Money = Money(cents = self.cents - rhs.cents)
}

fun main() {
    val left = Money(cents = 1000) - Money(cents = 275)
    print(left.cents)
}
```

```text
725
```

</details>

Next: [Closures and scoped blocks](/tutorial/10-closures).
