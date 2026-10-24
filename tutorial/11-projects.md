---
title: "Modules and capabilities"
description: "Splitting a program into modules with pub, importing them with impl, and the capability grants that decide what each module may touch: files, the network, processes and the clock, with the real compiler errors."
isPublished: true
tags: "tutorial, projects, modules, capabilities"
---
**You will learn:** how one file imports another, how `pub` controls what is
visible, and how a module must be granted each power it uses, such as reading
files.

## Modules

A module is a `.kp` file. Here are two files in the same folder. `geometry.kp`
is the module:

```kelp
pub datac Rect(val w: i32, val h: i32)

pub fun area(r: Rect) => i32 = r.w * r.h

fun secret() => i32 = 42
```

`main.kp` imports it with `impl "geometry"`:

```kelp project
impl "geometry"

fun main() {
    val r = geometry.Rect(w = 3, h = 4)
    print(geometry.area(r))
}
```

```text
$ kelpc run main.kp
12
```

The file name is the module name: `geometry.kp` is `geometry`. Its `pub` items are
visible to the file that imports it. Items without `pub`, such as `secret`, are
private to their own file. Using one from outside is an error:

```kelp project
impl "geometry"

fun main() {
    print(geometry.secret())
}
```

```text
$ kelpc check main2.kp
error: 'geometry.secret' is private: 'secret' is declared in module 'geometry' without 'pub', so only that module can name it; add 'pub' to its declaration to export it
  --> main2.kp:4:11
```

A larger program uses the same idea in a project directory with a manifest. The
[projects page](/getting-started/projects) describes that layout.

## Capabilities

A program in Kelp cannot read a file, open a network connection, start a process
or read the clock unless the module making the call was granted that power. The
grant is written in the source, on the `impl` line.

The entry file, the one with `main`, holds every grant. A module that it imports
holds none, until the importing line grants it. Here is a module that reads a
file:

```kelp
impl "std/fs"

pub fun count_lines(path: str) => i64 {
    val lines = fs.read_lines(path)
    return lines.len().to_i64()
}
```

`impl "std/fs"` brings in the file module. Without a grant, the importing file
must give `notes` the `fs` power, as the next program does:

```kelp project
impl "notes" caps(fs = ["/tmp/kelp-demo/**"])

fun main() {
    print(notes.count_lines("/tmp/kelp-demo/notes.txt"))
}
```

To run it, first create the file the program reads:

```sh
mkdir -p /tmp/kelp-demo
printf 'alpha\nbeta\ngamma\n' > /tmp/kelp-demo/notes.txt
```

```text
$ kelpc run reader.kp
3
```

The pattern `/tmp/kelp-demo/**` says which paths the module may touch: this folder
and everything in it. A call to a path outside the pattern stops the program:

```kelp project
impl "notes" caps(fs = ["/tmp/kelp-demo/**"])

fun main() {
    print(notes.count_lines("/etc/passwd"))
}
```

```text
$ kelpc run denied.kp
notes.kp:4:17: panic: '/etc/passwd' is outside the fs capability granted to module 'notes'
  granted:
    /tmp/kelp-demo/**
```

If the importing file gives no grant at all, the compiler refuses the program
before it runs. Here is `main` without the `caps(...)` clause:

```kelp project
impl "notes"

fun main() {
    print(notes.count_lines("/tmp/kelp-demo/notes.txt"))
}
```

```text
$ kelpc check nogrant.kp
error: 'std.fs.read_lines' needs the 'fs' capability, which module 'notes' was not granted; the module that imports this one must delegate it (`impl "<this module>" caps(fs = ["<pattern>"])`)
  --> notes.kp:4:17
```

The error is about `notes`, the file that makes the call, and it names the power
it lacks. The fix goes in the file that imports `notes`.

The domains are `fs`, `net`, `process`, `env`, `time`, `rand`, `machine`, `ui`, `mmio`, `irq`
and `frames`. A grant with an empty list, such as `process = []`, grants nothing.
The [capabilities reference](/language/capabilities) lists them all.

## Try it

1. Add a `pub fun shout(s: &str) => String` to `geometry.kp` that returns
   `String.from_str(s = s)`. Import it from `main.kp` and print the result.
2. In `reader.kp`, change the pattern to `/tmp/other/**` and run it. Read the
   panic. What does the module need in order to read the file?

Next: [Tools and tests](/tutorial/15-tooling).
