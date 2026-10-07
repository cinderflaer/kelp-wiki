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
line         := impl | trait | traitimpl | const | pd | datac | enum | fun

impl         := "impl" string [ "caps" "(" ( grant ( "," grant )* | "*" ) ")" ]
                // `caps(*)` (15.2) delegates the whole resource of every domain and
                // stands alone: a named domain beside the `*` is refused by name.
                // `as name` was removed (13.1) and `with caps(...)` with it (15.2):
                // the parser refuses each by name, and `as` stays a keyword
grant        := ident "=" "[" string ("," string)* "]"
// A leading "pub" (13.4) is accepted on trait, const, datac, enum and fun, and
// nowhere else: a `pd` is module-scoped and an import is not an item.
// `trait`/`traitimpl` (9.5): a trait is a set of methods, an impl gives them
// to a `datac`/`enum` or to a builtin. "Self" is an ordinary identifier used
// as a type name in both, and stands for the implementing type. A method with
// no body is a signature; one with a body is a default the impl may omit.
trait        := [ "pub" ] "trait" ident [ typeparams ] [ ":" bound ("+" bound)* ] "{" ( assoctype | traitmethod )* "}"
assoctype    := "type" ident [ ":" bound ("+" bound)* ]   // `type Item`, bound by each impl
traitmethod  := "fun" [ "mut" ] ( "Self" "." )? ident "(" [ param ("," param)* ] ")"
                [ ".return" ":" type ] ( body | )        // no body: a signature; no `Self.`: a static method
traitimpl    := "impl" traitname [ typeargs ] "for" typename "{" ( bindtype | method )* "}"
bindtype     := "type" ident "=" type
traitname    := ident [ "." ident ]                    // `Shape` or `shape.Shape`
typename     := ident [ "." ident ]
method       := "fun" [ "mut" ] "Self" "." ident "(" [ param ("," param)* ] ")"
                [ ".return" ":" type ] body
const        := [ "pub" ] "const" ident ":" type "=" expr
pd           := "pd" ("val" | "var") ident [ ":" type ] "=" expr
datac        := [ "pub" ] "datac" ident [ typeparams ] "(" [ field ("," field)* ] ")"
field        := ("val" | "var") ident ":" type
enum         := [ "pub" ] "enum" ident [ typeparams ] "{" ( ident [ "(" [ field ("," field)* ] ")" ] )* "}"
typeparams   := "<" typeparam ("," typeparam)* ">"
typeparam    := ident [ ":" bound ("+" bound)* ]
              | "const" ident ":" type                // a value parameter: `const N: usize`
bound        := traitname [ typeargs ]                // `Shape`, `From<i32>`
typeargs     := "<" type ("," type)* ">"   // in an expression: adjacent to the name and to "("
fun          := [ "pub" ] [ "extern" ] "fun" [ "mut" ] ( ident [ typeparams ] "." )? ident [ typeparams ]
                "(" [ param ("," param)* ] ")" [ ".return" ":" type ] body
                // `[typeparams]` after the function's own name bounds its type
                // parameters (9.5); on a receiver it names the receiver's type
                // arguments and takes no bounds.
param        := ident ":" [ "mut" | "move" ] ( type | "impl" traitname )   // `impl Trait`: a whole parameter type, bare or behind `&`
body         := "=" expr | block | <nothing for extern>

type         := [ "&" [ "mut" ] "dyn" ident ]  // a borrowed trait object: `&dyn T`, `&mut dyn T`
              | "Box" "<" "dyn" ident ">"       // an owned trait object
              | ident "::" ident                // an associated type: `I::Item`, `Self::Item`
              | [ "&" ] ( ident [ "<" type ("," type)* ">" ] [ "." ident ]
                       | "fun" "(" [ fparam ("," fparam)* ] ")" [ ".return" ":" type ]
                       | "[" type ";" expr "]"        // a fixed-size array: [T; N]
                       | "(" type "," type ("," type)* ")" )  // a tuple: (A, B)
fparam       := [ "mut" | "move" ] type
```

```
stmt         := "val" | "var" | "while" | "for" | "return" | "break" | "continue" | expr
val          := "val" ( ident [ ":" type ] | pattern ) "=" expr
var          := "var" ( ident [ ":" type ] | pattern ) "=" expr
pattern      := "(" position "," position ("," position)* ")"
position     := ident | "_" | pattern
while        := "while" expr block
for          := "for" ident "in" expr block   // the `in` is contextual, not a keyword
                                              // `break`/`continue` are statements, not keywords
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
              | "fun" "(" [ param ("," param)* ] ")" [ ".return" ":" type ]
                ( "=" expr | block )
              | "[" expr ("," expr)* "]"       // an array literal: length is the count
              | "[" expr ";" expr "]"          // a repeat: [0; 4096]
              | "(" expr "," expr ("," expr)* ")"   // a tuple value: (lo, hi)
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
- `impl` carries the optional grant: `caps(domain = [pattern, ...])`, or the
  single `caps(*)` that delegates the whole resource of every domain the
  importing module holds. The `*` stands alone; a named domain beside it is
  refused by name (15.2).
- `trait` and `traitimpl` are the trait forms (§9.5): a `trait` body is
  methods, and `impl Trait for Type` gives them to a `datac`/`enum` or to a
  builtin. A method with no body is a signature; one with a body is a default
  the impl may omit or override, and a trait may name supertraits after a `:`.
  `Self` is an ordinary `ident` in both, standing for the implementing type,
  and `typeparam` carries the bounds a generic declaration may put on a type
  parameter (`fun f<T: A + B>`).
- `type` carries the borrowed trait object `&dyn Name` / `&mut dyn Name`
  (§9.5.1) ahead of the ordinary `[ "&" ]` type. `dyn` is not a keyword: it is
  recognized only after a leading `&` (or `&mut`), and the form is legal only as
  a parameter type or a local binding type; a bare `dyn Name` is refused by
  name.
- The later trait forms: `type Item` in a trait and `type Item = T` in an impl
  ([Associated types](/language/associated-types)); a trait's own type
  parameters, `trait From<T>`, a static method written without `Self.`, and a
  bound or impl that names the arguments ([Generic traits](/language/generic-traits));
  `Box<dyn Name>` ([Owned trait objects](/language/box-dyn)); `const N: usize` as
  a type parameter and `impl Trait` as a whole parameter type
  ([Const generics](/language/const-generics)); and `break`/`continue`
  ([Iterators](/language/iterators)).
- A leading `pub` is accepted on a top-level `const`, `datac`, `enum`, `fun`,
  `extern fun` and `trait`, and nowhere else (13.4): a `pd` is module-scoped by
  design, an `impl` is not an item, and a method's reachability follows its
  declaring type.
  A top-level item with no `pub` is private to its own module, and a declaration
  that carries `pub` may name only types its own module exports, so an exported
  signature is reachable in every name it writes.
- `postfix` carries the three postfix forms: `?`, field access, and a call, which
  is why `f(x)?` and `a.b.c(1)` both parse.
- `primary` includes `block` and `if`/`when` as expressions, which is how
  `val label: String = if flag { "yes" } else { "no" }` works.
- `(T)` is the parenthesized type `T`, and `(e)` is the parenthesized expression
  `e`, so a tuple has two or more positions and there is no one-element tuple;
  `()` is neither a type nor a value, because the absent value's type is `unit`.
  A tuple value is read by a destructuring `val`/`var`, by a constant index
  (`t.0`), by `for (a, b) in ...` and by a tuple pattern in `when`
  ([Bindings and assignment](/language/bindings)).
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
- [Traits and static dispatch](/language/traits)
