---
title: "Tutorial 11: Projects and modules"
description: "Chapter 11 of the Kelp tutorial: a project directory with coral.toml, impl imports relative to src/, a dependency under src/deps, pub visibility and the real errors for private items and exported signatures."
isPublished: true
tags: "tutorial, projects, modules"
---
Everything so far was one file. A real program is a **project**: a directory with a
`coral.toml`, sources under `src/`, and modules that import each other. A module
**is** a file, `impl "path"` imports one, and `pub` decides what other modules may
see. References: [Projects and coral.toml](/getting-started/projects),
[Modules and imports](/language/modules) and [Coral](/tooling/coral).

## A project

```text
shapes_app/
    coral.toml
    src/main.kp
    src/shapes/circle.kp
    src/deps/mathx/lib.kp
```

The manifest:

```toml
name = "shapes_app"
version = "0.1.0"
entry = "src/main.kp"

[dependencies]
mathx = "Juniper/fpl/mathx"
```

`kelpc` reads only the flat top (`name`, `version`, `entry`) and stops at the first
`[section]`; `[dependencies]`, `[tasks]` and `[toolchain]` belong to
[Coral](/tooling/coral), the build tool.

**A caveat about this chapter.** Coral was not installed on the machine that checked
these pages, so I could not run `coral sync`, which is the command that fetches
`mathx` into `src/deps/mathx/`. Instead I wrote the dependency's `lib.kp` by hand,
one line, exactly where `coral sync` would have put the contents of the `mathx`
folder. Everything below was then built with `kelpc build shapes_app/`, which is
what Coral calls too. The manifest and the dependency's *path* are the wiki's
documented shape; the dependency's *contents* are mine and tiny, not the real
`mathx` library.

The dependency, `src/deps/mathx/lib.kp`:

```kelp
pub fun square(x: f64).return: f64 = x * x
```

The module, `src/shapes/circle.kp`:

```kelp
impl "deps/mathx/lib"

pub datac Circle(val r: f64)

fun Circle.area().return: f64 = mathx.square(self.r) * 3.14159

fun secret().return: i32 = 42

pub fun unit_circle().return: Circle = Circle(r = 1.0)
```

The entry, `src/main.kp`:

```kelp
impl "shapes/circle"

fun main() {
    val c = circle.Circle(r = 2.0)
    print("area ${c.area()}")
    print("unit ${circle.unit_circle().area()}")
}
```

```text
$ kelpc build shapes_app/ -o app && ./app
area 12.566360
unit 3.141590
```

Both backends printed this.

## What to notice

- **`impl` paths are relative to `src/`**, not to the importing file or the working
  directory. `impl "shapes/circle"` is `src/shapes/circle.kp`, from any depth. The
  module's name is the last path segment, so the call site writes `circle.Circle`.
- **A dependency's entry is `impl "deps/<name>/lib"`**, and the module is named after
  the folder: `mathx`. That is why `circle.kp` calls `mathx.square(...)`. A dependency
  is a git remote and there is no version number, no lockfile and no registry; what
  `coral sync` put there *is* what you build with.
- **Nothing is imported by default**, not even the standard library: you write
  `impl "std/str"` as in earlier chapters. A module's own top-level names need no
  qualifier, and everything else is `module.name`.
- The `impl` word has two uses: `impl "path"` (a string) imports, and
  `impl Trait for Type` (chapter 9) implements. The token after `impl` tells them
  apart. Imports go first in the file, then `const`/`pd`, then types and functions.

## Visibility

Every top-level item is private to its module until it is marked `pub`. `Circle` and
`unit_circle` are `pub`; `secret` is not. Reaching for it from another module gets an
error distinct from a name that does not exist:

```kelp
impl "shapes/circle"

fun main() {
    print("${circle.secret()}")
}
```

```text
$ kelpc check bad_private
error: 'circle.secret' is private: 'secret' is declared in module 'circle' without 'pub', so only that module can name it; add 'pub' to its declaration to export it
  --> bad_private/src/main.kp:4:14
```

Three more rules, each with its real message:

- **`pub` goes on the type, never on a method.** A method is reachable when its
  type is. Writing `pub fun Circle.area()` is refused:

```text
$ kelpc check bad_pubmethod
error: 'pub' cannot be written on a method: a method's reachability follows its declaring type, so mark the type 'pub' instead
  --> bad_pubmethod/src/shapes/circle.kp:5:5
```

- **An exported signature may only name exported types.** A `pub fun` that returns
  a private `Hidden` is refused, even though a caller could technically use the
  value:

```kelp
datac Hidden(val r: f64)

pub fun make().return: Hidden = Hidden(r = 1.0)
```

```text
$ kelpc check bad_sig
error: 'shapes.circle.make' is exported but its signature names 'shapes.circle.Hidden', which module 'shapes/circle' does not export: add 'pub' to 'Hidden', or make 'shapes.circle.make' private
  --> bad_sig/src/shapes/circle.kp:3:19
```

- A `pd` never takes `pub`, and `pub` is accepted only on a top-level `fun`,
  `extern fun`, `extern type`, `datac`, `enum` or `const`
  (see [Modules and imports](/language/modules)).

Inside its own file an item is always reachable by its bare name; `pub` only governs
another module's `module.item` spelling.

## Exercises

1. In a new project, add `src/shapes/rect.kp` with a `pub datac Rect`, an area
   method, and a `pub fun square(side: f64).return: Rect`, and call both from `main`.
2. In `bad_private`, what is the smallest change that makes the program compile?

<details>
<summary>Solutions</summary>

1. `coral.toml` with the same three flat lines and no dependencies, then:

```kelp
pub datac Rect(val w: f64, val h: f64)

fun Rect.area().return: f64 = self.w * self.h

pub fun square(side: f64).return: Rect = Rect(w = side, h = side)
```

```kelp
impl "shapes/rect"

fun main() {
    val r = rect.Rect(w = 2.0, h = 3.0)
    val s = rect.square(4.0)
    print("${r.area()} ${s.area()}")
}
```

```text
$ kelpc build ex11/ -o app && ./app
6.000000 16.000000
```

2. Add `pub` to `fun secret()` in `circle.kp`, which is what the error message says.
   Built and run on both backends, `main` then prints:

```text
42
```

</details>

Next: [Capabilities](/tutorial/12-capabilities).
