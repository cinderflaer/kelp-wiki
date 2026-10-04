---
title: "Tutorial 6: Ownership, borrowing and moves"
description: "Chapter 6 of the Kelp tutorial: one owner per value, parameters that borrow, move and mut parameters, borrows that end at their last use, cursors over a linked list, and partial moves, with the real borrow-checker errors."
isPublished: true
tags: "tutorial, language, ownership"
---
There is no garbage collector in Kelp and no lifetime syntax. Owned values
(`String`, `Bytes`, `List`, `Map`, `Box`, every `datac` and `enum`) have exactly one
owner, and the end of the owner's scope is the free, on every exit path. The checker
makes that safe with a handful of rules. This chapter walks through them; the
reference is [Ownership and borrowing](/language/ownership).

## The program

```kelp
datac Node(val value: i32, val next: Box<Node>)

fun show(s: String) {
    print("show: ${s}")
}

fun consume(s: move String).R: usize = s.len()

fun main() {
    // a parameter borrows: `name` is still ours afterwards
    val name = String.from_str("bob")
    show(name)
    print("still have ${name}")

    // `move` hands it over for good
    val other = String.from_str("alice")
    print("consumed ${consume(other)} bytes")

    // a borrow ends at its last use, so pushing after it is fine
    var names: List<String> = List.empty()
    names.push("alpha")
    val first = names.get(0)
    print("first is ${first}")
    names.push("beta")
    print("now ${names.len()} names")

    // a cursor walks a linked list; rebinding it is fine, the list stays pinned
    var list = Node(value = 1, next = Box.of(Node(value = 2, next = Box.of(Node(value = 3, next = Box.empty())))))
    var cur = &list
    var sum = 0
    sum += cur.value
    while !cur.next.is_empty() {
        cur = cur.next.get()
        sum += cur.value
    }
    print("sum ${sum}")
}
```

```text
show: bob
still have bob
consumed 5 bytes
first is alpha
now 2 names
sum 6
```

Both backends printed this.

## Parameters borrow, `move` takes

The first surprise for Rust readers: **passing an owned value to a parameter is not
a move.** A parameter `s: String` is a shared borrow, which is why `name` was still
usable after `show(name)`. A parameter `s: move String` takes ownership, and the
caller loses the value; `s: mut String` is an exclusive borrow that may change it
(exercise 1). Moving by assignment works the same way as passing to a `move`
parameter:

```kelp
fun main() {
    val a = String.from_str("x")
    val b = a
    print(b)
    print(a)
}
```

```text
$ kelpc check c6bad1.kp
error: use of moved value 'a'
  --> c6bad1.kp:5:11
```

```kelp
fun consume(s: move String).R: usize = s.len()

fun main() {
    val a = String.from_str("bob")
    print(consume(a))
    print(a)
}
```

```text
$ kelpc check c6bad2.kp
error: use of moved value 'a'
  --> c6bad2.kp:6:11
```

The cure is one of: borrow instead of move, take a second owned copy with
`.clone()`, or make the last use really the last.

## Borrows end at their last use

This is a **non-lexical** borrow rule. `val first = names.get(0)` borrows `names`
until `first` is last read, and not until the end of the block. In the program the
`push("beta")` came after the last use of `first`, so it compiled. Swap the order
and the borrow is live across the mutation:

```kelp
fun main() {
    var names: List<String> = List.empty()
    names.push("alpha")
    val first = names.get(0)
    names.push("beta")
    print(first)
}
```

```text
$ kelpc check c6bad3.kp
error: cannot borrow 'names' as exclusive: already borrowed as shared
  --> c6bad3.kp:5:5
```

Two notes from the language page: a use inside a loop body keeps the borrow live for
the whole loop (the next iteration reaches the earlier statements), and a use in one
arm of an `if` keeps it live through the whole `if`.

## Cursors

A reference you rebind as you go is a **cursor**. `var cur = &list` and then
`cur = cur.next.get()` in the program walked a three-node list. The checker tracks
which owners a cursor may borrow from: rebinding the cursor is fine, the owner
(`list`) stays pinned while the cursor is used. Mutating the owner under a live
cursor is refused:

```kelp
datac Node(val value: i32, val next: Box<Node>)

fun main() {
    var list = Node(value = 1, next = Box.of(Node(value = 2, next = Box.empty())))
    var cur = &list
    list = Node(value = 9, next = Box.empty())
    print(cur.value)
}
```

```text
$ kelpc check c6bad5.kp
error: cannot assign to 'list' while it is borrowed
  --> c6bad5.kp:6:5
```

Over a `List` the same shape works by index, `cur = xs.get(i)`.

## Partial moves

Reading an owned field of an owned local takes that field out and leaves the rest
of the record owned. Exercise 2 does this. From a borrow it is refused, because it
would create two owners of one buffer:

```kelp
datac Bag(val xs: List<i32>, val name: String)

fun steal(b: &Bag).R: List<i32> = b.xs

fun main() {
    val b = Bag(xs = List.empty(), name = "bag")
    print(steal(b).len())
}
```

```text
$ kelpc check c6bad4.kp
error: cannot move the field 'xs' out of 'b': the value is borrowed, so it is not this frame's to give away
  --> c6bad4.kp:3:35
```

To take an owned field out from behind a borrow, hold it in a `Box` and `take()` it,
or clone it.

## The two rules behind most borrow errors

1. An owned value is moved once.
2. A borrow must not outlive its use, and while it is live the owner may not be
   mutated or moved.

[Pitfalls](/language/pitfalls) lists the common messages and fixes.

## Exercises

1. Write `exclaim(s: mut String)` that appends `!`, and call it twice on a
   `var`. What happens when the argument is a `val`?
2. Write `name_of(b: move Bag).R: String` over `datac Bag(val xs: List<i32>, val name: String)`
   that takes the name out and returns it.

<details>
<summary>Solutions</summary>

1.

```kelp
fun exclaim(s: mut String) {
    s.push_str("!")
}

fun main() {
    var greeting = String.from_str("hello")
    exclaim(greeting)
    exclaim(greeting)
    print(greeting)
}
```

```text
hello!!
```

With a `val` the call is refused:

```kelp
fun exclaim(s: mut String) {
    s.push_str("!")
}

fun main() {
    val greeting = String.from_str("hello")
    exclaim(greeting)
    print(greeting)
}
```

```text
$ kelpc check c6x1bad.kp
error: cannot assign to 'greeting': not declared 'var'
  --> c6x1bad.kp:7:13
```

2.

```kelp
datac Bag(val xs: List<i32>, val name: String)

fun name_of(b: move Bag).R: String {
    val n = b.name
    return n
}

fun main() {
    val b = Bag(xs = List.empty(), name = "bag")
    val n = name_of(b)
    print("took ${n}")
}
```

```text
took bag
```

</details>

Next: [Errors: Option, Result and panic](/tutorial/07-errors).
