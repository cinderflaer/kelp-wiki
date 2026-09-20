---
title: "Small projects to build"
description: "A ladder of ideas, from one-file programs that need nothing but the standard library to a project with a library, a test task and a dependency. Each one is small enough to finish in an evening."
isPublished: true
tags: "getting-started"
---
You learn a language by writing programs in it that you actually want. Everything
below is small: one file at the bottom of the ladder, a handful of files at the
top, and no idea that needs more than the standard library plus one library from
the [catalogue](/libraries).

Three constraints are worth knowing before you pick one, because they shape what a
small program looks like in Kelp:

- **A path is resolved, not refused.** A gated call takes an absolute path,
  because `fs` patterns are absolute and the check normalizes before it matches.
  `fs.cwd()` and `path.absolute(fs.cwd(), arg)` turn `notes.txt` into one, so a
  tool can take a relative argument. See
  [A first real tool](/getting-started/first-tool).
- **Anything outside the program is a capability**, granted on the `impl` line. A
  program that prints needs no grant; a program that reads a file needs `fs`.
- **A test or task entry lives under `src/`.** That matters only at the top of the
  ladder; see [Testing what you write](/getting-started/testing).

## Rung 1: one file, standard library only

| Idea | What it uses | What it teaches |
| --- | --- | --- |
| `tail`, the other half of [your first tool](/getting-started/first-tool) | `fs.read_lines`, a descending `while` | indexing from the end, and control flow with no `break` |
| A line-numbered printout, like `cat -n` | `fmt.pad_left`, a counter | keeping a running index while you walk a list |
| A palindrome and anagram checker | `str.char_at`, `List<i32>.sort` | byte against character indices, sorting in place |
| Collatz lengths for 1 to 100 | `while`, `i64` | integer division and modulo, and finding the longest by hand |
| Roman numerals, both directions | `String.push_str`, `str.parse_i64` | building text when a template is not allowed |
| A right-aligned multiplication table | `fmt.pad_left`, `fmt.int` | formatting into a `String` rather than printing pieces |
| A dice roller with a histogram | `rand.below`, `str.repeat` | a capability grant, and a `Map` as a counter |
| A passphrase from a word list on disk | `fs.read_lines`, `rand.below` | two grants in one program, and resolving a relative path with `fs.cwd` |
| Countdown to a date | `time.now_unix` | the `time` grant, and integer date arithmetic |

## Rung 2: one library from the catalogue

A dependency is a manifest line, so these want a project: `coral init`, add the
library under `[dependencies]`, and run `coral sync`.

| Idea | Library | What it teaches |
| --- | --- | --- |
| A JSON pretty-printer | [`json`](/libraries/json) | parse into owned values, walk them, rebuild the text |
| A CSV column tally | [`csv`](/libraries/csv), [`table`](/libraries/table) | rows as records, a `Map` accumulator, a rendered report |
| A config file with defaults | [`config`](/libraries/config) | typed accessors (`get_str_or`, `get_int_or`) and why a float is text |
| Duplicate files by checksum | [`hash`](/libraries/hash) | `fs.walk`, FNV-1a per file, a `Map` from digest to path |
| Days until a date | [`datetime`](/libraries/datetime) | `parse_iso8601`, `diff_seconds`, calendar arithmetic |
| A reproducible lottery draw | [`prng`](/libraries/prng) | a seed, `below`, `shuffle_i32`, and a run you can repeat |
| Word frequency from a text file | [`table`](/libraries/table) | `str.split`, a `Map`, sorting, a report |
| A report in colour, that respects `NO_COLOR` | [`term`](/libraries/term), [`log`](/libraries/log) | the `env` grant, and stdout against stderr |
| `wc` with flags and `--help` | [`argparse`](/libraries/argparse) | the finished shape of the tool from rung 1 |

## Rung 3: project-shaped

Here the point is not the feature count, it is the shape: more than one module, a
test task, a pin, a dependency.

| Idea | Shape | What it teaches |
| --- | --- | --- |
| A library you keep, with its test task | `src/<name>/lib.kp` plus `src/tasks/test.kp` | exports, a namespace alias, `testkit` |
| Two files that talk to each other | `src/main.kp` plus `src/shapes/*.kp` | local `impl` paths relative to `src/` |
| Two implementations, timed | a task per version, [`benchkit`](/libraries/benchkit) | `benchkit` needs the `time` grant delegated to it |
| A client and a server | [`lineproto`](/libraries/lineproto), `std/net` | two processes, a socket grant on each side, a text protocol |

## Three to start with today

**`tail`.** Open the `head` program from [A first real tool](/getting-started/first-tool)
and change the loop: start `i` at `lines.len()` and count down while `i > 0 &&
lines.len() - i < count`, printing `lines.get(i - 1)`. Fifteen minutes, same
grants, and you will hit the "no `break`" rule in the first version you write.

**A temperature table.** Print Celsius and Fahrenheit for 0 to 100 in steps of 10,
in two columns:

```kelp
impl "std/fmt"
impl "std/str"

fun main() {
    var c: i64 = 0
    while c <= 100 {
        val f = c.to_f64() * 9.0 / 5.0 + 32.0
        val c_text = fmt.int(c)
        val f_text = fmt.float(f, 1)
        val left = fmt.pad_left(c_text.as_str(), 4, ' ')
        val right = fmt.pad_left(f_text.as_str(), 6, ' ')
        print(str.concat(left.as_str(), right.as_str()))
        c += 10
    }
}
```

```
   0  32.0
  10  50.0
  20  68.0
  30  86.0
  40 104.0
  50 122.0
  60 140.0
  70 158.0
  80 176.0
  90 194.0
 100 212.0
```

Why the two `val`s in the middle instead of `fmt.int(c).as_str()`: `.as_str()` on a
temporary is refused, because the temporary would be freed before the view could
be used. Bind it to a local first. That one rule explains a large share of the
text errors you will meet, and [Pitfalls](/language/pitfalls) lists the rest.

**A CSV column tally.** `coral init tally`, add `csv = "Juniper/fpl/csv"` under
`[dependencies]`, `coral sync`, then have the program print `row.len()` for each
row of a file before it counts anything. Half of a small data tool is getting the
parse and the loop right; the tally is the easy part.

## Keeping them small

- **One entry file and one capability** until it runs. Add the second module when
  the first file passes a hundred lines.
- **Print instead of writing files** when a path rule is in the way. The program
  is still a program.
- **Start it as a project anyway**, even for one file: `coral init` costs a
  second, and a `[tasks]` entry, a dependency and a `[toolchain]` pin are one line
  each when you want them.
- **Stop at the first version that runs**, then add one thing. Every idea above is
  a complete program in its first form.

## See also

- [A first real tool](/getting-started/first-tool): the rung 1 shape, in full
- [Testing what you write](/getting-started/testing): what to add when it grows
- [Examples](/examples): eighteen built and run programs at every size
- [Libraries (fpl)](/libraries): the catalogue, with a page per library
- [Standard library](/stdlib): `str`, `fs`, `fmt`, `math`, `time`, `rand` and the rest
