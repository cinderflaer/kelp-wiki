---
title: "`csv`: RFC-4180-ish CSV parse and write"
description: "Comma-separated fields, double-quote quoting, \"\" as an escaped quote inside a quoted field, embedded commas, quotes and newlines inside a quoted field. A bare \\r outside quotes is treated as part..."
isPublished: true
tags: "library, text, data-formats"
---
Comma-separated fields, double-quote quoting, `""` as an escaped quote inside a
quoted field, embedded commas, quotes and newlines inside a quoted field. A bare
`\r` outside quotes is treated as part of a CRLF line ending and dropped.
`write` always emits CRLF.

No capability.

```toml
[dependencies]
csv = "Juniper/fpl/csv"
```

```kelp
impl "deps/csv/lib"
```

## Types

```kelp
datac Row(val fields: List<String>)

enum ParseErr {
    UnterminatedQuote
}
```

`Row` wraps `List<String>` in a one-field `datac` because `List<List<String>>`
cannot be written: a nested container has no C representation to hold inline
([syntax.md](https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md) §12.1). The same pattern `listx`'s `Chunk<T>` uses.

## `Row` methods

| Method | Returns |
| --- | --- |
| `row.len()` | field count |
| `row.get(i)` | `&str` |
| `row.is_empty()` | `bool` |
| `row.fields` | the `List<String>` itself, read-only through the borrow |

## Parse

```kelp
fun parse(text: &str).R: result.Result<List<Row>, ParseErr>
```

Rules:

- A quoted field ends at the first unescaped `"`; `""` inside it becomes one `"`.
- A comma, `\n` or `\r` inside quotes is field content, not a separator.
- `\r` outside quotes is skipped (CRLF).
- A file whose last line has no newline still yields that row, provided the row
  has content (`field` non-empty or a field already committed).
- An empty `text` yields zero rows. A text of just `"\n"` yields one row holding
  one empty field.
- `Err(UnterminatedQuote)` when the text ends inside a quoted field.

## Write

```kelp
fun write(rows: &List<Row>).R: String
fun write_field(s: &str, out: mut String)
fun field_needs_quote(s: &str).R: bool
```

- Every row is terminated with CRLF, including the last.
- A field is quoted only when it contains `,`, `"`, `\n` or `\r`; a `"` inside
  becomes `""`.
- `write_field` appends one field to an existing `String`; `field_needs_quote` is
  the predicate `write` uses.

## Example

```kelp
impl "deps/csv/lib"

fun main() {
    val parsed = csv.parse("name,note\nalice,\"hello, world\"\nbob,\"said \"\"hi\"\"\"\n")
    if let Ok(rows) = parsed {
        print(rows.len())
        for row in rows {
            print(row.len())
        }
        print(rows.get(1).get(1))
    }

    var rows2: List<csv.Row> = List.empty()
    var r1: List<String> = List.empty()
    r1.push("a,b")
    r1.push("plain")
    rows2.push(csv.Row(fields = r1))
    var r2: List<String> = List.empty()
    r2.push("multi")
    r2.push("line\nbreak")
    rows2.push(csv.Row(fields = r2))
    print!(csv.write(rows2))
}
```

Output (`print!` leaves the CRLFs to the terminal, so the blank line is the
final `\r\n`):

```
3
2
2
2
hello, world
"a,b",plain
multi,"line
break"

```

## Limits

- No header handling, no column names, no delimiter option, no type parsing.
- No quoting of a leading/trailing space inside an unquoted field; the writer
  leaves whitespace alone.
- A `"` that appears in an unquoted field is kept as a literal quote on parse,
  and the field is re-quoted on write.
- `Row.get` returns a `str`; use `row.fields.get(i)` for the owned `String`
  (a borrow).
