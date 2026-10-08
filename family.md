---
title: "Kelp family"
description: "Projects built on Kelp rather than inside it: tools and languages written in Kelp, the conventions they share, and how to start another one."
isPublished: true
tags: "family"
---
The Kelp toolchain (`kelpc`, Coral, Lighthouse) and the library catalogue (fpl) are
the core of the project. The **Kelp family** is everything built *on* Kelp: programs
that are written in the language, use Coral as their build tool, and live in the same
Gitea. They are the language's proof that it can carry real software, and they are
where its rough edges get found first.

## Projects

| Project | What it is | Written in | Repository |
| --- | --- | --- | --- |
| [WebKelp](/family/webkelp) | a markdown-style language (`.wk`) that compiles to plain HTML and CSS, with an escape hatch for everything HTML and CSS can do. The live demo and playground have been removed. | Kelp | [`Juniper/polyp` (folder `web/`)](https://homelabone.xenoo.dev/gittea/Juniper/polyp/src/branch/main/web) |

The core repositories, for comparison, are listed on the [home page](/home).

## Pages

- [WebKelp](/family/webkelp): what it is, how to build it, and a first page.
- [WebKelp syntax reference](/family/webkelp-syntax): every construct, the page settings,
  the CSS pipeline, and what is deliberately not supported.
- [WebKelp playground](/family/webkelp-playground): the in-browser editor, its Kelp backend, and its limits.
- [How WebKelp is built](/family/webkelp-internals): the module layout, the data flow, the
  capability split and the test setup.
- [Writing tools in Kelp](/family/writing-tools-in-kelp): the structure the family projects
  share, and the compiler errors a first real program runs into.

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

## See also

- [Tooling](/tooling) for `kelpc`, Coral and Lighthouse
- [Projects and coral.toml](/getting-started/projects)
- [Libraries (fpl)](/libraries)
