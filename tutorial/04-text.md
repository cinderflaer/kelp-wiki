---
title: "Tutorial 4: Text"
description: "Chapter 4 of the Kelp tutorial: str, View and String, templates, building and splitting text, parsing numbers, and the two refusals every newcomer meets: templates are not values, and String is not str."
isPublished: true
tags: "tutorial, language, text"
---
Text is where Kelp's ownership model first shows up in everyday code. Four types
carry text (`str`, `View`, `String`, `Bytes`); this chapter uses the first three.
The reference is [Text](/language/text) and [`std/str`](/stdlib/str).

| Type | What it is |
| --- | --- |
| `str` | a borrowed pointer to NUL-terminated UTF-8. A literal like `"hello"` is a `str`. It has no stored length |
| `View` | a borrowed pointer **and** a length: slices and scans cost nothing extra |
| `String` | owned, growable UTF-8, freed at the end of its scope |

## One program

```kelp
impl "std/str"
impl "std/fmt"
impl "std/result"

fun shout(s: &str).R: String = str.to_upper(s)

fun main() {
    // str: a borrowed literal. String: owned and growable.
    val lit = "kelp language"
    var out = String.empty()
    out.push_str("wrote ")
    out.push_str(lit)
    print(out)

    // a template interpolates numbers, str and String alike
    val n: i32 = 42
    val owned: String = "owned text"
    print("n=${n} lit=${lit} owned=${owned} sum=${n + 1}")

    // String -> str is a borrow
    print(shout(owned.as_str()))

    // a View knows its length and slices without allocating
    val v = lit.view()
    print("len ${v.len()} first byte ${v.get(0)}")
    print(v.slice(0, 4))

    // split, join, parse
    val parts = str.split("a,b,,c", ",")
    print("${parts.len()} pieces")
    print(str.join(parts, "-"))
    val parsed = str.parse_i64("41")
    if let Ok(x) = parsed {
        print("parsed ${x + 1}")
    }
    val bad = str.parse_i64("4x1")
    if let Err(e) = bad {
        print("not a number")
    }
    val seven = fmt.int(7)
    print(fmt.pad_left(seven.as_str(), 4, '.'))
    print(fmt.float(3.14159, 2))
    print("chars ${str.char_count("héllo")} bytes ${str.len("héllo")}")
}
```

```text
wrote kelp language
n=42 lit=kelp language owned=owned text sum=43
OWNED TEXT
len 13 first byte 107
kelp
4 pieces
a-b--c
parsed 42
not a number
...7
3.14
chars 5 bytes 6
```

Same output on the LLVM backend and with `KELPC_ORACLE=c`.

## What to take from it

**Templates.** `"n=${n}"` interpolates any scalar or text value, owned or borrowed,
and an expression is fine inside the braces (`${n + 1}`). Printing a float shows six
decimals. The `print` builtin takes exactly one argument; to print a mixture, use a
template.

**A template is not a value.** It can only be handed to `print` or `print!`.
This is the first surprise for people from Python:

```kelp
fun main() {
    val n = 3
    val label: String = "n is ${n}"
    print(label)
}
```

```text
$ kelpc check c4bad.kp
error: a string template can only be printed: pass it to 'print(...)' or 'print!(...)'; a template is not a value, so build the text with 'str.concat', 'fmt.*' or a 'String'
  --> c4bad.kp:3:25
```

To build text, use `String.empty()` and `push_str`, or `str.concat`, or the `fmt`
functions. The program did the first: `out.push_str(lit)`.

**`str` to `String` converts by itself, but only that way, and only where a
`String` is expected.** `val owned: String = "owned text"` copies the literal. The
other direction is a borrow you write out, `.as_str()`:

```kelp
impl "std/str"

fun main() {
    val s: String = "owned"
    print(str.len(s))
}
```

```text
$ kelpc check c4bad2.kp
error: argument 's' has type 'String', expected 'str' — there is no implicit conversion this direction (5.1 only goes the other way, 'str'/'View' to an owned 'String'); call `.as_str()` to borrow it
  --> c4bad2.kp:5:19
```

The message names the fix. Most `std/str` functions take `&str`, which is why
`shout(owned.as_str())` appears in the program.

**`View`.** `lit.view()` pays one `strlen` and then `len()`, `get(i)` and
`slice(from, to)` are constant time, and a slice allocates nothing. A `View` is
`Copy` but cannot be stored in a field or a list. Text you must keep is a `String`.

**Bytes versus characters.** `str.len` counts bytes. `"héllo"` is five characters and six
bytes, and the program printed both counts with `str.char_count` and `str.len`.
`to_upper` is ASCII only.

**Splitting, joining, parsing.** `str.split` keeps empty pieces: `"a,b,,c"`
is four pieces, and joining them with `-` gives `a-b--c`. `str.parse_i64`
returns a `Result` (chapter 7), tested here with `if let Ok(x) = ...`. `fmt.int`,
`fmt.float`, `fmt.pad_left` format numbers and pad them.

One trap the program had to dodge: `fmt.int(7)` is a temporary `String`, and
`fmt.pad_left` wants a `str`:

```kelp
impl "std/fmt"

fun main() {
    print(fmt.pad_left(fmt.int(7), 4, '.'))
}
```

```text
$ kelpc check c4bad3.kp
error: argument 's' has type 'String', expected 'str' — there is no implicit conversion this direction (5.1 only goes the other way, 'str'/'View' to an owned 'String'); call `.as_str()` to borrow it
  --> c4bad3.kp:4:24
```

Writing `.as_str()` on that temporary is refused as well, so bind the `String`
to a `val` first (`seven` in the program). The language page lists it under
[Two traps](/language/text#two-traps).

## Exercises

1. Split `"the quick brown fox"` on spaces and print the number of words and then
   each word with its length.
2. Build the text `1, 2, 3, 4` in a `String` in a loop. Mind the separator: it
   goes before every number but the first.

<details>
<summary>Solutions</summary>

1.

```kelp
impl "std/str"

fun main() {
    val line = "the quick brown fox"
    val words = str.split(line, " ")
    print("${words.len()} words")
    for w in words {
        print("${w} (${w.len()})")
    }
}
```

```text
4 words
the (3)
quick (5)
brown (5)
fox (3)
```

2.

```kelp
impl "std/str"
impl "std/iter"

fun main() {
    var out = String.empty()
    for i in iter.range(1, 5) {
        if i > 1 {
            out.push_str(", ")
        }
        val piece = str.from_i64(i)
        out.push_str(piece.as_str())
    }
    print(out)
}
```

```text
1, 2, 3, 4
```

</details>

Next: [Records, enums and methods](/tutorial/05-data).
