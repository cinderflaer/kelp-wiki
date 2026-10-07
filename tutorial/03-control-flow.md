---
title: "Tutorial 3: Control flow and iterators"
description: "Chapter 3 of the Kelp tutorial: if, elif, when, while, for over lists and ranges, writing your own Iterator, break and continue, and the refusal to mutate a list you are walking."
isPublished: true
tags: "tutorial, language"
---
This chapter covers choosing and repeating. Kelp has `if`/`elif`/`else`, `when`,
`while` and `for`; there is no `loop`, no labelled break and no `goto`. The
reference is [Control flow](/language/control-flow) and
[Iterators, `for` and `break`](/language/iterators).

## The program

```kelp
impl "std/iter"
impl "std/option"

fun classify(n: i32).return: &str = when {
    n > 0 -> "positive"
    n < 0 -> "negative"
    else -> "zero"
}

datac Countdown(var n: i64)

impl iter.Iterator for Countdown {
    type Item = i64
    fun mut Self.next().return: option.Option<i64> {
        if self.n <= 0 {
            return option.Option.None
        }
        val v = self.n
        self.n = self.n - 1
        return option.Option.Some(value = v)
    }
}

fun main() {
    for n in [5, -2, 0] {
        val kind = classify(n)
        if n > 2 {
            print("${n}: ${kind} and big")
        } elif n < 0 {
            print("${n}: ${kind}")
        } else {
            print("${n}: ${kind} and small")
        }
    }

    var i = 0
    while i < 3 {
        print!("w${i} ")
        i += 1
    }
    print("")

    for i in iter.range(0, 10) {
        if i % 2 == 0 {
            continue
        }
        if i > 7 {
            break
        }
        print!("${i} ")
    }
    print("")

    for v in Countdown(n = 4) {
        print!("${v}... ")
    }
    print("liftoff")

    val words: List<String> = List.empty()
    var names: List<String> = List.empty()
    names.push("ada")
    names.push("grace")
    for name in names {
        print("name ${name} has ${name.len()} letters")
    }
    print("${words.len()} words")
}
```

```text
5: positive and big
-2: negative
0: zero and small
w0 w1 w2 
1 3 5 7 
4... 3... 2... 1... liftoff
name ada has 3 letters
name grace has 5 letters
0 words
```

Identical output on the LLVM backend and on the C oracle.

## Choosing

`if` takes a `bool`, and `elif` is the preferred spelling of the chain (`else if`
is accepted but `kelpc lint` points you to `elif`). An `if` can also be an
expression when both arms give the same type and an `else` is present.

`when` without a scrutinee is a chain of `condition -> value` arms, evaluated in
order, and with a value it needs an `else`. `classify` above uses it. `->` appears
nowhere else in the language. With a scrutinee, `when` matches an `enum` (chapter 5).

## Repeating

- `while cond { ... }` re-evaluates the condition before each pass.
- `for x in xs { ... }` walks a `List<T>` or an array `[T; N]` front to back. The
  loop variable is a `val`. For an owned element type, such as `String`, it is a
  borrow: `name.len()` worked on a `&String` above.
- `for i in iter.range(0, 10)` walks a half-open range. The `std/iter` module is
  imported with `impl "std/iter"`, and its items are reached as `iter.range`,
  `iter.range_step`, `iter.count`, `iter.sum_i64` and `iter.collect_list`. See
  [`std/iter`](/stdlib/iter).
- `break` leaves the innermost loop and `continue` goes to its next pass.

## Your own iterator

`for x in it` works for any type that implements the `Iterator` trait: one
associated type `Item` and one method, `next`, which returns an `Option` — `Some`
to continue, `None` to stop. `Countdown` above shows all of it:

- `datac Countdown(var n: i64)` is a record, chapter 5.
- `impl iter.Iterator for Countdown { ... }` says the type is an iterator.
- `fun mut Self.next()` is a method whose receiver is `mut`, because advancing
  changes the iterator. Inside, `self` is the receiver.
- The loop calls `next()` until it returns `None`.

Traits come properly in chapter 9, so treat this as a recipe for now. The point to
take away is that `for` is not magic: it is an ordinary `while` over `next()`.

## The one `for` rule to remember

The body of a `for` may **read** the list it walks but may not change it:

```kelp
fun main() {
    var xs: List<i32> = List.empty()
    xs.push(1)
    for x in xs {
        xs.push(x + 1)
    }
    print(xs.len())
}
```

```text
$ kelpc check c3bad.kp
error: cannot mutate 'xs' while iterating over it
  --> c3bad.kp:4:14
```

When a loop has to change what it walks, walk by index with `while` instead.

## Exercises

1. Print FizzBuzz for 1 to 15.
2. Write an iterator `ByTwos` that counts down by twos from a starting value and stops before zero.

<details>
<summary>Solutions</summary>

1.

```kelp
impl "std/iter"

fun main() {
    for i in iter.range(1, 16) {
        if i % 15 == 0 {
            print("FizzBuzz")
        } elif i % 3 == 0 {
            print("Fizz")
        } elif i % 5 == 0 {
            print("Buzz")
        } else {
            print("${i}")
        }
    }
}
```

```text
1
2
Fizz
4
Buzz
Fizz
7
8
Fizz
Buzz
11
Fizz
13
14
FizzBuzz
```

(A `when` that yields a template does not compile: a template can only be printed,
which chapter 4 explains. That is why every branch calls `print`.)

2. Copy `Countdown`, step by two:

```kelp
impl "std/iter"
impl "std/option"

datac ByTwos(var n: i64)

impl iter.Iterator for ByTwos {
    type Item = i64
    fun mut Self.next().return: option.Option<i64> {
        if self.n <= 0 {
            return option.Option.None
        }
        val v = self.n
        self.n = self.n - 2
        return option.Option.Some(value = v)
    }
}

fun main() {
    for v in ByTwos(n = 6) {
        print("${v}")
    }
}
```

```text
6
4
2
```

</details>

Next: [Text](/tutorial/04-text).
