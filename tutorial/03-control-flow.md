---
title: "Control flow"
description: "if, elif and if as a value, while, for over arrays and ranges, break and continue, and return, with the real output of each program."
isPublished: true
tags: "tutorial, language"
---
**You will learn:** how to choose between paths with `if`, repeat with `while` and
`for`, and leave early with `break`, `continue` and `return`.

## The program

```kelp
impl "std/iter"

fun sign(n: i32) => &str {
    if n > 0 {
        return "positive"
    } elif n < 0 {
        return "negative"
    }
    return "zero"
}

fun main() {
    for n in [3, -2, 0] {
        print(sign(n))
    }

    var i: i32 = 1
    while i <= 3 {
        print("tick ${i}")
        i += 1
    }

    val xs = [10, 20, 30]
    for x in xs {
        if x == 20 {
            continue
        }
        print("x = ${x}")
    }

    for k in iter.range(0, 10) {
        if k == 2 {
            break
        }
        print("k = ${k}")
    }

    val label: String = if i > 3 { "done" } else { "not yet" }
    print(label)
}
```

```text
positive
negative
zero
tick 1
tick 2
tick 3
x = 10
x = 30
k = 0
k = 1
done
```

## Branches

`if` works as it does in most languages, with `elif` for another condition. The
condition must be a `bool`. Writing `if n` for an integer is an error:

```text
$ kelpc check ifn.kp
error: if condition must be 'bool', found 'i32'
  --> ifn.kp:3:5
```

so a test is always a comparison.

`if` can also produce a value, as the `label` line does. A value-producing `if`
needs an `else`, and both branches must produce the same type.

`return` leaves the function immediately. The `sign` function uses it in each
branch, which is the usual style for a function with several exits.

## Loops

- `while` repeats while its condition is true. The condition is checked before
  each pass.
- `for x in xs` walks a list or an array one element at a time. `x` is a copy
  for a number, and a borrow of the element otherwise.
- `iter.range(0, 10)` produces the numbers from 0 up to 10, but not including 10.
  It needs `impl "std/iter"`. Ranges and other iterators are covered again in the
  [closures and iterators](/tutorial/10-closures) chapter.
- `break` leaves the loop. `continue` skips to the next pass.

A `for` loop does not let its body change the list it is walking: a `push` or
`remove` on that same list is a compile error. When the loop has to change its
list, walk it by index with `while` instead. The [control flow reference](/language/control-flow#for)
has the rule.

## Try it

1. Add a `while` loop that prints the numbers from 10 down to 1 by subtracting 3
   each time. Which numbers print?
2. Add a case to `sign` that returns `"huge"` when `n` is over 1000. Where must
   that check go so that it runs before the `"positive"` case?

Next: [Text](/tutorial/04-text).
