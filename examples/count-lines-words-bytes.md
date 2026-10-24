---
title: "Count lines, words and bytes"
description: "Prints the line, word and byte counts of one file: the smallest example that does real work with a file, and the closest to a shell one-liner (wc)."
isPublished: true
tags: "example"
---

The `count-lines-words-bytes` program prints the line, word and byte counts of one file.
It is the smallest example that does real work with a file.
It is the closest of the examples to a shell one-liner, `wc`.

| | |
| --- | --- |
| Source | [`src/count-lines-words-bytes.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki-wikijs/raw/branch/main/examples/src/count-lines-words-bytes.kp) |
| Needs | nothing but the standard library (the `fs` capability) |
| Shows | reading text, a byte loop over a `str`, `fmt` and `str.concat` for output |

## The program

```kelp
impl "std/fs"
impl "std/str"
impl "std/fmt"
impl "std/process"

fun is_space(c: u8) => bool = c == ' ' || c == '\t' || c == '\n' || c == '\r'

fun report(label: &str, n: i64) {
    val padded = fmt.pad_right(label, 8, ' ')
    val count = fmt.int(n)
    print(str.concat(padded.as_str(), count.as_str()))
}

fun main() {
    val argv = process.args()
    if argv.len() < 2 {
        print("usage: count-lines-words-bytes <file>")
        process.exit(2)
    }

    val path = argv.get(1)
    val text = fs.read_text(path.as_str())
    val s = text.as_str()
    val bytes = str.len(s)

    var lines: i64 = 0
    var words: i64 = 0
    var in_word = false
    var i: int = 0
    while i < bytes {
        val c = str.byte(s, i)
        if c == '\n' {
            lines += 1
        }
        if is_space(c) {
            in_word = false
        } else if !in_word {
            words += 1
            in_word = true
        }
        i += 1
    }

    // A file whose last line has no newline still counts as one line.
    if bytes > 0 && str.byte(s, bytes - 1) != '\n' {
        lines += 1
    }

    report("lines", lines)
    report("words", words)
    report("bytes", bytes.to_i64())
}
```

## Run it

The program takes an absolute path, because the language has no way to read the
current directory. The run passes `$PWD/input.txt` for that reason.

```sh
printf 'the quick brown fox\njumps over the lazy dog\nand again\n' > input.txt
kelpc build count-lines-words-bytes.kp -o count-lines-words-bytes && ./count-lines-words-bytes "$PWD/input.txt"
```

## Output

```
lines   3
words   11
bytes   54
```

## What to take from it

- **Text is bytes.** `str.len` and `str.byte` count and index bytes; `str.char_count`
  would be the codepoint-oriented pair. The whole loop is `u8` work.
- **A character literal takes the type its context needs**, which is why
  `if c == '\n'` needs no cast: `c` is a `u8`, so the literal is one.
- **Output is built, not concatenated with `+`.** There is no `+` on strings:
  `str.concat(a, b)` allocates, `fmt.*` formats, and `String.push_str` appends in
  place. Note that `fmt.pad_right(...)` and `fmt.int(...)` are bound to `val`s
  before `.as_str()` is taken: `.as_str()` on a temporary is refused.
- **`process.exit(2)` is the only way to fail a program by exit code**
  ([`panic`](/language/errors) also exits non-zero, with a message).
- **The entry module holds the wildcard for every domain**, so this program needs
  no grant for `fs`. A module that is *not* the entry module would: see
  [sandbox-directory-grant](/examples/sandbox-directory-grant).

## See also

- [`std/fs`](/stdlib/fs) for the read/write/walk surface
- [`std/str`](/stdlib/str) and [`std/fmt`](/stdlib/fmt)
- [Text](/language/text) for `str` versus `String` versus `View`
