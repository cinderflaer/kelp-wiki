---
title: "Patterns for owned values"
description: "Six patterns for writing Kelp with single ownership: a tree of Box, a growing List, a Map of owned values, text and views without copies, returning owned values, and passing borrows. Each is a complete program."
isPublished: true
tags: "language, ownership, memory, collections"
---
Each pattern below is a complete program. All of them compiled and printed the
output shown with the 26.10.5 release compiler. The rules they follow are on
[The rules of ownership](/memory/rules).

## A tree of Box

A recursive type holds its children in a `Box`, because a `datac` field cannot
contain its own type directly. `Box.empty()` is a child that is not there, and
`Box.of(x)` moves a value into a new box. The function that walks the tree takes
a borrow, so the caller keeps the tree.

```kelp
datac Tree(val value: i32, val left: Box<Tree>, val right: Box<Tree>)

fun leaf(v: i32) => Tree = Tree(value = v, left = Box.empty(), right = Box.empty())

fun sum(t: Tree) => i32 {
    var total = t.value
    if !t.left.is_empty() {
        total += sum(t.left.get())
    }
    if !t.right.is_empty() {
        total += sum(t.right.get())
    }
    return total
}

fun main() {
    val root = Tree(value = 1, left = Box.of(leaf(2)), right = Box.of(leaf(3)))
    print(sum(root))
}
```

```text
6
```

`t.left.get()` borrows the child, so `sum` reads it without taking it away.

## A growing List

A `List` owns its elements. `push` moves a value in, `pop` moves the last one
out, and `get` returns a borrow for a non-`Copy` element. A function that only
reads the list takes `&List<T>`. The list is `List<i64>` because `iter.range`
yields `i64`.

```kelp
fun total(xs: List<i64>) => i64 {
    var sum: i64 = 0
    for x in xs {
        sum += x
    }
    return sum
}

fun main() {
    var xs: List<i64> = List.empty()
    for i in iter.range(1, 5) {
        xs.push(i * 10)
    }
    print(total(xs))
    val last = xs.pop()
    print("popped ${last}, ${xs.len()} left")
    xs.set(0, 7)
    print(xs.get(0))
}
```

```text
100
popped 40, 3 left
7
```

## A Map of owned values

A `Map` owns its keys and values. `insert` moves a `String` in, `get` borrows it,
and `remove` moves it out. A map value has to be a scalar, a `String`, a `Bytes`
or a `datac`/`enum`, so a value that is a `List` goes in a one-field `datac`.

```kelp
fun main() {
    var names: Map<String, String> = Map.new()
    names.insert(key = "ada", v = String.from_str("Ada Lovelace"))
    names.insert(key = "linus", v = String.from_str("Linus Torvalds"))
    print(names.get(key = "ada"))
    val gone = names.remove(key = "linus")
    print("removed ${gone}")
    print(names.has(key = "linus"))
    print(names.len())
}
```

```text
Ada Lovelace
removed Linus Torvalds
false
1
```

`gone` owns the removed string, and it is dropped at the end of `main`.

## Text and views without copies

A `View` is a borrowed pointer and a length. Slicing one allocates nothing, so a
parser can hand out pieces of its input. `to_string()` copies a piece only when
the piece has to outlive the input. This function returns a view of its
parameter, which is allowed because the return is derived from that parameter.

```kelp
fun first_word(line: str) => View {
    val v = line.view()
    var end: int = 0
    while end < v.len() && v.get(end) != 32 {
        end += 1
    }
    return v.slice(0, end)
}

fun main() {
    val line = String.from_str("the quick brown fox")
    val w = first_word(line.as_str())
    print(w.len())
    print(w.to_string())
    print(line.len())
}
```

```text
3
the
19
```

`line.view()` runs one `strlen`, and `v.get` and `v.len` are constant time after
that. Index a `str` in a loop with `str.byte` instead, and each call reads up to
its index, which is quadratic over the loop.

## Returning an owned value

A function that builds a value returns it with an owned return type. The caller
owns the result, and nothing is dropped inside the function. Build text in a local
`String` and return that local; do not return a borrow of it.

```kelp
fun make_name(id: i32) => String {
    var s = String.from_str("user-")
    val digits = str.from_i64(id.to_i64())
    s.push_str(digits.as_str())
    return s
}

fun main() {
    val a = make_name(7)
    val b = make_name(42)
    print(a)
    print(b)
    print(a.len() + b.len())
}
```

```text
user-7
user-42
13
```

`digits` is bound to a name before `as_str()` borrows it. Passing the call's result
straight into `as_str()` is refused, because the temporary would be dropped before the
borrow is used.

## Passing borrows to a function

A plain parameter reads its argument, `mut T` lets the callee change a `datac`
in place, and `mut i32` lets it change a scalar through `*`. The caller passes
the variable itself, and the change is visible to the caller afterwards.

```kelp
datac Counter(var count: i32)

fun bump(c: mut Counter) {
    c.count += 1
}

fun add_to(n: mut i32, by: i32) {
    *n += by
}

fun peek(c: Counter) => i32 = c.count

fun main() {
    var c = Counter(count = 0)
    bump(c)
    bump(c)
    print(peek(c))
    var total: i32 = 5
    add_to(total, 10)
    print(total)
    print(c.count)
}
```

```text
2
15
2
```

To hand a whole `List` to a function that keeps it or throws it away, use a `move`
parameter instead: `fun sum_all(xs: move List<i32>)` takes the list, and the
caller's name is moved from.

## See also

- [Common refusals](/memory/refusals): the messages these patterns avoid
- [Collections](/language/collections): every method on `List`, `Map` and `Box`
- [Text](/language/text): `String`, `Bytes`, `str` and `View` in full
