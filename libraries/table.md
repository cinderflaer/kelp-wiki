---
title: "`table`: column layout with auto-sized widths"
description: "Builds an aligned text table over a header row and List<Row> - widths are taken from the widest cell, columns are left-aligned and joined with \" | \"."
isPublished: true
tags: "library, collections"
---
Builds an aligned text table over a header row and `List<Row>`: widths are taken
from the widest cell, columns are left-aligned and joined with `" | "`.

No capability.

```toml
[dependencies]
table = "Lilly/fpl/table"
```

```kelp
impl "deps/table/lib"
```

## Types

```kelp
datac Row(val cells: List<String>)
datac Table(val headers: List<String>, var rows: List<Row>)
```

Rows are `List<Row>` rather than `List<List<String>>`: each row is a named
one-field `datac`, which is what lets `add_row`, `column_widths` and `render`
speak about a row. `List<List<String>>` is legal; the wrapper is the shape this
library ships. The same fix `listx`'s `Chunk<T>` uses.

## Functions

| Function | Returns | Notes |
| --- | --- | --- |
| `new_table(headers: move List<String>)` | `Table` | moves the header list in; bind with `var` to add rows |
| `add_row(t: mut Table, cells: move List<String>)` | `Unit` | **panics** `table.add_row: cell count does not match the header count` |
| `column_widths(t: &Table)` | `List<usize>` | the widest cell per column, header included |
| `render(t: &Table)` | `String` | the finished table |

`add_row` refuses a ragged row rather than padding or truncating: a table with a
mismatched row is very likely a caller bug, and rendering it anyway would hide
that instead of surfacing it.

## `render` output

1. The header row, each column padded to its width.
2. A separator line: `-` repeated to each width, joined by `-+-`.
3. One line per row, same padding.

Columns are joined with `" | "`. The header and separator are separated by a
single `\n`; every subsequent row is preceded by `\n`. **There is no trailing
newline**, so `print!(table.render(&t))` is the usual way to emit it.

Single-byte width: `str.len`, so a multi-byte character counts as its byte
length and the column will be visually short.

## Example

```kelp
impl "deps/table/lib"

fun main() {
    var headers: List<String> = List.empty()
    headers.push("name")
    headers.push("n")
    var t = table.new_table(headers)
    var r1c: List<String> = List.empty()
    r1c.push("alpha")
    r1c.push("1")
    table.add_row(t, r1c)
    var r2c: List<String> = List.empty()
    r2c.push("b")
    r2c.push("200")
    table.add_row(t, r2c)
    print!(table.render(&t))
    val w = table.column_widths(&t)
    print(w.get(0))
    print(w.get(1))
}
```

Output (the `5` and `3` run on from the table's last line because `render` emits
no trailing newline):

```
name  | n  
------+----
alpha | 1  
b     | 2005
3
```

## Notes

- No right alignment, no per-column alignment, no wrapping, no borders beyond the
  header separator, no colour.
- Widths are recomputed on every `render` call; `Table.rows` is a `var` field, so
  rows can be added after the first render.
- A cell is only ever a `String`; format numbers with `fmt.int`/`fmt.float`
  before pushing them.
