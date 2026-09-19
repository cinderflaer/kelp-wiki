# Lexical structure

Source section:
[`syntax.md` §2](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md).

## Comments

`//` starts a line comment. There are **no block comments** (§2.1).

```kelp
// one line, written as a full sentence when it explains a decision
val limit = 10   // trailing comments are the same thing
```

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
ordinary identifier. `in` is not a keyword either — `for x in xs` reads it as a
separator, so a binding may be named `in`.

## Literals

```kelp
val a = 42              // integer literal
val b = 3.5             // float literal
val c = true            // bool literal
val d = "text\n"        // string literal
val e = 'x'             // character literal
val f = "n = $a, sum = ${a + 1}"   // string template
```

- **Integer literals are decimal digits only**: no suffix, no hex, no digit
  separators. A literal has no width of its own — it takes the integer type its
  context requires, and `i32` when nothing determines it. To write a bit pattern
  you write the decimal value (`192`, `128`) or compute it.
- **Float literals** are `digits.digits`, and are `f64` unless the context
  requires `f32`.
- A **character literal** is one Unicode scalar value in single quotes: `'x'`,
  `' '`, `'"'`, `'é'`, `'中'`. It takes the integer type its context requires and
  is `char` when nothing determines one — which is why byte-level code reads the
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
- **String literals** use the escapes `\n`, `\t`, `\r`, `\\`, `\"` and
  `\u{...}`. The set is closed: there is no `\x1b`, which is why the `term`
  library builds its ESC byte as `'\u{1b}'`.

## String templates

A template is a string literal containing `$name` or `${expr}` (§2.5):

```kelp
print("area = ${c.area()}")
print("r = $c.r")            // $name names an identifier, nothing more
```

`$name` interpolates one identifier; `${...}` interpolates any expression, and
the expression may contain a nested template or span several lines.

!!! warning "A template is not a value"
    The only place a template may appear is as the single argument of `print` or
    `print!`. To build a string with the same content, use `str.concat`, `fmt.*`
    or a `String`.

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

- [Types](types.md)
- [Operators and expressions](expressions.md)
- [Grammar summary](grammar.md)
