---
title: "`dedup`: duplicate files and tree drift"
description: "Duplicate-file grouping and tree snapshot/drift over a caller-supplied List<Entry>: size prefilter, hash grouping, byte-for-byte confirmation. No capability, and no imports: reading is the caller's, passed in as closures."
isPublished: true
tags: "library, filesystem"
---
Two halves over one type. `duplicates` finds the files that share their content;
`snapshot` records a tree and `drift` reports what moved since.

**No capability, and no imports.** This library never reads a file: reading is
the caller's, and it arrives as a closure. So `dedup` needs no `fs` grant, has no
dependency to declare, and every function is testable on a list built by hand.

```toml
[dependencies]
dedup = "Juniper/fpl/dedup"
```

```kelp
impl "deps/dedup/lib"
```

## Types

```kelp
datac Entry(val path: String, val size: u64, val mtime: i64)
datac Digest(val path: String, val size: u64, val mtime: i64, val hash: u64)
datac Group(val hash: u64, val size: u64, val members: List<Digest>)

datac Options(
    val min_size: u64,
    val max_size: u64,
    val newer_than: i64,
    val keep_empty: bool,
    val hash_all: bool,
    val verify: bool
)

datac Report(
    val files: usize,
    val unique: usize,
    val hashed: usize,
    val bytes_hashed: u64,
    val groups: List<Group>
)
```

A `Digest` is a file plus its hash, which is also exactly what a snapshot record
is, so both halves share one type.

## Duplicates

```kelp
fun default_options().R: Options
fun keeps(e: &Entry, o: &Options).R: bool
fun filter(entries: &List<Entry>, o: &Options).R: List<Entry>
fun duplicates(
    entries: &List<Entry>,
    o: &Options,
    hash: closure(&Entry).R: u64,
    equal: closure(&str, &str).R: bool
).R: Report
fun wasted(g: &Group).R: u64
fun group_bytes(g: &Group).R: u64
fun total_wasted(groups: &List<Group>).R: u64
fun total_files(groups: &List<Group>).R: usize
fun copy_entry(e: &Entry).R: Entry
fun copy_digest(d: &Digest).R: Digest
fun copy_group(g: &Group).R: Group
fun group_digests(xs: &List<Digest>).R: List<Group>
fun confirm(g: &Group, equal: closure(&str, &str).R: bool).R: Group
fun candidates(files: &List<Entry>, o: &Options).R: List<Entry>
```

`duplicates` is the whole pipeline in one call: apply the size window in `o`,
keep only the files whose size another file shares, `hash` each survivor once,
group by `(size, hash)`, and, when `o.verify` is set, call `equal` against the
first member of each group so a hash collision narrows the group instead of
reporting a duplicate that is not one. The pieces are exported too, so a caller
can run the stages itself.

`Report.unique` is the payoff of the size prefilter: the files dropped without a
read. On a real tree it is most of them.

### Options

| Field | Meaning |
| --- | --- |
| `min_size` | smallest file to consider |
| `max_size` | largest; `0` means no upper bound |
| `newer_than` | unix seconds, at or after which a file qualifies; `0` means no lower bound |
| `keep_empty` | whether a zero-length file is considered at all |
| `hash_all` | hash every file, not only the ones whose size another file shares |
| `verify` | confirm each group with `equal` after hashing |

## Snapshots and drift

```kelp
datac Snapshot(val root: String, val generated: i64, val records: List<Digest>)
datac Drift(val unchanged: usize, val changed: List<String>, val missing: List<String>, val added: List<String>)

fun record(entries: &List<Entry>, hash: closure(&Entry).R: u64).R: List<Digest>
fun snapshot(root: &str, generated: i64, entries: &List<Entry>, hash: closure(&Entry).R: u64).R: Snapshot
fun drift(s: &Snapshot, entries: &List<Entry>, hash: closure(&Entry).R: u64).R: Drift
fun drifted(d: &Drift).R: bool
```

`drift` decides in three steps: size first, then the recorded modification time
as the cheap proxy for "touched", and only a file whose `mtime` moved is read
again through `hash`. So a file touched without being changed reads as changed,
and a file changed with its `mtime` put back reads as untouched. That is the
trade, and it is the one every incremental tool makes.

Serialization is the caller's: a `Snapshot` is a `root`, a timestamp and a
`List<Digest>`, so a caller that wants JSON writes it with
[`json`](/libraries/json) and one that wants a database writes that.

## Example

```kelp
impl "std/fs"
impl "std/fmt"
impl "std/str"
impl "deps/dedup/lib"
impl "deps/fsx/lib" caps(fs = ["/tmp/dedupdemo/**"])
impl "deps/hash/lib"

// The two closures are the whole interface to the filesystem.
fun file_hash(e: &dedup.Entry).R: u64 {
    val data = fs.read(e.path.as_str())
    return hash.fnv1a_64(data = &data)
}

fun file_equal(a: &str, b: &str).R: bool = fsx.files_equal(a = a, b = b)

fun entry_of(p: &fsx.PathInfo).R: dedup.Entry = dedup.Entry(
    path = p.path.clone(),
    size = p.size,
    mtime = p.mtime
)

fun main() {
    val found = fsx.survey(root = "/tmp/dedupdemo", max_depth = 32, keep = fsx.any_path)
    var entries: List<dedup.Entry> = List.empty()
    var i: usize = 0
    while i < found.files.len() {
        entries.push(entry_of(p = found.files.get(i)))
        i += 1
    }

    val o = dedup.default_options()
    val report = dedup.duplicates(entries = &entries, o = &o, hash = file_hash, equal = file_equal)
    print(fmt.uint(n = report.files.to_u64()))
    print(fmt.uint(n = report.unique.to_u64()))
    print(fmt.uint(n = report.groups.len().to_u64()))
    print(fmt.uint(n = dedup.total_wasted(groups = &report.groups)))

    val snap = dedup.snapshot(root = "/tmp/dedupdemo", generated = 1700000000, entries = &entries, hash = file_hash)
    val moved = dedup.drift(s = &snap, entries = &entries, hash = file_hash)
    print(dedup.drifted(d = &moved))
}
```

With `/tmp/dedupdemo` holding three copies of one 12-byte file and one unrelated
file:

```
4
1
1
24
false
```

## Notes

- **Reading is never done here.** `hash` takes an `&Entry`, not a path, so the
  caller decides how a file is read (and whether it is read at all): a test can
  hash the length, a tool can hash the bytes, and a cache can hash nothing.
- `hash` is called once per candidate, `equal` only for the groups `verify`
  covers. A caller passing an expensive checksum pays for it once per file.
- `group_digests` groups without sorting. `List.sort` on the owned element
  exists now (the order is `Digest`'s fields, so path first), but grouping wants
  equality of hashes rather than an order, and the two-pass version counts hashes
  in a `Map` and scans for the ones that repeat, which is linear in practice
  because few hashes repeat.
- `copy_group` is `Group.members.clone()`, the derived `List<Digest>` copy.
  `copy_entry` and `copy_digest` are written out field by field: the derived copy
  is reached through a `List`, so a bare `datac` value has no `.clone()` of its
  own.
- `duplicates` applies the size window itself; `record`/`snapshot` do not, so a
  caller that wants the same window over a snapshot calls `filter` first.

## See also

- [`fsx`](/libraries/fsx): the depth-capped walk whose `PathInfo` fills an `Entry`
- [`hash`](/libraries/hash): the checksums to hand `duplicates`
- [`json`](/libraries/json): writing a `Snapshot` as a document
