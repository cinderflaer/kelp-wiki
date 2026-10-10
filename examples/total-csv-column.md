---
title: "Total a CSV column"
description: "The total-csv-column program totals one column of a CSV file and prints it as an aligned table, with two dependencies."
isPublished: true
tags: "example"
---

The `total-csv-column` program totals one column of a CSV file.
It prints the total as an aligned table.
It is the first example with two dependencies, and the first that builds a `Map`.

| | |
| --- | --- |
| Source | [`src/total-csv-column.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki-wikijs/raw/branch/main/examples/src/total-csv-column.kp) |
| Needs | `csv = "Lilly/fpl/csv"`, `table = "Lilly/fpl/table"` |
| Shows | CSV rows and fields, a `Map` accumulator, `str.parse_i64`, rendering a table |

## The dependencies

```toml
# coral.toml
[dependencies]
csv   = "Lilly/fpl/csv"
table = "Lilly/fpl/table"
```

```kelp
impl "deps/csv/lib"
impl "deps/table/lib"
```

Each folder lands flat at `src/deps/<name>/`, so the import names the entry file
and nothing about which repository it came from.

## The program

```kelp project
impl "deps/csv/lib"
impl "deps/table/lib"
impl "std/str"
impl "std/fmt"

// Totals the `units` column per region, in a function of its own.
fun totals_by_region(rows: &List<csv.Row>).return: Map<String, i64> {
    var totals: Map<String, i64> = Map.new()
    var i: usize = 1          // row 0 is the header
    while i < rows.len() {
        val row = rows.get(i)
        val region = row.get(0)
        val parsed = str.parse_i64(row.get(1))
        if let Ok(units) = parsed {
            var running: i64 = 0
            if totals.has(region) {
                running = totals.get(region)
            }
            totals.insert(key = region, v = running + units)
        }
        i += 1
    }
    return totals
}

fun render(totals: &Map<String, i64>) {
    var headers: List<String> = List.empty()
    headers.push("region")
    headers.push("units")
    var t = table.new_table(headers)

    val names = totals.keys()
    var i: usize = 0
    while i < names.len() {
        val name = names.get(i)
        var cells: List<String> = List.empty()
        cells.push(name.clone())
        cells.push(fmt.int(totals.get(name.as_str())))
        table.add_row(t, cells)
        i += 1
    }
    print!(table.render(&t))
    print("")
}

fun main() {
    val text = "region,units\nnorth,12\nsouth,7\nnorth,5\n"
    val parsed = csv.parse(text)
    if let Ok(rows) = parsed {
        // An `&`-expression on a temporary is refused, but a parameter borrows
        // one for free, so the map needs no binding of its own.
        render(totals_by_region(rows))
    }
}
```

## Run it

```sh
kelpc build total-csv-column.kp -o total-csv-column && ./total-csv-column
```

## Output

```
region | units
-------+------
north  | 17   
south  | 7    
```

The trailing spaces are the table library padding each column to its widest cell.
`table.render` emits no final newline, which is why the program prints an empty
line after it: `print!("{render}")` then `print("")`.

## What to take from it

- **A `Map` key is a bare `str` in every method** when the map is `String`-keyed
  (`has`, `get`, `insert`, `remove`). That is why `totals.has(region)` takes the
  `&str` straight from `row.get(0)` while `totals.get(name.as_str())` needs
  `.as_str()` for a `String` that `Map.keys()` handed back.
- **Entries keep insertion order**, so the report is stable: `north` appears
  before `south` because the file mentions it first. There is no sorting step and
  no hash-order surprise.
- **`str.parse_i64` returns a `Result`,** so a malformed number is a value to
  handle rather than a panic. This program silently skips such rows; a stricter
  one would report them.
- **`Row.get(i)` hands back a `&str`,** so no allocation happens while reading a
  file's worth of fields.
- **A parameter may borrow a temporary while an explicit `&` may not**, which
  [Pitfalls](/language/pitfalls) documents.

## See also

- [`csv`](/libraries/csv) and [`table`](/libraries/table)
- [Collections](/language/collections) for `Map` and `List`
- [filter-json-by-score](/examples/filter-json-by-score), which builds a tree rather than a map
