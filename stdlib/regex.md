---
title: "`std/regex`"
description: "A linear-time regular expression engine in pure Kelp: a Pike VM over bytes, a documented pattern subset, and backreferences, lookaround and named groups refused at compile. Hosted only."
isPublished: true
tags: "stdlib, text"
---
A linear-time regular expression engine in pure Kelp. It needs no capability of
its own, and it is **hosted only**: a freestanding project that imports it is
refused by name.

```kelp
impl "std/regex"
```

The pattern is data, not syntax: the language itself still has no regular
expression literal, so a pattern is a `&str` handed to `regex.compile`. The
engine was specified in `plan/regex.md`.

## Engine

The pattern is parsed to an AST, compiled to a Thompson NFA program, and run by
a **Pike VM**: a list of threads in priority order, the capture slots carried
per thread, over **bytes**. Matching costs O(program size × input length). No
pattern can backtrack, so `(a+)+$`, `(a|aa)+$` and `(x+x+)+y` are as cheap as
any other pattern. There is no recursion proportional to the input: the VM is
iterative with an explicit stack, and the parser and emitter recurse only on
group nesting, which is limited to 100.

Semantics are leftmost-first (Perl-like): a match starts at the leftmost
position where any match exists, and among matches there the first one in
priority order wins (alternation prefers the left branch, greedy repeats prefer
more, lazy repeats prefer fewer).

## Syntax

Exactly this subset:

- **Literals**: any byte except the metacharacters `\ . [ ] ( ) * + ? { | ^ $`
  (a `]` or `}` on its own is literal). `\` followed by any ASCII punctuation
  byte is that byte (`\.`, `\{`, `\-`, ...).
- **`.`**: any byte except `\n`; with `(?s)` any byte.
- **Classes**: `[abc]`, `[a-z0-9_]`, `[^...]`. A `]` right after `[` or `[^` is
  literal; `-` first or last is literal. Inside a class: the escapes `\d \D \w
  \W \s \S`, `\n \r \t`, `\xHH` and escaped punctuation. No POSIX `[:alpha:]`,
  no nested classes, no `\b` (it is an error there).
- **Escapes**: `\d` is `[0-9]`; `\w` is `[A-Za-z0-9_]`; `\s` is space and
  `\t \n \v \f \r`; `\D \W \S` are their complements; `\b` is a word boundary
  and `\B` its negation (word = `\w`, ASCII); `\n \r \t`; `\xHH`; `\\`.
- **Anchors**: `^` start of input, `$` end of input (no trailing-newline
  allowance). With `(?m)`: `^` also after any `\n`, `$` also before any `\n`.
- **Groups**: `( )` capturing, numbered by opening parenthesis from 1; `(?: )`
  not.
- **Alternation** `|`.
- **Repetition**: `* + ? {n} {n,} {n,m}` and the lazy forms `*? +? ?? {n}?
  {n,}? {n,m}?`. Counted repeats are expanded into the program (`x{2,4}` is
  `xx(x(x)?)?`).
- **Flags**: `(?i)` ASCII case-insensitive, `(?s)` dot matches newline, `(?m)`
  multi-line; combinable (`(?is)`); `(?i:...)` scopes them to one group. A bare
  `(?i)` holds until the end of the enclosing group (it carries across `|`).
  There is no `(?-i)`.

Everything is bytes. `.` matches one byte; a non-ASCII literal matches its byte
sequence and a repeat after it applies to the whole character; inside a class
its bytes are separate members. Case folding is ASCII only. A `&str` has no NUL,
so `\x00` never matches there. An empty alternative is an empty match (`a|`,
`()`), and the empty pattern matches the empty string at the start.

## Refused at compile

Every bad pattern is an `Err(RegexErr)` carrying a message and the byte offset
where the parser noticed. Nothing panics and nothing matches.

| Construct | Message |
| --- | --- |
| backreference `\1`..`\9` | `backreferences are not supported` |
| lookaround `(?=` `(?!` `(?<=` `(?<!` | `lookaround is not supported` |
| named group `(?<n>` `(?P<n>` | `named groups are not supported` |
| pattern over 4096 bytes | `pattern is too long (limit 4096 bytes)` |
| groups nested over 100 deep | `nesting is too deep (limit 100)` |
| counted repeat over 1000 | `repeat count is too large (limit 1000)` |
| `{n,m}` with n > m | `invalid repeat: the lower bound is greater than the upper bound` |
| `{` that is not `{n}` `{n,}` `{n,m}` | `invalid repeat: expected {n}, {n,} or {n,m}` |
| `*` `+` `?` `{` with nothing before | `nothing to repeat` |
| `a**`, `a+?+` | `nested repetition operator` |
| `(` without `)` | `unclosed group` |
| stray `)` | `unmatched ')'` |
| `[` without `]` | `unclosed character class` |
| `[z-a]`, `[a-\d]` | `invalid character class range` |
| `\q` and other unknown letters | `invalid escape '\q'` |
| `\x` without two hex digits | `invalid \x escape: two hexadecimal digits are required` |
| pattern ending in `\` | `trailing backslash` |
| unknown flag `(?x)` | `unknown group flag 'x'` |
| program over 50000 instructions, or instructions × capture slots over 2000000 | `pattern is too large (...)` |

## API

```kelp
datac RegexErr(val message: String, val offset: usize)
datac Match(val start: usize, val end: usize, val text: String)
datac Captures(val text: String, val slots: List<i32>)
```

```kelp
regex.compile(pattern: &str).R: result.Result<Regex, RegexErr>
regex.is_match(pattern: &str, text: &str).R: bool          // panics on a bad pattern
Regex.is_match(&str).R: bool
Regex.find(&str).R: option.Option<Match>
Regex.find_at(&str, start: usize).R: option.Option<Match>
Regex.captures(&str).R: option.Option<Captures>
Regex.find_all(&str).R: List<Match>
Regex.replace(&str, replacement: &str).R: String
Regex.replace_all(&str, replacement: &str).R: String
Regex.split(&str).R: List<String>
Regex.steps().R: i64
Regex.reset_steps()
Regex.group_count().R: usize
Captures.get(i: usize).R: option.Option<String>
Captures.span(i: usize).R: option.Option<Match>
Captures.len().R: usize                                    // groups including group 0
```

The matching methods take the `Regex` **exclusively** (`fun mut`): the scratch
lives in the `Regex` and a match writes it, so the caller holds a `var`.

`find_at` searches from byte `start`, but `^`, `\b` and `\B` still see the whole
text. A `start` past the end is `None`. `find_all`, `replace_all` and `split`
resume at `end` after a non-empty match and at `end + 1` after an empty one, so
`a*` over `baac` matches at 0 (empty), 1..3, 3 (empty) and 4 (empty). A `split`
returns one more piece than there are matches. A group that did not take part,
or an index past the last group, is `None`; a group inside a repeat reports its
last iteration.

A replacement template uses `$0` for the whole match, `$1`..`$9` for a group and
`$$` for a dollar sign. A group that did not take part, or does not exist, is
empty; a `$` followed by anything else is literal. There is no `${name}`.

## Limits and resources

A compiled `Regex` owns its scratch, allocated once in `compile`, never per input
byte or per match call. The ceilings are: a pattern of 4096 bytes, nesting of 100
groups, a counted repeat of 1000, a program of 50000 instructions (counted
repeats are expanded), and instructions × capture slots of 2,000,000 (about
16 MiB of thread slots). A compiled regex therefore stays below roughly 24 MiB; a
small pattern is a few kilobytes. Matching an input of length `L` takes at most
`N × (L + 1)` thread steps, where `N` is the program size; `Regex.steps()`
reports the count for a test that wants to see the linearity.

## Freestanding

`std/regex` is **hosted only**. It was built into a riscv64 image with an
allocator to see whether the allocator subset was enough. The parser, the program
and the VM link clean, because they are `List` and integer code. Two things do
not: `Match`, `RegexErr` and `Option<String>` each carry a `String`, and the
derived equality the compiler emits for such a `datac`/`enum` calls the hosted
`kelp_map_key_eq`; and `View.slice`/`View.to_string` are runtime calls a
freestanding build does not define. Both are compiler work outside the module, so
it is `Hosted` in `freestanding::std_admission` and a freestanding project that
imports it is refused by name with the allowed-module list.

## Example

```kelp
impl "std/regex"
impl "std/option"
impl "std/result"
impl "std/str"

fun compile_or_die(pat: &str).R: regex.Regex {
    val r = regex.compile(pat)
    if let Ok(re) = r {
        return re
    }
    panic("bad pattern in the example")
}

fun repeated(unit: &str, times: usize, tail: &str).R: String {
    var s = String.with_capacity(str.len(unit) * times + str.len(tail))
    var i: usize = 0
    while i < times {
        s.push_str(unit)
        i += 1
    }
    s.push_str(tail)
    return s
}

fun main() {
    var word = compile_or_die("[a-z]+")
    print(word.is_match("123 abc"))
    print(word.is_match("123 456"))
    if let Some(m) = word.find("one two") {
        print("find: ${m.start}..${m.end} ${m.text}")
    }

    var pair = compile_or_die("(\\w+)=(\\w+)")
    if let Some(c) = pair.captures("x=1 y=2") {
        if let Some(k) = c.get(1) {
            print("key: ${k}")
        }
        if let Some(v) = c.get(2) {
            print("val: ${v}")
        }
    }

    var digits = compile_or_die("(\\d+)")
    print(digits.replace_all("a1b22", "[$1]"))
    print(digits.replace("a1b22", "<$0>"))

    var comma = compile_or_die(",\\s*")
    val parts = comma.split("a, b,c")
    print(parts.len())
    print(parts.get(1).as_str())

    when regex.compile("(ab") {
        Ok(_) -> print("compiled")
        Err(e) -> print("${e.message} @${e.offset}")
    }

    // An exponential pattern for a backtracker, cheap here: doubling the input
    // roughly doubles the steps, not squares them.
    val bomb = repeated("a", 30, "b")
    var p = compile_or_die("(a+)+$")
    p.reset_steps()
    print(p.is_match(bomb.as_str()))
    print(p.steps())

    val bomb2 = repeated("a", 60, "b")
    var p2 = compile_or_die("(a+)+$")
    p2.reset_steps()
    print(p2.is_match(bomb2.as_str()))
    print(p2.steps())
}
```

```text
true
false
find: 0..3 one
key: x
val: 1
a[1]b[22]
a<1>b22
3
b
unclosed group @0
false
248
false
488
```

## See also

- [`std/str`](/stdlib/str)
- [`glob`](/libraries/glob): `*`/`?` shell patterns, the language's other
  pattern matcher
- [Limits in v1](/language/limits)
