---
title: "`polyp`: a declarative native UI library over GTK4"
description: "Polyp is the Elm architecture over GTK4: `view` is a pure function of your state, `update` is an exhaustive `when` over a `Msg` enum, and a builder with trailing blocks writes the widget tree."
isPublished: true
tags: "library, ui"
---
A declarative native UI library for Kelp, over GTK4. The application describes
what the screen should be for the current state; Polyp owns the loop and builds
the widgets. It wraps GTK's own widgets rather than drawing, so a Polyp window is
a GTK window.

Gated on `ui` (the display domain, [Capabilities](/language/capabilities)).

Polyp is **not** an `fpl` folder. It ships in the compiler's own repository at
`examples/polyp/` (v1), with `examples/polyp-v0/` as a frozen copy of the earlier
plain-constructor API, because a consumer declares its native surface in its own
`coral.toml` rather than depending on a folder (see
[Using the library](#using-the-library)).

## The programming model: the Elm architecture

A view is a function of state, and it is re-rendered when the state changes. The
application writes three things and Polyp owns the rest:

- `State`: any type the application likes.
- `Msg`: an `enum` of the things a user can do.
- `view`: `fun(State).R: Node<Msg>`, a pure function of the state.
- `update`: `fun(mut State, Msg)`, where the application writes one exhaustive
  `when`.

This is not a style choice. It is the one architecture Kelp's ownership rules
allow:

- A Kelp closure **owns** its captures and cannot capture a borrow
  (`syntax.md` §7.4), and Kelp has no shared-ownership type to put the
  application state behind.
- So no callback captures the state at all. A button's handler is a closure
  whose entire environment is one small integer. It posts that integer to a
  fixed-size C queue, and the loop, which **does** own the state, reads it back,
  finds the `Msg` stored at that position in the tree it built, calls `update`,
  re-runs `view` and rebuilds the widgets.

GTK callbacks and the loop run on the same thread, so the queue needs no lock.

The builder block is the one place state is read from a callback-shaped literal,
and it is safe because the literal never outlives the call: it is a
`scoped fun(mut Children<M>)` value the callee may only call during `column` or
`row`, and its captures are shared borrows released afterwards
([Functions](/language/functions#trailing-blocks-and-scoped-parameters)). An
**exclusive** capture (the `state.count += 1` shape) is refused, so a button
still carries a `Msg`, never a mutation.

That makes the two declarative claims hold literally:

- **`view` is a pure function of the state.** It takes the state and returns a
  `Node<Msg>`; it is called on every state change and can do nothing else.
- **`update` is an exhaustive `when` over the `Msg` enum.** Adding a variant and
  forgetting to handle it is a compile error.

## Using the library

A Kelp library has no manifest, and a project's modules resolve only under its own
`src/`, so a Polyp consumer does two things by hand:

1. **Put the sources where `impl` can reach them.** Copy `examples/polyp/` to
   `src/deps/polyp/`, or link it, which is what `examples/polyp-counter/` does:

   ```sh
   mkdir -p src/deps
   ln -s ../../../polyp src/deps/polyp
   ```

2. **Paste the `[extern.*]` sections into your `coral.toml`.** The native
   symbols, headers and `pkg-config` package live in the consumer's manifest, and
   the section ids are the `impl` paths the library uses. A GTK binding needs the
   `ui` domain, which takes only the wildcard. See
   [Coral: the manifest](/tooling/coral#extern-user-modules-that-bind-a-native-symbol).

   ```toml
   [extern."deps/polyp/gtk"]
   domain = "ui"
   library = "gtk-4"
   header = "gtk/gtk.h"
   pkg_config = "gtk4"
   symbols = ["gtk_init", "gtk_window_new", "gtk_window_set_title", "gtk_window_set_default_size", "gtk_window_set_child", "gtk_window_present", "gtk_box_new", "gtk_box_append", "gtk_label_new", "gtk_label_set_markup", "gtk_widget_set_size_request", "gtk_entry_new", "gtk_editable_set_text", "gtk_editable_get_text", "gtk_widget_unparent", "gtk_button_new_with_label", "g_object_unref", "g_object_ref_sink", "g_main_context_iteration", "g_timeout_add_full", "connect=g_signal_connect_data", "connect_ret=g_signal_connect_data"]

   [extern."deps/polyp/queue"]
   domain = "ui"
   library = "c"
   header = "polyp_queue.h"
   include_dirs = ["src/deps/polyp/include"]
   symbols = ["polyp_post", "polyp_poll", "polyp_post_edit", "polyp_poll_edit", "polyp_poll_edit_text"]
   ```

Then grant the domain at the import:

```kelp
impl "deps/polyp/lib" caps(ui = ["*"])
```

The library holds `ui` and the application does not need to: `main` never names a
GTK call.

## API

```kelp
pub enum Node<M> {
    Column(val children: List<Node<M>>)
    Row(val children: List<Node<M>>)
    Text(val text: String, val size: i32, val bold: bool)
    Spacer(val height: i32)
    Entry(val text: String, val on_change: fun (String).R: M)
    Button(val label: String, val on_click: M)
}

pub datac Children<M>(var items: List<Node<M>>)
pub fun column<M>(block: scoped fun(mut Children<M>)).R: Node<M>
pub fun row<M>(block: scoped fun(mut Children<M>)).R: Node<M>
fun mut Children<M>.text(t: str)
fun mut Children<M>.text_styled(t: str, size: i32, bold: bool)
fun mut Children<M>.spacer(height: i32)
fun mut Children<M>.button(label: str, on_click: move M)
fun mut Children<M>.entry(value: str, on_change: fun (String).R: M)
fun mut Children<M>.column(block: scoped fun(mut Children<M>))
fun mut Children<M>.row(block: scoped fun(mut Children<M>))

pub fun plain_column<M>(children: move List<Node<M>>).R: Node<M>
pub fun plain_row<M>(children: move List<Node<M>>).R: Node<M>
pub fun text<M>(text: move String).R: Node<M>
pub fun button<M>(label: move String, on_click: move M).R: Node<M>

pub fun run<S, M>(title: str, width: i32, height: i32, init: move S,
                  view: fun(S).R: Node<M>, update: fun(mut S, M)).R: S

pub const QUIT_ID: i32
pub fun schedule_post(delay_ms: u32, id: i32)
pub fun schedule_quit(delay_ms: u32)
pub fun schedule_set_entry(delay_ms: u32, index: i32, new_text: str)
pub fun entries_built().R: i32
```

- `run` opens one `GtkWindow` with the given title and default size, renders the
  first tree, and iterates the default GLib main context until a quit is posted.
  It **returns the final state** (`init` is moved in, so returning it is how the
  caller reads what the run left behind).
- `fun(S)` in `view`'s type is "view borrows the state": a parameter of an owned
  type is a shared borrow, so an application writes
  `fun view(state: Counter).R: Node<Msg>` with no `&` anywhere. `update` is
  written `fun update(state: mut Counter, msg: Msg)`.
- `text` is a label. `text_styled(text, size, bold)` sets Pango markup after
  escaping the text, so a `&` or `<` is shown, not parsed; `size` is points and
  `0` means GTK's default. `spacer(height)` reserves vertical pixels.
- `entry(value, on_change)` is a text field. `value` seeds the text the first time
  the widget is built; `on_change` is a plain `fun(String).R: M` that turns the
  live text into the application's `Msg`.
- Button ids are handed out in tree order: the `i`-th `Button` in a depth-first
  walk is id `i`. `QUIT_ID` is `-2`, because `polyp_poll` answers `-1` for an
  empty queue. Entry ids are a separate space, so inserting an entry does not
  shift button ids.
- `schedule_post`, `schedule_quit` and `schedule_set_entry` post an id (or ask
  the loop to set an entry's text) after a delay. They exist for programs that
  have to run with no user, and they are the only reason `g_timeout_add_full` is
  bound.
- `entries_built()` is a diagnostic: the number of `Entry` widgets the process
  has built. A run that reuses its entries has a smaller count than one that
  rebuilds them.

## The counter

`examples/polyp-counter/` is this program, complete and buildable, and its
`src/deps/polyp` link points at `examples/polyp/`:

```kelp
impl "deps/polyp/lib" caps(ui = ["*"])
impl "std/env"
impl "std/fmt"
impl "std/str"

datac Counter(var count: i32, var draft: String)

enum Msg {
    Inc
    Dec
    Reset
    Changed(val text: String)
}

fun changed(text: String).R: Msg = Msg.Changed(text = String.from_str(text.as_str()))

fun view(s: Counter).R: polyp.Node<Msg> {
    return polyp.column { k ->
        k.text_styled("a counter", 0, true)
        val shown_count = fmt.int(s.count.to_i64())
        val shown = str.concat("count: ", shown_count.as_str())
        k.text(shown.as_str())
        k.spacer(6)
        k.button("+1", Msg.Inc)
        k.button("-1", Msg.Dec)
        k.button("reset", Msg.Reset)
        k.entry(s.draft.as_str(), changed)
    }
}

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
        Changed(text) -> {
            state.draft = String.from_str(text.as_str())
        }
    }
}

fun smoke_enabled().R: bool {
    val value = env.get("POLYP_SMOKE")
    return str.eq(value.as_str(), "1")
}

fun arm_smoke() {
    polyp.schedule_post(delay_ms = 100, id = 0)
    polyp.schedule_post(delay_ms = 150, id = 0)
    polyp.schedule_post(delay_ms = 200, id = 1)
    polyp.schedule_set_entry(delay_ms = 300, index = 0, new_text = "typed")
    polyp.schedule_quit(delay_ms = 400)
}

fun main() {
    if smoke_enabled() {
        arm_smoke()
    }
    val final = polyp.run(
        title = "polyp counter",
        width = 320,
        height = 200,
        init = Counter(count = 0, draft = String.from_str("")),
        view = view,
        update = update,
    )
    print(final.count)
    print(final.draft)
    print(polyp.entries_built())
}
```

The plain-constructor style of the same view still compiles:

```kelp
var kids: List<polyp.Node<Msg>> = List.empty()
kids.push(polyp.text(String.from_str("hi")))
kids.push(polyp.button(String.from_str("+1"), Msg.Inc))
return polyp.plain_column(kids)
```

## Headless testing with Xvfb

The counter is proved by `examples/polyp-counter/smoke.sh`. It builds with the
default (`llvm`) backend, then runs the binary under `xvfb-run -a` with
`GSK_RENDERER=cairo GDK_BACKEND=x11` and `POLYP_SMOKE=1`. That mode makes the
program schedule its own input: post id 0 (Inc), post id 0 (Inc), post id 1
(Dec), set the entry's text to `typed` at 300 ms (which fires the entry's real
`changed` signal), then quit after 400 ms.

The run is real: a GTK window, real click-callback thunks, the real queue, and an
entry whose text is set through its own `changed` signal. The only thing missing
is a user. stdout must be exactly:

```
1
typed
1
```

That is the count after the clicks, the text the entry posted, and one entry
widget built across all the rebuilds. A crash, a hang (`timeout 60`) or anything
else on stdout fails the script. GTK's own Xvfb warnings go to stderr and are not
the program's answer.

```sh
examples/polyp-counter/smoke.sh
```

The C backend produces the same three lines; both backends are supported.

## Reconciliation, exactly

Every state change rebuilds the whole tree and replaces the window's child, with
exactly one identity rule: **an `Entry` at ordinal position `i` in the new walk
reuses the `i`-th entry widget of the previous walk.** The old box is emptied
with `gtk_widget_unparent`, each entry keeps its own GTK reference, and the
reused widget is appended into the new box, so its live text, cursor and
selection survive: focus survives a rebuild and the user's typing is not lost.
The new tree's `value` is ignored for a reused entry; it only seeds a freshly
built one.

Everything else is rebuilt. This is not a tree diff and does not claim to be.

## Known limits

- **Whole-tree rebuild with one retention rule.** Nothing but an `Entry` at the
  same ordinal is reused, so no other widget identity or widget state (scroll,
  selection, animation) is preserved.
- **Focus retention is entry-only and ordinal.** A focused button, or a focused
  entry whose ordinal changed, does not keep focus.
- **No lazy or keyed lists**, no styling beyond `text_styled`, and no layout
  beyond `Column`/`Row`, GTK's default spacing and `Spacer`.
- **Ids are positional.** They are re-derived from tree order on every render, so
  an application that leans on raw ids is leaning on an implementation detail.
  The smoke run does, deliberately, because it has no user to click anything.
- **No exclusive captures.** A builder block may read the borrowed state, but
  `state.count += 1` inside a block is refused; a mutation goes through a `Msg`.
- **No library manifest.** See [Using the library](#using-the-library): the
  consumer pastes the `[extern.*]` sections and places the sources under
  `src/deps/polyp/`.
- **GTK is required to build and run.** There is no pure-Kelp proof of the loop
  without a display; the smoke test runs a real GTK window under Xvfb.

## See also

- [Coral: the manifest](/tooling/coral#extern-user-modules-that-bind-a-native-symbol)
- [User FFI](/language/externs)
- [Functions](/language/functions#trailing-blocks-and-scoped-parameters)
- [Capabilities](/language/capabilities)
