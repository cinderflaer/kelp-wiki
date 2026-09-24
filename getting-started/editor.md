---
title: "Set up your editor"
description: "Lighthouse is the language server, and the compiler is the authority behind it - diagnostics come from a real kelpc run on open and on save. This page covers the IntelliJ setup, kelpc fmt, and what to do with no editor at all."
isPublished: true
tags: "getting-started, tooling"
---
An editor is optional. Kelp compiles from the command line with no project and no
server, and that never stops working. What the editor buys you is the compiler
telling you about an error when you save instead of when you run.

## What the server can and cannot do

Lighthouse is a language server, and the split in it is worth knowing before you
trust a squiggle:

| Feature | Where the answer comes from |
| --- | --- |
| Diagnostics | `kelpc`, run on open and on save |
| Completion, hover, go-to-definition, symbols, rename, inlay hints | an index the server builds by reading the project's `.kp` files |

`kelpc` is the authority on what compiles, and the index has no type checker. The
rule from Lighthouse's README is the useful summary: **the index guesses and the
compiler decides**. A wrong guess costs you an offer, and it cannot make a wrong
edit on its own, because every auto-import arrives as a literal `impl` line you
see and accept.

## The pieces

| Piece | What it is |
| --- | --- |
| `server/` | the `lighthouse` binary: an LSP server over stdio, with no command-line flags |
| `intellij/` | an IntelliJ plugin: `.kp` file type, the server, a Kelp project entry, a Coral run configuration |

The server is a plain LSP server, so any editor whose LSP client can start it can
drive it. The IntelliJ plugin is the client this project ships, and it is the
only one. It is unpublished, so it is installed from a local build. See
[Lighthouse](/tooling/lighthouse) for what it contributes in full.

## IntelliJ

**The plugin requires IntelliJ IDEA Ultimate.** It uses the LSP client API, which
is not in Community builds.

```sh
git clone https://homelabone.xenoo.dev/gittea/Juniper/lighthouse
cd lighthouse/intellij
./gradlew buildPlugin
```

Install the zip from **Settings ▸ Plugins ▸ ⚙ ▸ Install Plugin from Disk…**, or
add the self-hosted update site once under **Settings ▸ Plugins ▸ ⚙ ▸ Manage
Plugin Repositories**:

```text
https://homelabone.xenoo.dev/gittea/Juniper/lighthouse/raw/branch/main/intellij/updatePlugins.xml
```

Everything `lighthouse` offers arrives over LSP, so a feature the server gains
needs no plugin update to appear in the editor. Beyond that, the plugin adds
**File ▸ New ▸ Project ▸ Kelp**, which scaffolds a project with `coral init`, and
a Coral run configuration with a gutter run icon on `fun main()`.
**Settings ▸ Languages & Frameworks ▸ Kelp** shows the project's `[toolchain]` pin
and can install that compiler version in the background, so the IDE uses the
compiler the project names.

## Formatting

`kelpc fmt` owns whitespace and nothing else: indentation, spacing, trailing
whitespace, the comment rules. It is token-faithful (no token's text is
rewritten), comment-preserving, and it leaves a file it cannot parse alone.

```sh
kelpc fmt -w src/            # rewrite every .kp file under src/
kelpc fmt --check src/       # write nothing, exit 1 if anything would change
```

A path may be a file or a directory, and a directory recurses, so those two
commands cover a whole project.

`--check` is the CI shape. One caveat: **the server does not call `fmt`**, so
there is no format-on-save. Run it yourself when you like, or add it to a
pre-commit hook.

## With no editor at all

`kelpc run file.kp` is enough to write the language in any text editor, and
`kelpc fmt -w` covers the formatting. A rebuild loop is three lines of shell:

```sh
while sleep 2; do
    kelpc build src/main.kp -o /tmp/app && /tmp/app
done
```

Two habits make that pleasant rather than painful:

- `kelpc fmt --check <path>` before you commit, so the diff holds changes and not
  whitespace;
- read the error's `--> file:line:col` and go to the line, rather than reading the
  message bottom-up. [When it does not work](/getting-started/troubleshooting) is
  a page about exactly that.

## Try this

Set the editor up, then make it show you something. Write a program with an
unknown name and save it:

```kelp
fun main() {
    println("hello")
}
```

`kelpc` says `error: call to undefined function 'println'` with a span, and the
quick fix offers `print`, which compiles. The diagnostic came from a real compiler
run and the fix came from the index, which is the whole design in one gesture.

## See also

- [Lighthouse](/tooling/lighthouse): every feature, and its deliberate gaps
- [`kelpc` CLI](/tooling/kelpc-cli): `build`, `run`, `fmt`, and where artifacts land
- [Your first program](/getting-started/first-program)
- [Install and build](/getting-started/install)
