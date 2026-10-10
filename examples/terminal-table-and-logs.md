---
title: "Terminal table and logs"
description: "A report that a script can parse on stdout and a human can read on stderr, with colour that switches itself off according to the NO_COLOR convention."
isPublished: true
tags: "example, cli"
---

The `terminal-table-and-logs` program prints a coloured table on stdout.
It prints log records on stderr, so a script can parse one and a person can read the other.
Colour switches off when the `NO_COLOR` variable is set.

| | |
| --- | --- |
| Source | [`src/terminal-table-and-logs.kp`](https://homelabone.xenoo.dev/gittea/Lilly/kelp-wiki-wikijs/raw/branch/main/examples/src/terminal-table-and-logs.kp) |
| Needs | `term` (env), `log` (time), `table` |
| Shows | two grants in one program, escapes against plain text, and stdout against stderr |

## The dependencies and the two grants

```toml
[dependencies]
term  = "Lilly/fpl/term"
log   = "Lilly/fpl/log"
table = "Lilly/fpl/table"
```

```kelp
impl "deps/term/lib" caps(env = ["NO_COLOR"])
impl "deps/log/lib" caps(time = [])
```

`term` reads the environment for `NO_COLOR`, so it needs the `env` domain, named
down to the one variable. `log` stamps each record with the clock, so it needs
`time`. `table` needs nothing.

## The program

```kelp project
impl "std/env"
impl "deps/term/lib" caps(env = ["NO_COLOR"])
impl "deps/log/lib" caps(time = [])
impl "deps/table/lib"

fun main() {
    var headers: List<String> = List.empty()
    headers.push("check")
    headers.push("result")
    var report = table.new_table(headers)

    var build_row: List<String> = List.empty()
    build_row.push("build")
    build_row.push("ok")
    table.add_row(report, build_row)

    var test_row: List<String> = List.empty()
    test_row.push("tests")
    test_row.push("2 failed")
    table.add_row(report, test_row)

    print!(table.render(&report))
    print("")

    // Colour on: no NO_COLOR in the environment, so each call wraps the text in
    // an SGR sequence. `cat -v` in the recorded run shows the escapes.
    env.unset("NO_COLOR")
    print(term.green("build ok"))
    print(term.red("tests failed"))
    print(term.bold("summary"))
    print("colour disabled = ${term.no_color()}")

    // Colour off: the variable's presence is the whole switch, so the same three
    // calls now return their argument unchanged.
    env.set("NO_COLOR", "1")
    print(term.green("build ok"))
    print(term.red("tests failed"))
    print(term.bold("summary"))
    print("colour disabled = ${term.no_color()}")

    // Log records are written to stderr, so stdout stays machine-readable.
    val logger = log.new_logger("report", log.LEVEL_INFO)
    log.info(&logger, "report rendered")
    log.error(&logger, "two checks failed")
    log.debug(&logger, "this one is dropped, below the minimum level")
}
```

## Run it

```sh
kelpc run terminal-table-and-logs.kp
```

## Output

stdout, shown through `cat -v` so the escape bytes appear as `^[`:

```
check | result  
------+---------
build | ok      
tests | 2 failed
^[[32mbuild ok^[[0m
^[[31mtests failed^[[0m
^[[1msummary^[[0m
colour disabled = false
build ok
tests failed
summary
colour disabled = true
```

stderr, where the timestamp is the one thing that varies:

```text
[1789841865] INFO report: report rendered
[1789841865] ERROR report: two checks failed
```

## What to take from it

- **`NO_COLOR` is checked on every colour call,** so setting it mid-run takes
  effect immediately. Its *presence* is the switch, whatever its value.
- **The program sets the variable itself,** which is why the two halves of the
  output are the same on any machine. The entry module holds every domain, so it
  may touch `env` directly; a library would be granted the one name.
- **`term` returns strings, it does not print.** A caller that wants to measure or
  buffer its output can; this one hands each string to `print`.
- **The cursor and clear helpers deliberately ignore `NO_COLOR`,** because moving
  the cursor is not colour and disabling it would break a caller that depends on
  it.
- **Log records go to stderr with a unix timestamp and a stable prefix,** so a
  pipeline that reads stdout is unaffected. A record below the logger's minimum
  level is dropped before anything is formatted.
- **Two capabilities, two patterns,** and neither widens the other: `env` is named
  down to one variable, and `time` has no pattern to restrict.
- **The table's trailing spaces are padding,** and `render` emits no final
  newline, which is why the program prints an empty line after it.

## See also

- [`term`](/libraries/term), [`log`](/libraries/log), [`table`](/libraries/table)
- [`std/env`](/stdlib/env) and [`std/time`](/stdlib/time) for the two gated modules
- [Capability patterns](/reference/capability-patterns)
