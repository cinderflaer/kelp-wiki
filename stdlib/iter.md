---
title: "`std/iter`"
description: "The Iterator trait that `for` walks, the half-open Range, the owned list iterator, the count, sum_i64 and collect_list drains, and the map, filter, take, skip, enumerate, zip and chain adapters. Pure Kelp, ungated."
isPublished: true
tags: "stdlib"
---
The `Iterator` trait that `for x in it` walks, the half-open `Range`, and three
helpers that drain an iterator. Ungated.

```kelp
impl "std/iter"
```

The module is pure Kelp, builds in a freestanding image where `std/option` does
(only `collect_list` waits for an allocator), and is why a `for` over a range
costs no libc: `Range.next` is an ordinary method and the loop is an ordinary
`while` by the time either backend sees it. The language side, including
`break` and `continue`, is [Iterators, `for` and `break`](/language/iterators).

## Surface

```kelp
pub trait Iterator {
    type Item
    fun mut Self.next().return: option.Option<Self::Item>
}

pub datac Range(var lo: i64, val hi: i64, val step: i64)
pub fun range(a: i64, b: i64).return: Range
pub fun range_step(a: i64, b: i64, step: i64).return: Range

pub fun count<I: Iterator>(it: move I).return: usize
pub fun sum_i64<I: Iterator>(it: move I).return: i64
pub fun collect_list<I: Iterator>(it: move I).return: List<I::Item>
```

| Item | Notes |
| --- | --- |
| `Iterator` | `next` hands back one **owned** item; `None` ends the loop. A type opts in with `impl iter.Iterator for T` and binds `type Item` |
| `Range` | `[lo, hi)` stepping by `step`; a negative step walks down and stops at `hi` from above. It owns nothing, so it needs no allocator |
| `range(a, b)` | step 1; an empty range yields nothing |
| `range_step(a, b, step)` | explicit step. A step of `0` is not rejected: it is treated as a descending step, so `range_step(0, 5, 0)` is empty and `range_step(5, 0, 0)` never advances |
| `count(it)` | how many items remain, by draining |
| `sum_i64(it)` | the sum; the item type must be `i64`, and any other item type is a type error at the addition |
| `collect_list(it)` | drains into a `List<I::Item>`, in order |

Each helper takes the iterator by `move`.

## Example

```kelp
impl "std/iter"

fun main() {
    for i in iter.range(0, 5) {
        print!("$i ")
    }
    print("")
    for i in iter.range_step(10, 0, -3) {
        print!("$i ")
    }
    print("")
    print(iter.count(iter.range(0, 10)))
    print(iter.sum_i64(iter.range(1, 5)))
    val l = iter.collect_list(iter.range(3, 6))
    print(l.get(2))
}
```

Output, on both backends:

```
0 1 2 3 4 
10 7 4 1 
10
10
5
```

## The list iterator and the adapters

```kelp
iter.into_iter(xs: move List<T>) -> ListIter<T>      // owned items, front to back
iter.cloned(xs: &List<T>) -> ListIter<T>             // a copy of a borrowed list
iter.map(it, f)        -> MapIter<..>     // f: closure(&Item) -> U
iter.filter(it, pred)  -> FilterIter<..>  // pred: closure(&Item) -> bool
iter.take(it, n)       -> TakeIter<..>    // at most the first n
iter.skip(it, n)       -> SkipIter<..>    // the items after the first n
iter.enumerate(it)     -> EnumerateIter<..>   // (usize, Item), from 0
iter.zip(a, b)         -> ZipIter<..>     // (A::Item, B::Item), stops at the shorter
iter.chain(a, b)       -> ChainIter<..>   // all of a, then all of b (same item type)
```

Each takes its iterator by `move` and is itself an `Iterator`, so they nest
(`iter.take(iter.filter(iter.into_iter(xs), keep), 3)`). A `for` over an adapter
needs it in a `var` (or a temporary), as for any iterator that advances. The
adapters are generic `datac`s with a `next` method; a generic type with such a
`next` is an iterator by shape, which is why none of them needs a generic trait
impl ([Iterators](/language/iterators#what-is-not-there-yet)).

## Not in the module

- **A borrowing `List.iter()`** yielding `&T`: `into_iter` moves the list in, and
  `cloned` walks a copy.
- `fold`, `any`, `all`, `find` and the other consumers beyond `count`, `sum_i64`
  and `collect_list`.

## See also

- [Iterators, `for` and `break`](/language/iterators)
- [Associated types](/language/associated-types)
- [`std/option`](/stdlib/option)
