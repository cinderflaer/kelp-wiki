---
title: "Tutorial 17: Polyp UI"
description: "Chapter 17 of the Kelp tutorial: Polyp's Elm architecture (view, update, messages), running a counter on the headless and software backends with no display, the ui grant the GTK backend needs, and what was not run."
isPublished: true
tags: "tutorial, ui, polyp"
---
Polyp is a declarative UI library. You write three things, and Polyp owns the loop:
a **state**, a **message** enum, a **`view`** that is a pure function of the state, and an
**`update`** that applies a message. The tree `view` returns is diffed against the last
one, and only the **patches** are applied to the live widgets. The references are
[`polyp`](/libraries/polyp), [Polyp on a framebuffer](/libraries/polyp-soft) and
[Polyp on bare metal](/libraries/polyp-freestanding).

Polyp is not an `fpl` library; it ships in the compiler repository under `examples/polyp/`.
A consumer links or copies it to `src/deps/polyp/`, so the projects below have
`src/deps/polyp` as a symbolic link to that directory (the convention
`examples/polyp-counter` uses).

## The GTK backend needs a display: not run here

The desktop backend opens a real GTK window. Its smoke tests, such as
`examples/polyp-counter/smoke.sh`, run it under `Xvfb` in the `dev-gtk.nix` shell with the
program driving itself (`POLYP_SMOKE=1`): they need that shell, GTK 4 and a display, so I did
**not** run them for this chapter. What I can show for the GTK backend is what the compiler
checks without one. The GTK module is gated on `ui`, the display domain (chapter 12), and a
program that imports `polyp` without the grant is refused, with the project's `coral.toml`
carrying the library's `[extern.*]` sections (copied from the counter example):

```kelp
impl "deps/polyp/core"
impl "deps/polyp/lib" caps(ui = ["*"])

datac Counter(var count: i32)

enum Msg {
    Inc
}

fun view(s: Counter).R: core.Node<Msg> {
    return polyp.column { k ->
        k.text("a counter")
        k.button("+1", Msg.Inc)
    }
}

fun update(state: mut Counter, msg: Msg) {
    when msg {
        Inc -> {
            state.count += 1
        }
    }
}

fun main() {
    val final = polyp.run(title = "demo", width = 320, height = 200, init = Counter(count = 0), view = view, update = update)
    print(final.count)
}
```

The `impl` line above carries `caps(ui = ["*"])`; the only grant `ui` takes is `*`, because no
call argument names a display. Without it, `kelpc check polyp_g` says:

```text
error: module 'deps/polyp/lib' cannot grant 'ui' access to '*': it does not hold that pattern itself (held: none); 'deps/polyp/lib' holds nothing here because the module that imports it wrote no 'caps(ui = [...])' grant on that `impl` line; a module can delegate less than it has, never more
  --> polyp_g/src/deps/polyp/lib.kp:9:36
exit 1
```

With it, `kelpc check` prints nothing and exits 0:

```text
exit 0
```

I did not build and run this one, only check it (the link step would need GTK).

## The same UI with no display: the headless backend

`core.kp` and the backends below are pure Kelp: no GTK, no `extern`, no `unsafe`, and no
capability. The headless backend applies patches to an in-memory tree, plays a scripted list
of events, and can print the tree as text, so a whole UI program runs in a test.

```kelp
impl "deps/polyp/core"
impl "deps/polyp/headless_backend"
impl "std/fmt"
impl "std/str"

datac Counter(var count: i32)

enum Msg {
    Inc
    Dec
    Reset
}

// view: a pure function of the state. Button ids follow visit order: 0 is +1, 1 is -1, 2 is reset.
fun view(s: Counter).R: core.Node<Msg> {
    return core.column { k ->
        k.text("a counter")
        val shown_count = fmt.int(s.count.to_i64())
        val shown = str.concat("count: ", shown_count.as_str())
        k.text(shown.as_str())
        k.button("+1", Msg.Inc)
        k.button("-1", Msg.Dec)
        k.button("reset", Msg.Reset)
    }
}

// update: an exhaustive `when` over the messages
fun update(state: mut Counter, msg: Msg) {
    when msg {
        Inc -> {
            state.count += 1
        }
        Dec -> {
            state.count -= 1
        }
        Reset -> {
            state.count = 0
        }
    }
}

fun main() {
    // the scripted "user": press +1 three times, -1 once, then quit
    var script: List<core.Event> = List.empty()
    script.push(core.Event.Post(id = 0))
    script.push(core.Event.Post(id = 0))
    script.push(core.Event.Post(id = 0))
    script.push(core.Event.Post(id = 1))
    script.push(core.Event.Quit)

    var backend = headless_backend.new(script = script)
    val final = core.run(backend = backend, init = Counter(count = 0), view = view, update = update)
    print("final count ${final.count}")
    print(headless_backend.dump(backend))
}
```

The project's `coral.toml` is just the name, version and `entry` (no `[unsafe]`, no
`[extern]`), and `src/deps/polyp` links to the library:

```text
$ kelpc build polyp_h -o counter && ./counter
final count 2
column
  text "a counter"
  text "count: 2"
  button id=0 "+1"
  button id=1 "-1"
  button id=2 "reset"

```

Both backends printed this. Reading it:

- `core.column { k -> ... }` is the same scoped trailing block as chapter 10: the block
  captures `s` by borrow, and `k.text`, `k.button`, `k.entry` and the other widgets add
  children. `core.Node<Msg>` is the tree, generic in your message type.
- Buttons get ids in **visit order**: `+1` is 0, `-1` is 1, `reset` is 2. The script's
  `Event.Post(id = 0)` is a click on button 0. Three clicks of `+1` and one of `-1` gave
  `final count 2`, and the dump shows the retained tree after the last render.
- `update` is an exhaustive `when` over the messages (chapter 5). If you add a variant to
  `Msg` and forget it in `update`, the compiler refuses the program, as in chapter 5.
- `core.run(backend, init, view, update)` owns the state and the loop, and returns the final
  state when a `Quit` event arrives.

## The software backend: real pixels, still no display

The soft backend lays the tree out, paints it through an integer rasterizer into a
framebuffer, and repaints only the damaged rectangles. The framebuffer here belongs to a
`HeadlessPlatform` (an in-memory one); a bare-metal kernel supplies its own. Its project has
an `[unsafe]` list naming the three library modules that touch a raw pixel:

```toml
name = "polyp_s"
version = "0.1.0"
entry = "src/main.kp"

# the soft backend draws through the raster, and the headless platform owns the framebuffer:
# those modules are the ones that touch a pointer
[unsafe]
modules = ["deps/polyp/soft/fb", "deps/polyp/soft/draw", "deps/polyp/soft/headless_platform"]
```

```kelp
impl "deps/polyp/core"
impl "deps/polyp/soft/fb"
impl "deps/polyp/soft/headless_platform"
impl "deps/polyp/soft/platform"
impl "deps/polyp/soft_backend"
impl "std/fmt"
impl "std/str"

datac Counter(var count: i32)

enum Msg {
    Inc
    Reset
}

fun view(s: Counter).R: core.Node<Msg> {
    return core.column { k ->
        k.text("a counter")
        val shown_count = fmt.int(s.count.to_i64())
        val shown = str.concat("count: ", shown_count.as_str())
        k.text(shown.as_str())
        k.button("+1", Msg.Inc)
        k.button("reset", Msg.Reset)
    }
}

fun update(state: mut Counter, msg: Msg) {
    when msg {
        Inc -> {
            state.count += 1
        }
        Reset -> {
            state.count = 0
        }
    }
}

fun main() {
    var platform = headless_platform.new(width = 160, height = 100)
    var backend = soft_backend.new()

    var state = Counter(count = 0)
    var tree: core.Node<Msg> = view(state)
    backend.resize(160, 100)
    val first = core.create_all(&tree)
    backend.apply(first)
    backend.layout()
    val f0 = platform.framebuffer()
    val d0 = backend.paint(f0)
    if d0.count() > 0 {
        platform.present(f0, d0)
    }
    print("frame 0: ${d0.count()} dirty rectangle(s), checksum ${fb.checksum(platform.framebuffer())}")

    // the scripted user: two presses of +1, then reset, then quit
    backend.schedule(core.Event.Post(id = 0))
    backend.schedule(core.Event.Post(id = 0))
    backend.schedule(core.Event.Post(id = 1))
    backend.schedule(core.Event.Quit)

    var n = 1
    var running = true
    while running {
        when soft_backend.frame(backend = backend, platform = platform, tree = tree, state = state, view = view, update = update) {
            Idle(next) -> tree = next
            Changed(next) -> tree = next
            Quit(next) -> {
                tree = next
                running = false
            }
        }
        print("frame ${n}: count ${state.count}, ${backend.last_painted()} rectangle(s) repainted, checksum ${fb.checksum(platform.framebuffer())}")
        n += 1
    }
}
```

```text
$ kelpc build polyp_s -o soft && ./soft
frame 0: 1 dirty rectangle(s), checksum 15210313492696918033
frame 1: count 1, 1 rectangle(s) repainted, checksum 11806053530912396779
frame 2: count 2, 1 rectangle(s) repainted, checksum 14091805840602346127
frame 3: count 0, 1 rectangle(s) repainted, checksum 15210313492696918033
frame 4: count 0, 0 rectangle(s) repainted, checksum 15210313492696918033
```

Both backends printed identical pixels, down to the checksum of every frame. Look at the
numbers: frames 0 and 3 have the **same checksum**, because after `reset` the view is the
same as at the start, and the repaint put the identical pixels back. Frame 4 had no event and
repainted **0** rectangles: an idle frame does no painting. Each press repainted one rectangle
(the text that changed), not the window.

## What this is for

The soft backend and the `Platform` contract (`present`, `now_ms`, `now_us`, `poll_event`,
`framebuffer`) are what a custom OS implements to get a UI. `examples/polyp-fb-riscv64` and
`examples/polyp-fb-x86_64` run the same todo program on a bare-metal framebuffer kernel; I
did not boot those here, and [Polyp on bare metal](/libraries/polyp-freestanding) documents
them.

## Exercises

1. Add a `Ten` message and a `+10` button to the headless counter, and have the script press
   it instead of `-1`.
2. Which frames in the `polyp_s` output repainted nothing, and why?

<details>
<summary>Solutions</summary>

1. The changes are one enum variant, one button, one `update` arm, and `id = 3` in the script
   (`+10` is the fourth button). Run on both backends:

```text
final count 13
column
  text "a counter"
  text "count: 13"
  button id=0 "+1"
  button id=1 "-1"
  button id=2 "reset"
  button id=3 "+10"

```

   The count is 3 + 10 = 13 and the tree has the fourth button.

2. Frame 4. The event it ran was the scripted `Quit`, which changes no widget, so nothing was damaged and no rectangle was repainted (`0 rectangle(s) repainted` in the output above, and the checksum is the same as frame 3's).

</details>

Next: [Where to go next](/tutorial/18-next).
