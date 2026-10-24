---
title: "`std/regex`"
description: "A linear-time regular expression engine in pure Kelp: a Pike VM over bytes, a documented pattern subset, and backreferences, lookaround and named groups refused at compile. Freestanding with the allocator pair."
isPublished: true
tags: "stdlib, text"
---
A linear-time regular expression engine in pure Kelp. It needs no capability of
its own, and it is **freestanding-capable** with the `[target] alloc`/`dealloc`
pair; a build with no allocator pair is refused the way any heap type is.

```kelp
impl "std/regex"
```

The pattern is data, not syntax: the language itself still has no regular
expression literal, so a pattern is a `&str` handed to `regex.compile`. The
engine was specified in `stdlib/regex.md`.

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
datac RegexErr(val message: String, val offset: int)
datac Match(val start: int, val end: int, val text: String)
datac Captures(val text: String, val slots: List<i32>)
```

```kelp
regex.compile(pattern: &str) => result.Result<Regex, RegexErr>
regex.is_match(pattern: &str, text: &str) => bool          // panics on a bad pattern
Regex.is_match(&str) => bool
Regex.find(&str) => option.Option<Match>
Regex.find_at(&str, start: int) => option.Option<Match>
Regex.captures(&str) => option.Option<Captures>
Regex.find_all(&str) => List<Match>
Regex.replace(&str, replacement: &str) => String
Regex.replace_all(&str, replacement: &str) => String
Regex.split(&str) => List<String>
Regex.steps() => i64
Regex.reset_steps()
Regex.group_count() => int
Captures.get(i: int) => option.Option<String>
Captures.span(i: int) => option.Option<Match>
Captures.len() => int                                    // groups including group 0
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

`std/regex` is **freestanding-capable** with the `[target] alloc`/`dealloc` pair
(kernel stage 23), and its row in `freestanding::std_admission` is `Allocator`.
The parser, the program and the Pike VM are `List` and integer code, so they
always linked clean; two things beside them did not, and both are compiler work
that shipped here.

- `Match`, `RegexErr` and `Option<String>` each carry a `String`, and the derived
  key equality the compiler emits for such a `datac`/`enum` (every type whose
  fields are all keyable, whether or not it is ever a `Map` key) called the
  hosted `kelp_map_key_eq`. The LLVM backend now emits that helper into a
  freestanding image as the same length-aware byte loop `View.eq` uses, so a
  `String`-field `datac` compares and hashes with nothing for `ld.lld` to
  resolve.
- `View.slice` and `View.to_string` had no freestanding lowering and the `View`
  type itself was refused. `View` is a borrowed `{ptr, len}` pair with no storage
  of its own, so all five of its operations are now admitted; `slice` is pointer
  arithmetic with the same bounds panic the hosted body has, and `to_string`
  allocates through the project's own allocator like every other `String`
  builder.

The acceptance is `examples/kernel0-eq` (riscv64) and
`examples/kernel0-eq-x86_64`: a `String`-field `datac` written `derive(eq, hash)` and
a `Map<Pair, i32>` that uses that pair, a `Bytes`-field
`datac` whose declared `eq` walks the bytes, a `View.slice` and
`View.to_string`, and a `regex.compile("[a-z]+(\\d+)")` matched against
`"xx hello42"`, with the match text and capture group printed over the UART
under QEMU. Both images link with no undefined symbol but the linker script's
weak `__bss_*`, and `tests/projects/freestanding_std_regex` is the build
project that pins the undefined-symbol check.

## Example

```kelp
impl "std/regex"
impl "std/option"
impl "std/result"
impl "std/str"

fun compile_or_die(pat: str) => regex.Regex {
    val r = regex.compile(pat)
    if let Ok(re) = r {
        return re
    }
    panic("bad pattern in the example")
}

fun repeated(unit: str, times: int, tail: str) => String {
    var s = String.with_capacity(str.len(unit) * times + str.len(tail))
    var i: int = 0
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
