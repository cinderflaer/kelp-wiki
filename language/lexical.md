---
title: "Lexical structure"
description: "Source section - syntax.md \u00a72."
isPublished: true
tags: "language"
---
Source section:
[`syntax.md` §2](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

## Comments

`//` starts a line comment, and `/* ... */` a block comment (§2.1).

```kelp
// one line, written as a full sentence when it explains a decision
val limit = 10   // trailing comments are the same thing

/* a block comment: one line, or several
   lines of prose */
```

A block comment ends at its own `*/`, and block comments **nest**: an inner `/*`
needs its own `*/`. That is what makes commenting out a region which already
contains a block comment work; C's first-`*/`-wins rule is what would turn it
into a parse error further down the file. An unbalanced `/*` is reported as an
*unterminated block comment*, at the opening delimiter.

Neither form is a token: both are trivia, so a comment may sit wherever
whitespace may, and `kelpc fmt` copies it verbatim. Delimiters inside a string or
character literal are ordinary text, so `"a/*b*/c"` is the bytes `a/*b*/c`.

## Statements and whitespace

There are no semicolons. A newline ends a statement, and a statement must fit on
one line **unless it is inside parentheses** (§2.2):

```kelp
val c = Circle(r = 2.0, x = 1.0)     // ok
val area = c.area()                  // ok

print(math.pow(base = 2.0,
               exp = 8.0))           // wrapping inside ( ) is fine
```

A trailing operator does **not** continue a line, and two statements on one line
with no separator is an error.

## Identifiers and keywords

An identifier starts with a letter or `_`. These are the keywords (§2.3):

```
as  closure  const  datac  else  enum  extern  false  for  fun  impl  move
mut  pd  return  true  val  var  when  while
```

`fn`, `let`, `struct`, `use`, `loop`, `break`, `continue`, `match`, `trait` and
`self` are **not** keywords: writing `fn` is a parse error, and `self` is an
ordinary identifier. `in` is not a keyword either: `for x in xs` reads it as a
separator, so a binding may be named `in`.

## Literals

```kelp
val a = 42              // integer literal
val b = 3.5             // float literal
val c = true            // bool literal
val d = "text\n"        // string literal
val e = 'x'             // character literal
val f = "n = $a, sum = ${a + 1}"   // string template
val g = 0xff            // integer literal, hexadecimal
val h = 0b1010          // integer literal, binary
val i = b'x'            // byte literal
```

- **Integer literals** are decimal, or hexadecimal after `0x` and binary after
  `0b`: `0xff`, `0b1010`. A radix literal is the same value as its decimal
  spelling (`0xff` is `255`), and like any literal it has no width of its own:
  it takes the integer type its context requires, and `i32` when nothing
  determines it, so `val mask: u8 = 0xff` and `val mask: u64 = 0xff` both work.
  There is no suffix (`5u8` is an error: the width comes from where the literal
  sits) and no digit separator, and there is no octal form. A malformed one is
  refused by name: `0b12` is "invalid digit '2' in a binary literal".
- **Float literals** are `digits.digits`, and are `f64` unless the context
  requires `f32`.
- A **character literal** is one Unicode scalar value in single quotes: `'x'`,
  `' '`, `'"'`, `'é'`, `'中'`. It takes the integer type its context requires and
  is `char` when nothing determines one, which is why byte-level code reads the
  way it thinks:

  ```kelp
  val ch: u8 = str.byte(text, i)
  if ch == '"' { }           // not `ch == 34`
  if ch == '\\' { }          // not `ch == 92`
  out.push(' ')              // not `out.push(32)`
  val digit: u8 = '0' + n    // not `48 + n`
  ```

  A code point that does not fit the type the context asks for is a **compile
  error**, not a truncation: `val ch: u8 = '中'` is refused by name.
- **A byte literal** is `b'x'`: one ASCII character or a `\xNN` escape, and a
  `u8` **by construction**. That is what it is for: `val nl = b'\n'` needs no
  type written anywhere, which the character-literal spelling (`val nl: u8 =
  '\n'`) does. It does not take the type its context asks for, so `val n: i64 =
  b'x'` is refused rather than widened: write `'x'` when the type should come
  from where the literal sits. A non-ASCII character is a code point, so it
  belongs in a character literal (`b'é'` is refused, and `b'\xe9'` is the byte
  233).
- **String, character and byte literals** use this escape set (grammar §20):
  `\n`, `\t`, `\r`, `\0`, `\'`, `\"`, `\\`, `\xNN` and `\u{...}`. What each
  form refuses is the shape it cannot hold: a string literal is NUL-terminated
  UTF-8, so it has no `\0` and no `\u{...}` and a byte above `0x7f` is not text
  (`"\xff"` is refused), and a byte literal is one byte, so it has no
  `\u{...}`.
- **`\xNN` is exactly two hex digits**, in every literal form, so it cannot run
  on into the text after it: `"\x41a"` is `"Aa"`, where C's hex escape
  swallows the `a`. In a character literal it is the code point (`'\x41'` is
  `'A'`); in a byte literal it is the byte (`b'\xff'` is 255).

## String templates

A template is a string literal containing `$name` or `${expr}` (§2.5):

```kelp
print("area = ${c.area()}")
print("r = $c.r")            // $name names an identifier, nothing more
```

`$name` interpolates one identifier; `${...}` interpolates any expression, and
the expression may contain a nested template or span several lines.

> **A template is not a value**
>
> The only place a template may appear is as the single argument of `print` or
> `print!`. To build a string with the same content, use `str.concat`, `fmt.*`
> or a `String`.

## Operators

The complete operator set (§2.6):

| Group | Operators |
| --- | --- |
| arithmetic (and unary minus) | `+` `-` `*` `/` `%` |
| bitwise | `&` `\|` `^` `<<` `>>` `~` |
| comparison | `==` `!=` `<` `<=` `>` `>=` |
| logic | `&&` `\|\|` `!` |
| assignment | `=` `+=` `-=` `*=` `/=` `%=` |
| references | `&` `&mut` `*` |
| propagation | `?` |
| separators and access | `.` `,` `:` `(` `)` `{` `}` |
| `when` arms only | `->` |
| character literal | `'` |

Two things are worth knowing up front:

- `&` is both the borrow prefix and bitwise-and; **position decides**:
  `&x` borrows, `a & b` masks.
- `<<` and `>>` are two adjacent characters, not one token, so a nested type
  argument list (`List<List<i32>>`) still closes.
- `[` and `]` are lexed but no expression uses them; they exist for capability
  grant lists.

## See also

- [Types](/language/types)
- [Operators and expressions](/language/expressions)
- [Grammar summary](/language/grammar)
