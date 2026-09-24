---
title: "`listx`: `List<T>` ergonomics"
description: "The list operations std/list deliberately stops short of - fold, zip, chunks, sort_by, sum/min/max, unique, position."
isPublished: true
tags: "library, collections"
---
The list operations `std/list` deliberately stops short of: `fold`, `zip`,
`chunks`, `sort_by`, `sum`/`min`/`max`, `unique`, `position`.

No capability.

```toml
[dependencies]
listx = "Juniper/fpl/listx"
```

```kelp
impl "deps/listx/lib"
```

## Types

```kelp
datac Pair<A, B>(val first: A, val second: B)
datac Chunk<T>(val items: List<T>)
```

`zip` returns `List<Pair<A, B>>` and `chunks` returns `List<Chunk<T>>`, so each
element is a named type: `Pair` is a two-field `datac` and `Chunk<T>` wraps one
`List<T>`. `List<List<T>>` is legal, but the named element is the shape these
functions ship.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `fold<T, A>(xs: &List<T>, init: move A, f: closure(move A, &T).R: A)` | `A` | left to right: `fold([1,2,3], 0, add)` = `add(add(add(0,1),2),3)`. Works for any element and accumulator type, owned included |
| `zip<A, B>(xs: &List<A>, ys: &List<B>)` | `List<Pair<A, B>>` | stops at the shorter list; `A`/`B` must be `Copy` |
| `chunks<T>(xs: &List<T>, size: usize)` | `List<Chunk<T>>` | runs of `size`, last one short; `T` must be `Copy` |
| `sort_by<T>(xs: mut List<T>, cmp: closure(&T, &T).R: bool)` | `Unit` | in place; `cmp(a, b)` true means `a` belongs before `b`. Any element type, owned included |
| `position_i32(xs, want)` / `position_i64(xs, want)` | `option.Option<usize>` | first index equal to `want` |
| `unique_i32(xs)` / `unique_i64(xs)` | `List<i32>` / `List<i64>` | distinct, first occurrence kept, order preserved |
| `unique_string(xs: &List<String>)` | `List<String>` | the same, cloning each kept element |
| `sum_i32`, `sum_i64`, `sum_f64` | that numeric type | 0 for an empty list |
| `min_i32`, `min_i64`, `min_f64` | that numeric type | **panics** on an empty list |
| `max_i32`, `max_i64`, `max_f64` | that numeric type | **panics** on an empty list |

## Why the type is in the name

A user module cannot overload a function name (`syntax.md` §7.2, overloading is
stdlib-only), so where the standard library would write one `sum`/`min`/`max`
per numeric type, this library spells the type into the name:
`sum_i32`, `min_i64`, `max_f64`.

## Cost

- `sort_by` is an insertion-selection hybrid over `remove`/`insert`, so it
  works for any element type, owned included, but it is O(n²) comparisons and
  O(n²) element moves. It is for an order the type does not define; `List.sort`
  is the builtin one and uses the element's own order (a scalar, or a `datac`'s
  fields).
- `unique_*` is O(n²) membership testing against the list built so far.
- `fold`, `zip` and `chunks` are single passes.

## Example

```kelp
impl "deps/listx/lib"
impl "std/option"

fun main() {
    var xs: List<i32> = List.empty()
    xs.push(3)
    xs.push(1)
    xs.push(2)
    print(listx.sum_i32(xs))
    print(listx.min_i32(xs))
    print(listx.max_i32(xs))
    print(listx.fold(xs, 0, fun(acc: i32, x: &i32).R: i32 = acc + x))
    val at = listx.position_i32(xs, 2)
    print(option.is_some(o = at))
    print(listx.unique_i32(xs).len())

    var ys: List<i32> = List.empty()
    ys.push(9)
    ys.push(9)
    val pairs = listx.zip(xs, ys)
    print(pairs.len())
    print(pairs.get(0).first)
    print(pairs.get(0).second)

    val groups = listx.chunks(xs, 2)
    print(groups.len())
    print(groups.get(1).items.len())

    listx.sort_by(xs, fun(a: &i32, b: &i32).R: bool = a > b)
    print(xs.get(0))
}
```

Output:

```
6
1
3
6
true
3
2
3
9
2
1
3
```

## Notes

- The closure parameter is written `&T` in the signature, but inside the literal
  a `Copy` element is used directly (`acc + x`, `a > b`): no `*` deref.
- `listx.fold(xs, 0, ...)` takes `init` by `move`; a `Copy` accumulator is
  copied, an owned one is moved in and moved through each step.
- There is no `sort`, `filter`, `map`, `any`, `all` or `find_index` here: those
  are builtin `List` methods or `std/list` free functions. `sort_by` exists
  because the builtin `List.sort` orders by the element's own order (a scalar,
  or a `datac`'s fields) and cannot take a comparator.
