---
title: "Grammar summary"
description: "Reproduced from syntax.md \u00a720, which is the authority. Note that View is an ordinary identifier here - it is a builtin type name like str or String, not a keyword."
isPublished: true
tags: "language"
---
Reproduced from
[`syntax.md` §20](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md),
which is the authority. Note that `View` is an ordinary identifier here: it is a
builtin type name like `str` or `String`, not a keyword.

```
program      := line* EOF
line         := impl | const | pd | datac | enum | fun

impl         := "impl" string [ "as" ident ] [ "with" "caps" "(" grant ("," grant)* ")" ]
grant        := ident "=" "[" string ("," string)* "]"
const        := "const" ident ":" type "=" expr
pd           := "pd" ("val" | "var") ident [ ":" type ] "=" expr
datac        := "datac" ident [ typeparams ] "(" [ field ("," field)* ] ")"
field        := ("val" | "var") ident ":" type
enum         := "enum" ident [ typeparams ] "{" ( ident [ "(" [ field ("," field)* ] ")" ] )* "}"
typeparams   := "<" ident ("," ident)* ">"
typeargs     := "<" type ("," type)* ">"   // in an expression: adjacent to the name and to "("
fun          := [ "extern" ] "fun" [ "mut" ] ( ident [ typeparams ] "." )? ident [ typeparams ]
                "(" [ param ("," param)* ] ")" [ ".R" ":" type ] body
param        := ident ":" [ "mut" | "move" ] type
body         := "=" expr | block | <nothing for extern>

type         := [ "&" ] ( ident [ "<" type ("," type)* ">" ] [ "." ident ]
                       | "fun" "(" [ fparam ("," fparam)* ] ")" [ ".R" ":" type ] )
fparam       := [ "mut" | "move" ] type
```

```
stmt         := "val" | "var" | "while" | "for" | "return" | expr
val          := "val" ident [ ":" type ] "=" expr
var          := "var" ident [ ":" type ] "=" expr
while        := "while" expr block
for          := "for" ident "in" expr block   // the `in` is contextual, not a keyword
return       := "return" [ expr ]
block        := "{" (line-separated stmt)* "}"

expr         := assign
assign       := binary ( ( "=" | "+=" | "-=" | "*=" | "/=" | "%=" ) assign )?
binary       := unary ( binop binary )?
binop        := "||" | "&&" | "==" | "!=" | "<" | "<=" | ">" | ">="
              | "|" | "^" | "&" | "<<" | ">>"       // << and >> are two adjacent < / > characters
              | "+" | "-" | "*" | "/" | "%"
unary        := ( "-" | "!" | "~" | "&" [ "mut" ] | "*" ) unary | postfix
postfix      := primary ( "?" | "." ident [ typeargs ] [ "(" args ")" ] )*
primary      := int | float | string | char | template | "true" | "false"
              | "fun" "(" [ param ("," param)* ] ")" [ ".R" ":" type ]
                ( "=" expr | block )
              | ident [ typeargs ] [ "(" args ")" ] | "(" expr ")" | block
              | "if" expr block chain
              | "if" "let" ident [ "(" (ident | "_") ("," (ident | "_"))* ")" ] "=" expr
                block chain
              | "when" "{" ( expr "->" expr )* "else" "->" expr "}"
char         := "'" ( <any Unicode scalar value except ' and newline>
                    | "\n" | "\t" | "\r" | "\0" | "\'" | "\"" | "\\"
                    | "\u{" hexdigit+ "}" ) "'"
args         := [ arg ("," arg)* ]
arg          := [ ident "=" ] expr
chain        := [ "elif" expr block chain
                | "elif" "let" ident [ "(" (ident | "_") ("," (ident | "_"))* ")" ] "=" expr
                  block chain
                | "else" ( block | "if" expr block chain
                         | "if" "let" ident [ "(" (ident | "_") ("," (ident | "_"))* ")" ] "=" expr
                           block chain ) ]
```

## Reading it

- `line` is what a top-level file holds, and the parser enforces the order the
  productions appear in: imports first, then declarations.
- `postfix` carries the three postfix forms: `?`, field access, and a call, which
  is why `f(x)?` and `a.b.c(1)` both parse.
- `primary` includes `block` and `if`/`when` as expressions, which is how
  `val label: String = if flag { "yes" } else { "no" }` works.
- `chain` is what follows the first block of an `if` or an `if let`: nothing, an
  `else` block, or another link. A link is written `elif` (the preferred
  spelling) or `else if`, so a chain may mix the two; a chain that produces a
  value needs the `else` block at its end.
- `typeargs` is written **adjacent** to the name and to the `(`:
  `Pair<i32, String>(…)`. Write a space before `<` when you mean a comparison.

## See also

- [Lexical structure](/language/lexical)
- [Types](/language/types)
- [Operators and expressions](/language/expressions)
