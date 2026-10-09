---
title: "Collections"
description: "List, Map, Box and the fixed-size array: building them, reading and removing elements, insertion order, and the panics that come with an index or key that is not there."
isPublished: true
tags: "tutorial, language, collections"
---
**You will learn:** how to hold many values with `List`, look them up by key with
`Map`, keep one value in a `Box`, and use a fixed-size array.

## The program

```kelp
fun main() {
    var xs: List<i32> = List.empty()
    xs.push(30)
    xs.push(10)
    xs.push(20)
    print("len ${xs.len()}")
    xs.sort()
    print(xs.get(0))
    print(xs.contains(20))
    while !xs.is_empty() {
        print("popped ${xs.pop()}")
    }

    var ages: Map<String, i64> = Map.new()
    ages.insert(key = "ada", v = 36)
    ages.insert(key = "linus", v = 54)
    ages.insert(key = "ada", v = 37)
    print("ada is ${ages.get(key = "ada")}")
    print("grace is ${ages.get_or(key = "grace", fallback = 0)}")
    print("has linus: ${ages.has(key = "linus")}")
    for (name, age) in ages {
        print("${name} ${age}")
    }

    val squares = [1, 4, 9]
    print("array sum ${squares.get(0) + squares.get(2)}")

    var slot: Box<i32> = Box.empty()
    slot.set(5)
    print("box ${slot.take()}")
    print("empty now: ${slot.is_empty()}")
}
```

```text
len 3
10
true
popped 30
popped 20
popped 10
ada is 37
grace is 0
has linus: true
ada 37
linus 54
array sum 10
box 5
empty now: true
```

## List

`List<T>` is a growable sequence. Its element type is written in the declaration,
`List<i32>`, or taken from the first value you add. `push` adds to the end, and
`pop` removes from the end and returns the value. `len` counts the elements, and
`sort` puts them in order.

`get(i)` reads the element at index `i`, counting from 0. It panics when the index
is past the end, as the [errors chapter](/tutorial/07-errors) showed.

## Map

`Map<K, V>` stores values by key. `insert` adds a key, or replaces the value if the
key is already there, which is what happens to `"ada"` in the program. `get` panics
for a missing key, so check with `has` first, or use `get_or`, which returns a
fallback instead.

A map keeps its entries in the order they were inserted. `for (name, age) in ages`
walks the pairs in that order, which is why the program prints `ada` before
`linus`.

Keys can be text, numbers, booleans, characters, or records and enums built from
those. A floating-point number cannot be a key, because `NaN` never equals itself
and the key could never be found again.

## Box

A `Box<T>` holds one value, or nothing. It is the simplest container, and it is
how a type can refer to itself, such as a linked list node. `take` removes the
value and leaves the box empty. Taking from an empty box panics.

## Arrays

`[1, 4, 9]` is an array with a fixed length of 3. Its length is part of its type,
so it never grows, and it allocates nothing. Read it with `get(i)` and change it
with `set(i, v)`. Use a list when the size changes and an array when it does not.

## Try it

1. Add `print(xs.get(5))` just before the `while` loop. What happens, and what
   does the message say?
2. Insert `"ada"` into `ages` a third time with the value 1, then print the keys
   with `ages.keys()` in a loop. Does the order change?

Next: [Traits and generics](/tutorial/09-traits).
