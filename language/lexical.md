---
title: "Lexical structure"
description: "The surface tokens of Kelp: comments and doc comments, line rules, keywords, literals and their escapes, string templates and operators."
isPublished: true
tags: "language"
---
Source: [`syntax.md` §2](/design/syntax).

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

### Documentation comments

`//!` and `///` are **documentation comments**: they document the declaration
that follows them, and they are the text `coral docs` reads. To the compiler
they are comments like any other, so nothing about them changes what a program
does:

```kelp
//! The buffer owns its bytes and drops them once, at the end of the owning
//! scope. Nothing here is a view: every getter copies.
datac Buffer(val bytes: Bytes)

/// How many characters a `&str` has, continuation bytes counted once.
fun char_count(s: &str) => usize
```

`//!` is read as the header of a block, so it has to start a line: consecutive
`//!` lines are one foldable unit above the declaration they document, and a `//!`
with code before it on the same line documents nothing and is a **compiler
error**:

```kelp
val n = 1   //! error: a '//!' is a documentation comment and must start a line
```

A documentation comment is exempt from the [comment-run rule](/language/style): a
run of doc lines is already one block, and a `//!` line does not count toward a
plain `//` run either.

#### Naming what a block documents

A block documents the declaration below it, which is what most blocks need. To
document something else, open the block with a **head**: one line,
`[docs(<kind>: <name>)]`, where `<kind>` is `module`, `fun`, `datac`, `enum`,
`const`, `field`, `variant` or `title`:

```kelp
//! [docs(title: "Error handling")]
//! Every fallible call returns a Result: there is no panic path here.

//! [docs(fun: Frame.decode)]
//! The frame decoder is what refuses a truncated frame.
```

`title` takes a quoted string, and is the kind for prose that belongs to no
declaration at all; every other kind takes a name as written in the source. The
closing `]` is what ends the head, so a head written open across lines is closed
by a `]` line of its own, which carries nothing and is dropped:

```kelp
//! [docs(fun: test)
//! The test function checks that a truncated frame is refused.
//! ]
```

A head is read by the tooling and never by the compiler, which does not see
inside a comment. A head the tool cannot read, an unknown kind or a `title:`
without quotes, is a warning from `coral docs` naming the file and line, not a
compile error.

#### Where the key comes from without a head

| Block sits above | Key |
| --- | --- |
| a `fun`, or an `extern fun` | `fun:name` |
| a `datac` or an `enum` | `datac:name`, `enum:name` |
| a `const` | `const:NAME` |
| a field, written `val` or `var` | `field:name` |
| a variant | `variant:Name` |
| the first declaration of a file, or its `impl` lines | `module:<file stem>` |

Those keys are what [Coral's docs commands](/tooling/coral#coral-docs) list,
search and print.

## Statements and whitespace

There are no semicolons. A newline ends a statement, and a statement must fit on
one line **unless it is inside parentheses** (§2.2):

```kelp
val c = Circle(r = 2.0, x = 1.0)     // ok
val area = c.area()                  // ok

print(math.pow(base = 2.0,
               exp = 8.0))           // wrapping inside ( ) is fine
```

A line that **ends in a binary or assignment operator** (`+ - * / && || = == != <= >=`
and the compound assignments), in `,`, in `.` or in a `when` arrow `->` continues on
the next line (from 26.10.3). A line that *starts* with an operator is a new
statement, so put the operator at the end of the line. Two statements on one line
need a separator, and without one it is an error.

```kelp
val total = base +
    tax                    // one statement
val n = xs.
    len()                  // a trailing `.` continues too
```

## Identifiers and keywords

An identifier starts with a letter or `_`. These are the keywords (§2.3):

```
as  closure  const  datac  elif  else  enum  extern  false  for  fun  if  impl
move  mut  pd  pub  return  trait  true  val  var  when  while
```

`fn`, `let`, `struct`, `use`, `loop`, `break`, `continue`, `match` and
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

- **Integer literals** are decimal, hexadecimal after `0x`, or binary after `0b`:
  `0xff`, `0b1010`. A radix literal is the same value as its decimal
  spelling (`0xff` is `255`), and like any literal it has no width of its own:
  it takes the integer type its context requires, and `i32` when nothing
  determines it, so `val mask: u8 = 0xff` and `val mask: u64 = 0xff` both work.
  A literal that does not fit the type its context asks for is refused at its own
  line, with a message naming a type that holds it: `val big = 4294967295` is an
  error, because nothing gives the literal a type and `i32` cannot hold it, so it
  is written `val big: u64 = 4294967295`. The widest literal that can be written
  is `u64::MAX`, `18446744073709551615`, because the scanner holds the whole
  `u64` range; a literal above it is refused by name rather than truncated. The same applies to a literal receiver,
  where the call supplies no expected type: `4294967295.to_u64()` is refused.
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
  `\n`, `\t`, `\r`, `\0`, `\'`, `\"`, `\\`, `\xNN` and `\u{...}`, plus `\$` in
  a string literal. What each
  form refuses is the shape it cannot hold: a string literal is NUL-terminated
  UTF-8, so it has no `\0` and no `\u{...}` and a byte above `0x7f` is not text
  (`"\xff"` is refused), and a byte literal is one byte, so it has no
  `\u{...}`.
- **A raw NUL byte in a string literal is refused where the `\x00` escape is**:
  `a 'str' is NUL-terminated, so a raw NUL byte cannot be in a string literal`.
  The `str` ends at that byte, so carrying it would truncate the literal in
  either backend instead of failing. It is a lexer rule, so it covers the whole
  literal, a template's text chunks included; a raw NUL in a comment or an
  identifier is untouched. This is also why a `Bytes` value built from a string
  literal cannot carry a NUL: arbitrary bytes are still what `Bytes` is for, and
  they are built (`Bytes.empty` and `push`), not written as text with a NUL in
  it.
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
the expression may contain a nested template or span several lines. `\$` is a
literal dollar sign: `"\$HOME"` is the five characters `$HOME`, an ordinary
string value rather than a template. A `$` followed by anything that is not a
name or `{` is already literal.

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
| separators and access | `.` `,` `:` `(` `)` `[` `]` `{` `}` |
| `when` arms only | `->` |
| character literal | `'` |
| byte literal | `b'` |

Two things are worth knowing up front:

- `&` is both the borrow prefix and bitwise-and; **position decides**:
  `&x` borrows, `a & b` masks.
- `<<` and `>>` are two adjacent characters, not one token, so a nested type
  argument list (`List<List<i32>>`) still closes.
- `[` and `]` form array literals and array types, and they hold lists in a
  capability grant (`caps(fs = ["/srv/**"])`).

## See also

- [Types](/language/types)
- [Operators and expressions](/language/expressions)
- [Grammar summary](/language/grammar)
