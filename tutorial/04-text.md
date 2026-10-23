---
title: "Text"
description: "str and String, templates, building and splitting text, and parsing numbers, with the refusal every newcomer meets: a String is not a str."
isPublished: true
tags: "tutorial, language, text"
---
**You will learn:** the two text types Kelp uses, how to build and join text, and
how to read a number out of text.

## The program

```kelp
impl "std/fmt"
impl "std/str"

fun shout(s: &str) => String {
    var out = String.empty()
    out.push_str(s)
    out.push_str("!")
    return out
}

fun main() {
    val name = "Kelp"
    print("hello, ${name}")

    val owned = String.from_str(s = "owned text")
    print(owned)
    print("length ${str.len(owned.as_str())}")

    val loud = shout("hey")
    print(loud)

    val digits = fmt.int(42)
    print(str.concat("total: ", digits.as_str()))

    val parts = str.split("a,b,c", ",")
    print("parts ${parts.len()}")
    print(parts.get(1))

    val n = str.parse_i64(s = "41")
    if let Ok(v) = n {
        print(v + 1)
    }
    val bad = str.parse_i64(s = "x1")
    if let Err(e) = bad {
        print("not a number")
    }
    print("tab\tand\nnewline")
}
```

```text
hello, Kelp
owned text
length 10
hey!
total: 42
parts 3
b
42
not a number
tab	and
newline
```

## Two kinds of text

Kelp has two text types you will use every day:

- **`str`** is text that someone else owns. A string literal such as `"Kelp"` is
  a `str`, and so is a parameter declared `&str`. You can read it, but it must be
  built somewhere else.
- **`String`** is text that your variable owns. It is dropped when the variable
  goes out of scope. `String.from_str(s = "...")` makes one from a literal.

A `String` becomes a `str` with `.as_str()`, a borrow, so the `String` keeps
ownership. The `shout` function builds a `String` with `String.empty()` and
`push_str`, then returns it. The function's return type is `String`, so the
caller owns the result.

A string literal is assigned to a `String` without `from_str` in some places,
such as a struct field or a list element. The [text reference](/language/text)
lists those cases. This chapter uses the explicit forms so that you can see which
type you have.

## Templates

`"hello, ${name}"` is a template. Inside `print` it writes its text directly.
Outside `print` it is a `String`, so you can keep it, return it, or pass it where a
`String` is expected:

```kelp
fun label(n: i32) => String {
    return "n is ${n}"
}
```

`label(7)` returns the `String` `n is 7`. To build text a piece at a time, use
`str.concat`, the `fmt` functions, or a `String`.
`fmt.int(42)` turns a number into a `String`. Pass a borrow of it on with
`.as_str()`, and bind it to a variable first, as the program does. A call that
returns a borrow of a temporary value is refused, because the temporary would be
dropped before the borrow is used.

## Parsing a number

`str.parse_i64` reads an integer from text. It does not panic on bad input. It
returns a `Result`, which [Errors](/tutorial/07-errors) covers in full. You can
read the success case with `if let Ok(v) = n`, and the failure case with
`if let Err(e) = bad`.

## Try it

1. Write a function `fun twice(s: &str) => String` that returns `s` joined
   with itself, using `String.empty()`, `push_str` twice, and `return`.
2. Split `"red,green,blue"` with `str.split` and print the second item.

Next: [Records, enums and ownership](/tutorial/05-data).
