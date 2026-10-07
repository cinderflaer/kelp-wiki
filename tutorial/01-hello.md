---
title: "Tutorial 1: Install and hello world"
description: "Chapter 1 of the Kelp tutorial: get a kelpc binary, run a file, build an executable, and see what a compile error looks like. Every program is quoted with its real output."
isPublished: true
tags: "tutorial, getting-started"
---
This is the first chapter of the [Kelp tutorial](/tutorial). It assumes you
program in something like Python, Rust or C and have not seen Kelp. By the end
you will have a compiler, you will have run a program two ways, and you will have
read one compile error.

Every program in this tutorial was written for it, built and run with a prebuilt
`kelpc 26.09.5` on **both** backends (the default LLVM backend and the C oracle,
`KELPC_ORACLE=c`), and the output printed under each one is what both produced. Every
refusal is the real text from `kelpc check`.

## Getting a compiler

Kelp's compiler is `kelpc`. There are two routes, both described on other pages
and not repeated here:

- **Build it from source** with Rust and LLVM 21, as in
  [Install and build](/getting-started/install). Inside the repository's
  `nix-shell shell.nix` it is `cargo build --release -p kelpc`, and the binary
  lands at `target/release/kelpc`.
- **Install a release binary** with the verifying installer `build/install.sh`.
  It never downloads anything and refuses to install what it cannot verify: you
  fetch the binary and its `SHA256SUMS` yourself and pass `--sums`. See
  [Release tooling](/tooling/release-tooling) for the full session. Linux x86_64
  is the only supported platform.

I could not exercise either route from here (building the compiler is out of
scope for this book's checks), so those commands are the wiki's, not mine. What I
did run is everything from here on, with a prebuilt binary:

```text
$ kelpc version
kelpc 26.09.5
```

`kelpc version --verbose` adds the commit, the build date, `rustc` and LLVM
versions, which is what to quote in a bug report.

A program that uses no networking needs only a C compiler and `libLLVM-21`, which
`cc` links against. Programs that touch `std/http`, `std/ws` or `std/tls` also
need OpenSSL (see the requirements table on the install page).

## Hello, world

Create `hello.kp`:

```kelp
fun main() {
    print("hello, world")
}
```

`fun main()` is the entry point. `print` is a builtin; it writes a line. There are
no semicolons, and the string is double-quoted.

Run it:

```text
$ kelpc run hello.kp
hello, world
```

`run` compiles and executes in one step and forwards the program's stdout, stderr and
exit code. To keep the executable, build it:

```text
$ kelpc build hello.kp -o hello
$ ./hello
hello, world
```

With no `-o` the binary lands in `build/<file stem>` in the current directory,
beside a `.ll` (the textual LLVM IR) and a `.o`. `-O0` is a cheap development
build and `-O2` is the default. The full command line is on
[the kelpc CLI page](/tooling/kelpc-cli).

## A slightly bigger first program

```kelp
fun greet(name: &str) {
    print("hello, ${name}")
}

fun main() {
    greet("Kelp")
    print("1 + 2 = ${1 + 2}")
}
```

```text
hello, Kelp
1 + 2 = 3
```

Three things to notice already:

- `"hello, ${name}"` is a **template**: `${...}` splices any printable
  expression into the text (chapter 4 covers text properly).
- `name: &str` is a parameter type. A parameter is a *borrow* of its argument by
  default; chapter 6 explains what that buys you.
- A function that returns nothing writes no return type. A function that returns a value writes `.return: i32` after the parameters (chapter 2).

## Reading an error

`kelpc check` runs everything a build runs except code generation, so it is the
fastest way to ask whether a file compiles. Here is a file with a mistake:

```kelp
fun main() {
    val x: i32 = "text"
    print(x)
}
```

```text
$ kelpc check c1bad.kp
error: cannot assign value of type 'str' to 'x' declared as 'i32'
  --> c1bad.kp:2:5
```

The shape is always the same: `error:`, what is wrong, and a `-->` line with
`file:line:column`. The exit status is 1 for an error. Nothing is converted behind
your back, which is the theme of the next chapter: a string is not an `i32`.

## Exercises

1. Write a program that prints the first three rows of the 7 times table, in the
   form `2 x 7 = 14`. (You will need `impl "std/iter"` and `iter.range(1, 4)`, a
   half-open range; chapter 3 explains both. Treat it as a pattern for now.)
2. Change `c1bad.kp` so it compiles by fixing the annotation rather than the
   value. What type should `x` have?

<details>
<summary>Solutions</summary>

1. Exercise 1:

```kelp
impl "std/iter"

fun main() {
    for i in iter.range(1, 4) {
        print("${i} x 7 = ${i * 7}")
    }
}
```

```text
1 x 7 = 7
2 x 7 = 14
3 x 7 = 21
```

2. A text literal is a `str`, so the annotation is what was wrong. Drop it and
   let the type be inferred:

```kelp
fun main() {
    val x = "text"
    print(x)
}
```

```text
text
```

</details>

Next: [Values, types and functions](/tutorial/02-values).
