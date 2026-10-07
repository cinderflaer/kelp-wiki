---
title: "Tutorial 8: Collections"
description: "Chapter 8 of the Kelp tutorial: List and Map (and the fixed-size array), how get and remove behave for owned and Copy elements, insertion-ordered maps, sorting records, and the real refusals for bad element types."
isPublished: true
tags: "tutorial, language, collections"
---
Three containers are compiler builtins, `List<T>`, `Map<K, V>` and `Box<T>` (you met
`Box` in chapter 6), plus the fixed-size array `[T; N]`. They are owned values with
the move and drop rules of chapter 6. The reference is
[Collections](/language/collections), with the library halves at
[`std/list`](/stdlib/list) and [`std/str`](/stdlib/str).

## The program

```kelp
impl "std/str"
impl "std/list"

datac Entry(val word: String, val count: i64)

fun main() {
    var xs: List<i32> = List.empty()
    xs.push(30)
    xs.push(10)
    xs.push(20)
    xs.sort()
    print("sorted: ${xs.get(0)} ${xs.get(1)} ${xs.get(2)}, len ${xs.len()}")
    print("contains 20: ${xs.contains(20)}")
    val top = xs.slice(1, 3)
    print("slice len ${top.len()}")
    val last = xs.pop()
    print("popped ${last}, left ${xs.len()}")

    val doubled = list.map(xs, fun(x: &i32).return: i32 = x * 2)
    print("doubled first ${doubled.get(0)}")

    // a Map keeps insertion order
    val text = "the cat and the dog and the bird"
    val words = str.split(text, " ")
    var counts: Map<String, i64> = Map.new()
    for w in words {
        counts.insert(key = w.as_str(), v = counts.get_or(key = w.as_str(), fallback = 0) + 1)
    }
    val keys = counts.keys()
    for k in keys {
        print("${k}: ${counts.get(key = k.as_str())}")
    }
    print("has cat ${counts.has(key = "cat")}, has cow ${counts.has(key = "cow")}")
    val gone = counts.remove(key = "cat")
    print("removed ${gone}, ${counts.len()} left")

    var entries: List<Entry> = List.empty()
    entries.push(Entry(word = "b", count = 2))
    entries.push(Entry(word = "a", count = 9))
    entries.sort()
    print("first entry ${entries.get(0).word}")

    var grid: List<List<i32>> = List.empty()
    var row: List<i32> = List.empty()
    row.push(1)
    row.push(2)
    grid.push(row)
    print("grid rows ${grid.len()}")

    val fixed: [i32; 4] = [4, 3, 2, 1]
    var total = 0
    for v in fixed {
        total += v
    }
    print("array of ${fixed.len()} sums to ${total}")
}
```

```text
sorted: 10 20 30, len 3
contains 20: true
slice len 2
popped 30, left 2
doubled first 20
the: 3
cat: 1
and: 2
dog: 1
bird: 1
has cat true, has cow false
removed 1, 4 left
first entry a
grid rows 1
array of 4 sums to 10
```

Same output on both backends.

## `List<T>`

`List.empty()` makes an empty list, and its element type comes from the binding
(`var xs: List<i32> = List.empty()`) or from the first `push`. The methods are
`len`, `is_empty`, `get`, `set`, `push`, `pop`, `insert`, `remove`, `clear`, `clone`,
`sort`, `reverse`, `contains` and `slice`.

`get(i)` gives a **copy** when the element is `Copy` (an `i32`) and a **shared
borrow** when it is owned (a `&String`), which is the chapter 6 rule again: that is
why the word loop below needs `.as_str()` where a `str` is expected. Out-of-range
indices and popping an empty list **panic**.

A `datac` element gets a derived deep copy and a derived order, field by field in
declaration order. That is how `entries.sort()` put `a` before `b` without any
comparison function being written. A record containing a `List`, `Map` or `Box` has
neither, and the compiler says so.

`list.map`, `list.filter`, `list.find_index`, `list.any`, `list.all` and `list.each`
are free functions in `std/list` that take a closure (chapter 10), written
`fun(x: &i32).return: i32 = x * 2`; inside, a `Copy` element is used directly. `filter`
needs a `Copy` element.

A list of lists needs no wrapper: `List<List<i32>>`.

## `Map<K, V>`

`Map.new()` with a written type. `insert(key, v)` upserts, `get`, `get_or`, `has`,
`remove`, `keys`, `values`, `len`. Three things to know:

- **Insertion order is kept.** The word counts printed `the`, `cat`, `and`, `dog`,
  `bird`, which is the order each word first appeared, not a hash order.
- A `String`-keyed map takes its key as a `str` in every method, so a `&String` loop
  variable needs `.as_str()`. A scalar key is passed by value.
- `get` and `remove` **panic** when the key is absent. Use `has` first, or
  `get_or` with a fallback:

```kelp
fun main() {
    var m: Map<String, i32> = Map.new()
    m.insert(key = "a", v = 1)
    print(m.remove(key = "zzz"))
}
```

```text
$ ./c8bad2
panic: Map.remove: key not found
exit 1
```

A key has to be keyable (a `String`, an integer, `bool`, `char`, or a record or
enum whose parts are), and a float is refused. A map **value** is narrower than a list
element:

```kelp
fun main() {
    var xs: List<i32> = List.empty()
    xs.push(1)
    print(xs.get(0))
    var counts: Map<String, List<i32>> = Map.new()
    print(counts.len())
}
```

```text
$ kelpc check c8bad1.kp
error: 'List<i32>' cannot be a 'Map' value: the value set is a scalar, 'String', 'Bytes', a 'datac', or an 'enum', which is narrower than a list's (that also takes a 'List' or a 'Box'). A container, an array, a borrow or a view, an atomic, a function value, and 'unit' are refused
  --> c8bad1.kp:5:29
```

A value that holds a list is wrapped in a one-field `datac`.

## Arrays

`[i32; 4]` is a fixed-size array whose length is part of its type. It allocates
nothing and is `Copy` when its element is. `for v in fixed` walks it, and
`.len()` is the type's own length. An integer array literal defaults to `i32`;
annotate it for another width.

## Exercises

1. Remove duplicate words from `"a b a c b d"`, keeping first appearances. (Use a
   `Map<String, bool>` as a seen-set.)
2. Build a `List<i64>` of 1 to 6, keep the evens with `list.filter`, and print how
   many there are and their sum.

<details>
<summary>Solutions</summary>

1.

```kelp
impl "std/str"

fun main() {
    val words = str.split("a b a c b d", " ")
    var seen: Map<String, bool> = Map.new()
    var unique: List<String> = List.empty()
    for w in words {
        if !seen.has(key = w.as_str()) {
            seen.insert(key = w.as_str(), v = true)
            unique.push(w.clone())
        }
    }
    print(str.join(unique, " "))
}
```

```text
a b c d
```

2.

```kelp
impl "std/list"

fun main() {
    var xs: List<i64> = List.empty()
    for i in [1, 2, 3, 4, 5, 6] {
        xs.push(i.to_i64())
    }
    val evens = list.filter(xs, fun(x: &i64).return: bool = x % 2 == 0)
    var total: i64 = 0
    for e in evens {
        total += e
    }
    print("${evens.len()} evens, sum ${total}")
}
```

```text
3 evens, sum 12
```

</details>

Next: [Traits and generics](/tutorial/09-traits).
