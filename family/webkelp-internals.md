---
title: "How WebKelp is built"
description: "The WebKelp compiler is about 2,100 lines of Kelp in seven modules. This page maps them, follows one document through the pipeline, and explains the capability split, the design choices and the golden tests."
isPublished: true
tags: "family, compiler"
---
WebKelp's compiler is a Coral-style Kelp project of about 2,100 lines with no
dependencies beyond `std/*`. This page is for someone reading or changing it. For using it,
see the [overview](/family/webkelp) and the [syntax reference](/family/webkelp-syntax).

## Layout

```
webkelp/
    coral.toml        name, version, entry = "src/main.kp"
    src/main.kp       CLI and all file I/O
    src/page.kp       front matter and whole-page assembly
    src/block.kp      block parser
    src/inline.kp     inline parser
    src/attrs.kp      the {attribute} parser
    src/text.kp       byte-level string helpers
    src/theme.kp      the default stylesheet, embedded as Kelp source
    tests/            golden tests: cases/*.wk with expected .html and .css
    examples/site/    a small sample site
```

| Module | Lines | Owns |
| --- | --- | --- |
| `block` | ~920 | headings, paragraphs, lists, quotes, fences, tables, containers, raw HTML, and the `Ctx` shared by a page |
| `inline` | ~340 | code spans, emphasis, links, images, spans, raw inline tags |
| `text` | ~300 | escaping, slugs, scanning helpers, `brace_close`, URL rewriting |
| `page` | ~220 | front matter, `Meta`, the document shell, fragment mode |
| `attrs` | ~160 | `Attrs`, `parse`, `split_trailing`, `looks_like_attrs` |
| `main` | ~150 | argument handling, reading and writing files, directory walking |
| `theme` | ~65 | `base_css()` |

## The capability split

`main.kp` is the only module that writes `impl "std/fs"`. Every other module imports only
`std/str`, which is ungated, and takes and returns text:

```kelp
// page.kp
pub fun compile(src: &str, css_href: &str, inline_css: bool).R: Page
```

`compile` takes the document as a `str` and returns a `Page(html, css)`. It cannot read a
file, because nothing it imports could. This is the [capability model](/language/capabilities)
used as a design tool: the part of the program that is hard to get right has no authority,
so it can be tested with plain strings and cannot surprise anyone.

## One document through the pipeline

```
main.build_one        read the .wk file
  page.compile
    block.to_lines      split on \n, drop \r, expand leading tabs
    front_matter_end    is there a --- ... --- block? read_meta -> Meta
    block.blocks        the block parser, recursive
      inline.render     for each paragraph, heading, cell and list item
    assemble            <!doctype>, <head>, the theme + collected CSS, <body>
main.build_one        write name.html and name.css
```

### The block parser

`block.blocks(lines, tight, ctx)` walks a `List<String>` with an index. At each non-blank
line it tries the constructs in a fixed order, and each construct is a function that appends
its HTML to the output and returns the index of the next unread line:

1. a `{…}` line on its own: remembered as *pending* attributes for the next block
2. `:::` container opener
3. code fence
4. heading
5. horizontal rule (before lists, so `***` is a rule and not an empty bullet)
6. `>` quote
7. list marker
8. table (a `|` line followed by a separator row)
9. raw HTML block
10. paragraph, which reads lines until `starts_block` says a new block begins

Nested content is handled by **building a new line list and calling `blocks` again**:
a quote strips its `>` markers, a list item removes its indentation, a container takes the
lines between its fences. Recursion is what makes nesting free.

`tight` is the one flag that recursion carries. A tight list item renders its first
paragraph without `<p>`; the list decides looseness by scanning for blank lines between
items or inside them.

`Ctx` is threaded through as a `mut` parameter and holds the state that belongs to the whole
page: the collected CSS, the hoisted `@import` lines, the first `#` heading, and the ids
already used (for the `-2`, `-3` suffixes).

### The inline parser

`inline.render_into(out, s, from, to)` scans **a byte range of one string**. Constructs that
contain other constructs (a link's text, emphasis) call `render_into` again on a narrower
range, so no substring is copied and there is no intermediate token list. Each construct
function returns the index after itself, or the index it was given to say *not here*, and
the caller then emits the byte literally. That "return your own start to decline" convention
is what makes an unmatched `*` or `[` harmless.

Because the emphasis search looks at bytes outside the current range only to test the byte
before an opener (word boundary for `_`), sharing one string across the recursion is safe.

### Brace matching

Attributes need to find the `}` that closes a `{`, and the obvious search breaks on
`x-data="{ open: false }"`. `text.brace_close` scans with two extra rules: braces nest, and a
quote that follows `=` opens a value inside which braces are ignored. Three places use it:
inline `{…}` after a link, the trailing `{…}` on a block line, and `:::` headers. The `=`
condition is deliberate: an apostrophe in prose (`{.it's}`) does not open a quote.

### CSS

`::: style` bodies go to `Ctx.add_css`, which splits them into lines and moves any
`@import` or `@charset` statement (through the line that ends it with `;`) into a separate
buffer. `page.compile` then concatenates hoisted imports, the theme, and the rest. That is
the whole reason the ordering rule exists: the theme is written first, and CSS ignores an
`@import` that follows any rule.

## Choices worth knowing

- **Bytes, not characters.** Every scanner works on `u8` with `str.byte`. Multi-byte UTF-8
  passes through untouched because none of its bytes is ASCII, and the slug function keeps
  bytes at or above 128.
- **No regular expressions and no `break`.** Kelp v1 has neither, so loops end through a
  condition (`while i < n && !found`). It costs a flag per loop and keeps every scanner's
  termination visible.
- **Small `datac`s instead of tuples.** `Split(body, attrs)`, `Fence(ch, len, rest)`,
  `Marker(indent, ordered, width, num)` and `Braces(attrs, end)` are returned where another
  language would return a tuple. They read better at the call site and avoid destructuring.
- **A declined construct is never an error.** The parser has no failure path: any input
  produces a document, and anything it does not recognise is text. This is what lets prose
  contain stray `*`, `<`, `{` and `[` safely.
- **Raw HTML is decided by one function**, `html_kind`, which returns *not HTML*, *to the next
  blank line* or *to the closing tag*. Everything about what counts as a raw block is in it and
  in `is_inline_tag`.

## Tests

`tests/run.sh` compiles each `tests/cases/*.wk` and diffs the output against the committed
`.html` and `.css`:

```sh
WEBKELP=./webkelp tests/run.sh             # run
WEBKELP=./webkelp tests/run.sh --update    # rewrite the expected files
```

| Case | Covers |
| --- | --- |
| `markdown.wk` | headings, emphasis, escapes, entities, nested and loose lists, quotes, fences, images |
| `escape-hatches.wk` | attributes, spans, containers, custom elements, raw blocks, `::: style` and `::: script`, front matter keys |
| `gaps.wk` | braces inside quoted values, hoisted `@import`, `html:` attributes, raw block tags |
| `fragment.wk` | `shell: none` |

Expected files are **golden**: they were generated by the compiler and then read by a person,
so a diff means "the output changed", and the reviewer decides whether that is a fix or a
regression. A new behaviour gets a new case rather than an edit to an old one.

## Adding a construct

1. Decide where it fits in the order above (blocks) or in `render_into`'s chain (inline).
2. Write a function that returns the next index, and returns the current one to decline.
3. Add a case under `tests/cases/`, run `--update`, and read the diff.
4. Add the row to the [syntax reference](/family/webkelp-syntax).

## See also

- [Writing tools in Kelp](/family/writing-tools-in-kelp)
- [Capabilities](/language/capabilities)
- [Text](/language/text) and [`std/str`](/stdlib/str)
