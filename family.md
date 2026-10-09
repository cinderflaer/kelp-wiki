---
title: "Kelp family"
description: "Projects built on Kelp rather than inside it: tools and languages written in Kelp, the conventions they share, and how to start another one."
isPublished: true
tags: "family"
---
Projects built on Kelp rather than inside it: tools and languages written in Kelp, the conventions they share, and how to start another one.

## Projects

| Project | What it is | Written in | Repository |
| --- | --- | --- | --- |
| [WebKelp](/family/webkelp) | a markdown-style language (`.wk`) that compiles to plain HTML and CSS, with an escape hatch for everything HTML and CSS can do. The live demo and playground have been removed. | Kelp | [`Lilly/polyp` (folder `web/`)](https://homelabone.xenoo.dev/gittea/Lilly/polyp/src/branch/main/web) |

## Pages

- [WebKelp](/family/webkelp): what it is, how to build it, the live demo and playground that were removed, and a first page.
- [WebKelp syntax reference](/family/webkelp-syntax): every construct, the page settings, the CSS pipeline and what is not supported.
- [How WebKelp is built](/family/webkelp-internals): the module layout, the data flow, the capability split and the test setup.
- [Writing tools in Kelp](/family/writing-tools-in-kelp): the structure the family projects share, and the compiler errors a first program runs into.

## What a family project looks like

Every family project follows the same few rules, and they are the reason these programs
stay small:

1. **A Coral project.** `coral.toml` with `name`, `version` and `entry = "src/main.kp"`,
   sources under `src/`. `kelpc build .` works on it without Coral.
2. **A pure core and a thin shell.** Only the entry module holds the `fs` (or `net`,
   `process`) capability. Every other module is text in, text out, so it needs no grant and
   can be tested without touching the machine. See [Capabilities](/language/capabilities).
3. **No dependencies unless they earn it.** The standard library covers files, paths,
   strings and process arguments; a family project reaches for [fpl](/libraries) only when a
   folder there does something it would otherwise have to write.
4. **Golden tests.** A directory of inputs with their expected outputs, and a script that
   diffs them. Compilers and generators are easy to test this way and hard to test any other.
5. **Its own documentation page here**, in this chapter.

The core repositories are listed in [Contributing](/meta/contributing).

[Back to the home page](/)
