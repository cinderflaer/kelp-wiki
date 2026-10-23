---
title: "Front end"
description: "The lexer, the _alias text pass and the parser. Covers the token kinds, the newline rule, the operator precedence and the few constructs the parser rewrites."
isPublished: true
tags: "compiler"
---
The front end turns one module's text into an AST.
It runs three steps in order: the lexer, the text alias pass and the parser.
The resolver calls all three for each module (`resolve.rs`).

## Lexing (`lexer.rs`)

`Lexer::tokenize` (`lexer.rs`) returns a token vector with a byte span on every token.
`Lexer::tokenize_with_trivia` (`lexer.rs`) also keeps comments, and `kelpc fmt` uses it.

- **Newlines end statements.** A newline is a token only at parenthesis depth 0, or inside a `{` block opened inside parentheses (`lexer.rs`).
  A newline after a line-continuing token such as `+`, `,` or `.` is dropped (`lexer.rs`).
  That is why Kelp has no semicolons.
- **Comments** are skipped unless trivia is requested (`lexer.rs`).
- **Strings** are decoded in `lex_string` (`lexer/literals.rs`).
  A string with `$name` or `${expr}` becomes a flat run of template tokens: `TemplateStart`, `StrChunk`, `TemplateExprStart`, `TemplateExprEnd` and `TemplateEnd`.
- **Labels** are `'name` with no closing quote (`lexer.rs`).
- **Keywords** are matched by text (`lexer.rs`).
  `in`, `alias`, `loop`, `percpu` and `type` are not keywords. The parser or the alias pass matches them as identifiers.
- **Other bytes** are an error: `unexpected character 'X'`.
  The lexer has no `#` arm, so `#` takes this path.

The lexer stops at its first error.

## Text aliases (`preprocess.rs`)

The alias pass replaces `_name` references with text before parsing.
It is a flat, global text substitution with no parameters, no scoping and no conditional compilation.

Two sources feed one table:

- `[alias]` entries in `coral.toml`, loaded by `load_manifest_aliases` (`resolve/loader_visit.rs`).
- Inline lines of the form `alias _name = <text to end of line>`, found by `alias_decl_shape` (`preprocess.rs`).
  The line must start after a newline, `{`, `}` or at the start of the file.
  An alias name starts with `_` and has at least one more character after it.

A reference is one identifier token, `_name`, that a declared alias names (`preprocess.rs`).
Inside a string literal, `_name` at the start of a word is replaced too, so `my_name` is left alone.
A `_name` that no alias declares is an ordinary identifier and is never rewritten.
The replacement is lexed again, and every token it produces takes the span of the use site (`preprocess.rs`).

Errors:

- a duplicate definition (`AliasTable::define`, `preprocess.rs`);
- a cycle, found during expansion and by `check_cycles` (`preprocess.rs`);
- replacement text that does not lex (`preprocess.rs`).

Up to `MAX_ALIAS_ROUNDS` (8, `resolve.rs`) discovery rounds run.
A failure in a discovery round is skipped, so a file loaded later can supply an alias that an earlier file used.

## Parsing (`parser.rs`)

`Parser::parse_program` (`parser/parser_part1.rs`) reads top-level items and dispatches on the leading keyword.
Statements are parsed by `parse_stmt` (`parser/parser_part4.rs`).
Expressions use precedence climbing in `parse_binary` (`parser/parser_part5.rs`).
Types are parsed by `parse_type_inner` (`parser/parser_part3.rs`), and string templates by `parse_template` (`parser/parser_part3.rs`).

The parser returns its first error and does not recover.
Expressions nest up to 200 levels (`MAX_NESTING`, `parser.rs`).

### Operator precedence

From loosest to tightest:

| Level | Operators |
| --- | --- |
| 1 | `\|\|` |
| 2 | `&&` |
| 3 | `==` `!=` |
| 4 | `<` `<=` `>` `>=` |
| 5 | `\|` |
| 6 | `^` |
| 7 | `&` (infix) |
| 8 | `<<` `>>` |
| 9 | `+` `-` |
| 10 | `*` `/` `%` |

The bitwise operators bind tighter than comparisons, which is unlike C.
All binary operators are left associative (`parser.rs`).

### Constructs the parser rewrites

- **`if let`** is rewritten into a `when` expression (`parser.rs`).
  When the scrutinee is a temporary, its root is first bound to a synthesized name with the prefix `#iflet` (`IF_LET_PREFIX`, `parser.rs`).
  A field chain over a temporary therefore drops the temporary once, at the end of the block.
- **`impl Trait` parameters** become a fresh bounded type parameter (`desugar_impl_trait_params`, `parser.rs`).
- **`for`** is not rewritten here. The parser produces `Stmt::For` (`parser.rs`).
  The type checker picks the loop form, as described in [Types](/compiler/types).

A `lexer.rs` comment says the parser desugars `for` into `while`.
The code does not do that, so the comment is out of date.

## Parse errors

A lexer or parser error is a message and a span.
Many parser messages have the form `expected <what>, found <token>`.
The resolver attaches the module id to the error, and the driver prints it as described in [Driver](/compiler/driver#diagnostics).

## Tests

- `lexer.rs` has unit tests for tokens, comments, newlines, strings and templates.
- `preprocess.rs` has unit tests for expansion, cycles, duplicates and unknown names.
- `parser.rs` has unit tests for declarations, types, statements, patterns and errors.
- `tests/frontend_fuzz.rs` mutates fixtures and runs `kelpc check` on them. The test asserts that nothing panics, aborts or hangs.
- `tests/fmt.rs` and `tests/lint.rs` cover the lexer's behaviour through the formatter and the linter.

## See also

- [Pipeline](/compiler/architecture)
- [Modules and capabilities](/compiler/resolve)
- [Types](/compiler/types)
- [Language: lexical structure](/language/lexical)
