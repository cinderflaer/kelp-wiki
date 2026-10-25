---
title: "List and set helpers"
description: "The list and set helpers beyond the builtins: fold, zip, chunks, a comparator sort, and the three set operations."
isPublished: true
tags: "example, collections"
---

The `list-and-set-helpers` program prints the results of the list helpers that go beyond the builtins.
Those are `fold`, `zip`, `chunks` and a comparator sort, followed by the three set operations.

| | |
| --- | --- |
| Source | [`src/list-and-set-helpers.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki-wikijs/raw/branch/main/examples/src/list-and-set-helpers.kp) |
| Needs | `listx`, `set` |
| Shows | closure-shaped helpers over a `List`, and `Set<T>` against `StrSet` |

## The dependencies

```toml
[dependencies]
listx = "Lilly/fpl/listx"
set   = "Lilly/fpl/set"
```

Both exist because of one language rule: a user module cannot overload a name. So
`listx` spells the element type into the function (`sum_i32`, `min_i64`), and
`set` ships two types where the standard library would have one generic set.

## The program

```kelp project
impl "deps/listx/lib"
impl "deps/set/lib"

fun main() {
    var xs: List<i32> = List.empty()
    xs.push(3)
    xs.push(1)
    xs.push(2)
    xs.push(1)

    print("listx      sum = ${listx.sum_i32(xs)}")
    print("listx      min = ${listx.min_i32(xs)}")
    print("listx      max = ${listx.max_i32(xs)}")
    print("listx      fold(+, 0) = ${listx.fold(xs, 0, fun(acc: i32, x: &i32) => i32 = acc + x)}")
    print("listx      unique = ${listx.unique_i32(xs).len()} distinct values")

    val at = listx.position_i32(xs, 2)
    if let Some(i) = at {
        print("listx      first index of 2 = ${i}")
    }

    var names: List<i32> = List.empty()
    names.push(10)
    names.push(20)
    names.push(30)
    val pairs = listx.zip(xs, names)
    print("listx      zip stops at the shorter = ${pairs.len()} pairs")
    print("listx      pair(0) = ${pairs.get(0).first} and ${pairs.get(0).second}")

    val groups = listx.chunks(xs, 3)
    print("listx      chunks of 3 = ${groups.len()} groups, first has ${groups.get(0).items.len()}")

    // sort_by works for any element type, here descending.
    listx.sort_by(xs, fun(a: &i32, b: &i32) => bool = a > b)
    print("listx      sorted descending = ${xs.get(0)} ${xs.get(1)} ${xs.get(2)} ${xs.get(3)}")

    // Sets: insertion order is preserved, so these print in a stable order.
    var left: set.Set<i32> = set.new()
    left.insert(1)
    left.insert(2)
    left.insert(3)

    var right: set.Set<i32> = set.new()
    right.insert(3)
    right.insert(4)

    val both = set.union(left, right)
    val shared = set.intersect(left, right)
    val only_left = set.difference(left, right)
    print("set        union = ${both.len()} members")
    print("set        intersect = ${shared.len()} members")
    print("set        difference = ${only_left.len()} members")
    print("set        has(2) = ${left.has(2)}")

    var words: set.StrSet = set.new_str()
    words.insert("alpha")
    words.insert("beta")
    words.insert("alpha")
    val list = words.to_list()
    print("set        StrSet keeps 2 of 3 inserts: ${list.len()}")
    print("set        first member = ${list.get(0).as_str()}")
}
```

## Run it

```sh
kelpc run list-and-set-helpers.kp
```

## Output

```
listx      sum = 7
listx      min = 1
listx      max = 3
listx      fold(+, 0) = 7
listx      unique = 3 distinct values
listx      first index of 2 = 2
listx      zip stops at the shorter = 3 pairs
listx      pair(0) = 3 and 10
listx      chunks of 3 = 2 groups, first has 3
listx      sorted descending = 3 2 1 1
set        union = 4 members
set        intersect = 1 members
set        difference = 2 members
set        has(2) = true
set        StrSet keeps 2 of 3 inserts: 2
set        first member = alpha
```

## What to take from it

- **A closure parameter is written `&T`, and a `Copy` element is used directly
  inside the literal.** `fun(acc: i32, x: &i32) => i32 = acc + x` needs no `*x`.
  Writing `*x` is an error, not a style choice.
- **`fold` threads an accumulator of any type, owned included,** while `zip` and
  `chunks` need `Copy` elements because they build new containers out of what
  `get` hands back.
- **`chunks` wraps each run in a one-field `datac`** (`Chunk<T>`), a named
  element type, the same shape `csv.Row` and `table.Row` use. `List<List<T>>` is
  legal, but `chunks` returns `List<Chunk<T>>`.
- **`sort_by` is an insertion-selection hybrid over `remove`/`insert`,** which is
  what makes it work for owned elements, at the cost of O(n²) comparisons.
- **`position_i32` returns an `Option`,** so a missing value is a `None` rather
  than a `-1` sentinel.
- **`Set<T>` is for `Copy` keys and `StrSet` is the `String` twin,** because a
  `String`-keyed `Map` takes its key as a bare `str` while a scalar key is taken by
  value. One generic set cannot serve both.
- **Membership order is insertion order,** which is what makes the printed
  results stable across runs.

## See also

- [`listx`](/libraries/listx) and [`set`](/libraries/set)
- [Collections](/language/collections) for the builtin `List`, `Map` and `Box`
- [`std/list`](/stdlib/list) for `map`, `filter`, `each`, `find_index`, `any`, `all`
