---
title: "Install and hello world"
description: "Run a Kelp program, build an executable and read a compile error, with the real output of kelpc 26.10.4."
isPublished: true
tags: "tutorial, getting-started"
---
**You will learn:** how to run a Kelp file, how to build it into an executable,
and how to read a compiler error.

## Get the compiler

Kelp's compiler is `kelpc`. [Install](/getting-started/install) describes how to
get it, either from a release binary or by building it. Once `kelpc` is on your `PATH`, check it:

```text
$ kelpc version
kelpc 26.10.4
```

## Hello, world

Create a file called `hello.kp`:

```kelp
fun greet(name: &str) {
    print("hello, ${name}")
}

fun main() {
    greet("Kelp")
    print("1 + 2 = ${1 + 2}")
}
```

`fun main()` is where the program starts. `print` writes a line of text. Kelp
has no semicolons, and strings use double quotes. The `${...}` in the string is a
template: it puts the value of an expression into the text.

Run it:

```text
$ kelpc run hello.kp
hello, Kelp
1 + 2 = 3
```

`kelpc run` compiles the file and runs the result in one step. To keep the
executable, build it instead:

```text
$ kelpc build hello.kp -o hello
$ ./hello
hello, Kelp
1 + 2 = 3
```

Without `-o`, the executable is written to `build/hello` in the current
directory. The [kelpc command line](/tooling/kelpc-cli) lists the other options.

## Reading an error

`kelpc check` does everything a build does except write the executable, so it is
the fastest way to ask whether a file is correct. Here is a file with a mistake:

```kelp refused
fun main() {
    val x: i32 = "text"
    print(x)
}
```

```text
$ kelpc check err.kp
error: cannot assign value of type 'str' to 'x' declared as 'i32'
  --> err.kp:2:5
```

Every error has the same shape: `error:` and what is wrong, then `-->` with the
file, line and column. The exit status is 1 when there is an error. Kelp never
converts a string to a number for you, and the next chapter explains why.

## Try it

1. Change `"text"` in `err.kp` to `42`. Does `kelpc check` accept the file now?
2. Add a line `print(x + 1)` to `hello.kp` and run it. What does the output show?

Next: [Values, types and functions](/tutorial/02-values).
