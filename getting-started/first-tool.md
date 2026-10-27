---
title: "A first real tool"
description: "A head you can actually use, written line by line - argv, a capability, an error path and an exit code. Under sixty lines, no dependencies, and every output on this page was produced by the program below."
isPublished: true
tags: "getting-started, cli, filesystem"
---
Hello world proves the toolchain works. This page writes something you could put
on your `PATH`: `head`, which prints the first lines of a file. It is under sixty
lines, needs no dependency, and it is where `argv`, a capability, an error path and
an exit code all show up at once.

Every output below was produced by the program on this page, against `kelpc 26.09.0`.

## The program

```kelp
// head -- the first N lines of a file, ten by default.
//
//   kelpc build head.kp -o head && ./head --lines 3 /tmp/five.txt
//   coral run -- --lines 3 /tmp/five.txt    # inside a Coral project

impl "std/fs"
impl "std/process"
impl "std/path"

fun usage() {
    print("usage: head [--lines N] <path>")
}

// A relative argument is resolved against the working directory, so the gated
// call still receives an absolute path: `fs` patterns are absolute, and the
// capability check normalizes before it matches.
fun absolute_or_here(name: str, here: str) => String {
    if path.is_absolute(name) {
        return String.from_str(name)
    }
    return path.absolute(here, name)
}

// `None` means "not a usable count", and the caller keeps the default.
fun count_from(text: str) => option.Option<i64> {
    val parsed = str.parse_i64(text)
    if let Ok(n) = parsed {
        if n > 0 {
            return option.Option.Some(value = n)
        }
    }
    return option.Option.None
}

fun main() {
    val argv = process.args()
    if argv.len() < 2 {
        usage()
        process.exit(2)
    }

    var count: i64 = 10
    var at: int = 1

    if str.eq(argv.get(1).as_str(), "--lines") {
        if argv.len() < 4 {
            usage()
            process.exit(2)
        }
        if let Some(n) = count_from(argv.get(2).as_str()) {
            count = n
        }
        at = 3
    }

    val target = argv.get(at)
    val here = fs.cwd()
    val resolved = absolute_or_here(target.as_str(), here.as_str())

    val lines = fs.read_lines(resolved.as_str())
    var i: int = 0
    while i < lines.len() && i.to_i64() < count {
        print(lines.get(i).as_str())
        i += 1
    }
}
```

## Build and run it

```sh
kelpc build head.kp -o head
printf 'a\nb\nc\nd\ne\n' > /tmp/five.txt
./head --lines 3 /tmp/five.txt
```

`-o` is what puts the binary where you want it: without it, the artifact and its
generated files land in `build/` in the current working directory, and `-o` only
works when the directory it names already exists.

```
a
b
c
```

The default is ten lines, which is more than this file has, so all of it prints:

```sh
./head /tmp/five.txt
```

```
a
b
c
d
e
```

In a project, Coral forwards the arguments and the exit code, so nothing about the
program changes:

```sh
coral run -- --lines 3 /tmp/five.txt
```

## The four things this program uses

**`argv` is a `List<String>`, and the first entry is the program's own path**, the
same as in C. `argv.len() < 2` is the check for "no arguments", not `< 1`, and the
file path sits at index 1 unless `--lines` claimed it first. `process.args()` is
gated on `process`, but reading it needs only the empty grant:
`impl "std/process"` is enough.

**A path is resolved against the working directory.** `fs` patterns are
absolute, so a relative argument cannot reach a gated call as written: the
program asks `fs.cwd()` for the working directory and runs the argument through
`path.absolute`, which normalizes the join so the check accepts it. Then both
spellings name the same file:

```sh
./head five.txt
./head /tmp/five.txt
```

The second command in the section above passes an absolute path, which
`absolute_or_here` returns unchanged.

**Files fail by panicking, unless you ask for the value.** `fs.read_lines` and
its kin abort the process with the errno. That is a real, uncaught failure and it
looks like this:

```sh
./head /tmp/nope.txt
```

```
panic: fs.read: cannot open file
  errno 2: No such file or directory
```

The exit code is 1. To print a sentence and exit 2 instead, match the `Result`
that `fs.read_text` returns:

```kelp
val text = fs.read_text(resolved.as_str())
if let Err(e) = text {
    print(str.concat("error: ", e.message.as_str()))
    process.exit(2)
}
if let Ok(body) = text {
    val lines = str.split(body.as_str(), "\n")
    // …
}
```

Every fallible call in [`std/fs`](/stdlib/fs) returns a `Result`, and a program
that wants the panic writes `result.expect(call, "message")`.

**Exit codes are the interface.** 0 is success, 2 is a usage error, 1 is a
failure. `kelpc run` forwards the program's status, so a shell script can act on
it, and so does `coral run`.

## Small things to add

Each of these is one function and no new imports beyond the one named:

| Idea | What to use | What it teaches |
| --- | --- | --- |
| A `--chars N` flag, so a file of accented text is cut at N characters and not N bytes | `str.char_count`, `str.byte_index`, `str.copy_range` | the byte and codepoint index sets, and why they differ |
| A `tail` that counts back from the end | `lines.len()`, a descending `while` | indexing from the end, and a loop whose exit is in its condition |
| Several paths, with a header per file | a second loop over the arguments | `argv` as a list rather than positional slots |
| A `total` line at the end, like `wc` | `n.toText()`, a counter | building output when `print` takes one argument |

The `tail` version is the one worth doing: counting down means the loop condition
carries the exit, and `break` and `continue` ([Iterators, `for` and
`break`](/language/iterators)) are there for the early exit that does not fit a
condition. Putting the exit in the header keeps a loop's termination visible, which
is why most programs in this documentation still do it.

## See also

- [Testing what you write](/getting-started/testing): turn `count_from` into something checked
- [`std/process`](/stdlib/process), [`std/fs`](/stdlib/fs), [`std/str`](/stdlib/str)
- [count-lines-words-bytes](/examples/count-lines-words-bytes) and [word-count-with-flags](/examples/word-count-with-flags): the same shape at two sizes, the second with `argparse`
- [When it does not work](/getting-started/troubleshooting)
