# json_filter

Parses a JSON array, keeps the records whose `score` reaches a threshold, and
prints the result canonically. This is the first example with a **dependency**.

| | |
| --- | --- |
| Source | [`src/json_filter.kp`](src/json_filter.kp) |
| Needs | `json = "Juniper/fpl/json"` |
| Shows | an owned tree, index walking, typed readers, rebuilding a document |

## The dependency

A library is a folder in a git repo, so a project declares the folder and gets its
*contents* at `src/deps/json/`:

```toml
# coral.toml
[dependencies]
json = "Juniper/fpl/json"
```

```sh
coral sync       # fetch (the only command that moves a dependency forward)
```

That is why the import names the file and nothing else about where it came from:

```kelp
impl "deps/json/lib" as json
```

## The program

```kelp
impl "deps/json/lib" as json

// A helper, not because the work is long, but because an owned local declared
// inside an `if let` arm does not build yet, see the wiki's Known issues.
fun keep_high_scores(doc: &json.Json).R: String {
    var kept: List<json.Json> = List.empty()
    var i: usize = 0
    while i < json.array_len(doc) {
        val item = json.array_get(doc, i)
        val score = json.as_i64(json.get(item, "score"))
        if score >= 7 {
            kept.push(json.clone(item))
        }
        i += 1
    }
    val out = json.array(kept)
    return json.write_sorted(&out)
}

fun main() {
    val text = "[{\"name\":\"ada\",\"score\":9},{\"name\":\"bob\",\"score\":3},{\"name\":\"cyd\",\"score\":7}]"
    val parsed = json.parse(text)
    if let Ok(doc) = parsed {
        print(keep_high_scores(doc))
    }
}
```

## Run it

```sh
kelpc build json_filter.kp -o json_filter && ./json_filter
```

## Output

```
[{"name":"ada","score":9},{"name":"cyd","score":7}]
```

## What to take from it

- **A `Json` tree is owned and read-only in practice.** v1 matches an enum payload
  through a borrow, so a document is built **bottom-up**: collect the children in a
  `List`, then wrap them with `json.array` or `json.object`. That is the whole
  reason `kept` exists.
- **Readers panic on the wrong type**; `json.as_i64` on a string is a panic, not an
  `Option`. A program that must tolerate a shape uses `json.try_i64`,
  `json.as_i64_or`, or checks `json.is_int` first.
- **`json.write_sorted` is canonical**: keys sorted, so one document has one text,
  which is what makes it useful as a key or a diff.
- **The helper function is a workaround, not a style choice.** An owned local
  (here `var kept: List<Json>`) declared inside an `if let` arm fails to codegen on
  the current compiler: [Known issues](../meta/known-issues.md) BUG-1 has the
  repro. The comment stays in the source so the next reader does not "simplify" it
  back into the bug.
- **`json.clone` is a deep copy**; `array_get` lends a borrow, so the tree must be
  copied to outlive the walk.

## See also

- [`json`](../libraries/json.md): the whole library, including JSON Pointer
- [Libraries (fpl)](../libraries/index.md) for the dependency model
- [Known issues](../meta/known-issues.md)
