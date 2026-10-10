---
title: "Recursive Fibonacci"
description: "The first twenty Fibonacci numbers on one line, computed recursively: the smallest program with a function, a loop and two kinds of output."
isPublished: true
tags: "example"
---

The `recursive-fibonacci` program prints the first twenty Fibonacci numbers on one line.
It computes them recursively.
It is the smallest example with a function, a loop and two kinds of output.

| | |
| --- | --- |
| Source | [`src/recursive-fibonacci.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki-wikijs/raw/branch/main/examples/src/recursive-fibonacci.kp) |
| Needs | nothing, not even the standard library |
| Shows | recursion, `while`, `.return: i64`, `print` versus `print!` |

## The program

```kelp
fun fib(n: i64).return: i64 {
    if n < 2 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}

fun main() {
    var i: i64 = 0
    while i < 20 {
        print!(fib(i))
        if i < 19 {
            print!(" ")
        }
        i += 1
    }
    print("")
}
```

## Run it

```sh
kelpc run recursive-fibonacci.kp
```

## Output

```
0 1 1 2 3 5 8 13 21 34 55 89 144 233 377 610 987 1597 2584 4181
```

## What to take from it

- **The return type is written `.return: i64`** after the parameter list. There is no
  `->`, and no inferred return type for a block body.
- **`print!` does not add a newline, `print` does.** The final `print("")` is what
  ends the line; a program that leaves the last line unterminated is a program
  whose shell prompt lands mid-line.
- **Both the parameter and the loop counter are `i64` on purpose.** Integer widths
  are distinct types and nothing promotes them, so `fib(i)` with an `i32` counter
  would be a type error; the conversion, if needed, is `i.to_i64()`.
- **Recursion is unrestricted.** This one is exponential; it is here to be read,
  not to be pasted into something that needs the fortieth number.

## See also

- [Functions](/language/functions) and [Control flow](/language/control-flow)
- [Text](/language/text) for what `print` accepts
