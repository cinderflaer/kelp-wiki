# `std/mem`

Raw allocation. Ungated.

```kelp
impl "std/mem"
```

| Function | Returns | Notes |
| --- | --- | --- |
| `mem.alloc(n: usize)` | `Bytes` | a zero-filled buffer of `n` bytes |

That is the whole module. `Bytes` is the owned buffer type, so an allocation is
used like any other `Bytes`: `get`/`set`, `len`, `append`, `clone`, `as_str`,
and the ability to be handed to `fs.write`, `net.send_all` or a hash function.

```kelp
impl "std/mem"

fun main() {
    val buf = mem.alloc(4)      // zero-filled
    print(buf.len())            // 4
    print(buf.get(0))           // 0
}
```

!!! note "Why this is small"
    Growth goes through `Bytes.push`/`reserve`, and `String`/`List`/`Map` manage
    their own storage, so there is nothing else for a `mem` module to expose in
    v1 — no `free` (drops are automatic), no `realloc`, no address arithmetic.

## See also

- [Text](../language/text.md) for the `Bytes` API
- [`std/io`](io.md), [`std/fs`](fs.md), [`std/net`](net.md) for the consumers of a
  buffer
