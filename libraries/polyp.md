---
title: "`polyp`: a declarative native UI library for Kelp"
description: "Polyp is the Elm architecture with a backend-neutral core: `view` is a pure function of your state, `update` an exhaustive `when`, and the keyed diff is a `List<Patch>` a backend applies, GTK or a bare framebuffer."
isPublished: true
tags: "library, ui"
---
A declarative native UI library for Kelp. The application describes what the
screen should be for the current state; Polyp owns the loop and **patches** the
live widget tree instead of rebuilding it. Since v3 the tree, the keyed diff and
the loop live in a **backend-neutral core**, and GTK is one backend behind an
interface: a second, pure-Kelp **software backend** draws the same UI into a
framebuffer with no display server, hosted or bare metal. GTK is the desktop
backend, and a Polyp window is a GTK window.

Gated on `ui` (the display domain, [Capabilities](/language/capabilities)). Only
the GTK backend needs the grant; the core, the headless backend and the software
backend name no display symbol and need no capability.

Polyp is **not** an `fpl` folder. It ships in the compiler's own repository at
`examples/polyp/`, with `examples/polyp-v0/` as a frozen copy of the earlier
plain-constructor API and `examples/polyp-counter-v0/` its counter, because a
consumer declares its native surface in its own `coral.toml` rather than
depending on a folder (see [Using the library](#using-the-library)).

There is no published version number. **v2** added the keyed patch, `scrolled`,
`checkbox`, `progress`, `separator`, the layout options and `polyp.css`.
**v3** split the library into a core and one module per backend, and added the
display-free path; the application surface is unchanged apart from the tree's
type, which is `core.Node<M>` now that it lives in the core. The design is
[`plan/polyp-v3.md`](https://homelabone.xenoo.dev/gitea/Juniper/kelp/src/branch/main/plan/polyp-v3.md).

## The layering

```
application            view(S) -> core.Node<M>      update(mut S, M)
      |
polyp (lib.kp)         the v1/v2 surface a program imports: column { },
      |                row { }, keyed { }, widgets, class, css, run, stats
      v
core.kp  (hosted, pure Kelp: no GTK, no extern, no unsafe)
      |
      +-- gtk_backend.kp       the live GTK widget tree, real signals
      +-- headless_backend.kp  an in-memory retained tree, a scripted event
      |                        list and a text dump, for display-free tests
      +-- soft_backend.kp      a retained tree over the integer rasterizer,
                               for a framebuffer, hosted or bare metal
```

`core.kp` holds the loop, the tree and the matching. It names no GTK symbol,
calls no `extern fun` and uses no `unsafe`, so it is also the module the soft
backend reuses unchanged. A backend holds widgets and knows nothing about the
application's `Msg`: it never sees a `Node`, only the plain `Props` a patch
carries, and the events it produces carry only integers and, for a programmatic
edit, a string.

What changed between two renders is a pure function of two trees:

```kelp
pub fun diff<M>(old: &Node<M>, new: &Node<M>).R: List<Patch>
pub fun diff_into<M>(old: &Node<M>, new: &Node<M>, out: mut List<Patch>)

pub enum Patch {
    Create(val path: Path, val kind: i32, val props: Props)
    Update(val path: Path, val props: Props)
    Remove(val path: Path)
    Move(val path: Path, val to_index: i32)
}
```

`path` is a `Path`, a list of `Seg` from the root; the last segment is `Index(i)`
for an unkeyed child and `Keyed(i, key)` for a keyed one. `kind` is one of the
`KIND_*` integers the backend maps to its own widget, and `props` is plain data:
`text`, `size`, `bold`, `label`, `checked`, `permille`, `spacing`, `height`,
`margin`, `expand`, `align` and `classes`. `diff_into` is `diff` with a
caller-owned list, so a driver can reuse one buffer across frames. The backend
interface itself:

```kelp
pub trait Backend {
    fun mut Self.apply(patches: &List<Patch>)          // one line: core.apply_patches
    fun mut Self.make(path: &Path, at: i32, kind: i32, props: &Props)
    fun mut Self.patch_widget(path: &Path, props: &Props)
    fun mut Self.drop_widget(path: &Path)
    fun mut Self.place_widget(path: &Path, to_index: i32)
    fun mut Self.pump()
    fun mut Self.poll().R: Event
    fun Self.path_of(id: i32).R: option.Option<Path>
    fun Self.focus().R: option.Option<i32>
    fun mut Self.set_focus(id: i32)
    fun mut Self.set_entry_text(id: i32, text: &str)
    fun Self.entry_text(id: i32).R: String
    fun Self.entry_ids().R: List<i32>
    fun Self.entries_built().R: i32
    fun Self.stats().R: Stats
}
```

`apply` is implemented once per backend as a one-line delegation to
`core.apply_patches`, so the walk that turns a path into a widget call, and the
id rule, live in one place and cannot drift between backends. `run<B: Backend,
S, M>(backend, init, view, update) -> S` owns the state, the path-to-id table,
the focus check and the counters, and it names no backend.

The **headless** backend (`examples/polyp/headless_backend.kp`) applies the same
patches to an in-memory tree and prints a text dump; it needs no display, so a
whole program can run in a test. `examples/polyp-core-test/` asserts the pure
diff (identical trees produce nothing, a text change one `Update`, a keyed
reorder `Move`s and no create or remove, and a duplicate key panics naming it)
and runs the todo program on the headless backend with the same counters the GTK
smoke run prints. The **soft** backend is
[Polyp on a framebuffer](/libraries/polyp-soft), and its bare-metal proof is
[Polyp on bare metal](/libraries/polyp-freestanding).

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
  whose entire environment is one small integer. It posts that integer to the
  backend's event queue (the GTK backend's is the fixed-size C queue in
  `include/polyp_queue.h`; the headless and soft backends queue it in Kelp), and
  the loop, which **does** own the state, reads it back, resolves the id to the
  node it names, takes that node's `Msg` from a fresh `view`, calls `update`,
  re-runs `view` and patches the widgets.

GTK callbacks and the loop run on the same thread (`g_signal_connect` handlers
run inside `g_main_context_iteration`, which the loop calls), so the queue needs
no lock.

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
`src/`, so a Polyp consumer does three things by hand:

1. **Put the sources where `impl` can reach them.** The convention Coral fetches
   a dependency into is `src/deps/<name>/`, and a path ending in `/lib` under
   `deps/` is named after its directory, so `impl "deps/polyp/lib"` is reached as
   `polyp.*`. Copy `examples/polyp/` to `src/deps/polyp/`, or link it, which is
   what `examples/polyp-counter/` and `examples/polyp-todo/` do:

   ```sh
   mkdir -p src/deps
   ln -s ../../../polyp src/deps/polyp
   ```

   The library's own `impl "deps/polyp/core"`, `"deps/polyp/gtk_backend"` and
   `"deps/polyp/queue"` lines already spell that location, so the copy has to
   land exactly there.

2. **Paste the `[extern.*]` sections into your `coral.toml`.** The native
   symbols, the headers and the `pkg-config` package live in the consumer's
   manifest, because a library has none of its own. The section ids are the
   `impl` paths the library uses. This is the list
   `examples/polyp-todo/coral.toml` carries, and it is the list the library needs
   as of v3:

   ```toml
   [extern."deps/polyp/gtk"]
   domain = "ui"
   library = "gtk-4"
   header = "gtk/gtk.h"
   pkg_config = "gtk4"
   symbols = ["gtk_init", "gtk_window_new", "gtk_window_set_title", "gtk_window_set_default_size", "gtk_window_set_child", "gtk_window_present", "gtk_window_get_focus", "gtk_window_set_focus", "gtk_box_new", "gtk_box_append", "gtk_box_remove", "gtk_box_insert_child_after", "gtk_box_reorder_child_after", "gtk_box_set_spacing", "gtk_label_new", "gtk_label_set_markup", "gtk_widget_set_size_request", "gtk_entry_new", "gtk_editable_set_text", "gtk_editable_get_text", "gtk_button_new_with_label", "gtk_button_set_label", "gtk_check_button_new_with_label", "gtk_check_button_set_label", "gtk_check_button_set_active", "gtk_progress_bar_new", "gtk_progress_bar_set_fraction", "gtk_separator_new", "gtk_scrolled_window_new", "gtk_scrolled_window_set_child", "gtk_widget_set_margin_start", "gtk_widget_set_margin_end", "gtk_widget_set_margin_top", "gtk_widget_set_margin_bottom", "gtk_widget_set_hexpand", "gtk_widget_set_vexpand", "gtk_widget_set_halign", "gtk_widget_set_valign", "gtk_widget_add_css_class", "gtk_widget_remove_css_class", "gtk_css_provider_new", "gtk_css_provider_load_from_string", "gdk_display_get_default", "gtk_style_context_add_provider_for_display", "gtk_widget_is_ancestor", "g_object_unref", "g_main_context_iteration", "g_timeout_add_full", "connect=g_signal_connect_data", "connect_ret=g_signal_connect_data", "g_signal_handler_block", "g_signal_handler_unblock"]

   [extern."deps/polyp/queue"]
   domain = "ui"
   library = "c"
   header = "polyp_queue.h"
   include_dirs = ["src/deps/polyp/include"]
   symbols = ["polyp_post", "polyp_poll", "polyp_post_edit", "polyp_poll_edit", "polyp_poll_edit_text", "polyp_post_focus", "polyp_poll_focus"]
   ```

   `header` is one key per section, which is why the queue is its own module:
   `polyp_queue.h` is a header of the library and `gtk/gtk.h` is GTK's, and a
   section names one. See
   [Coral: the manifest](/tooling/coral#extern-user-modules-that-bind-a-native-symbol).

3. **Grant the domain.** Every GTK and queue call is in the `ui` domain
   (`plan/ffi-display-domain.md`; the only accepted grant is the wildcard), so
   the consumer's import of the library delegates it:

   ```kelp
   impl "deps/polyp/lib" caps(ui = ["*"])
   ```

   The library holds `ui` and the application does not need to: `main` never names
   a GTK call.

## API

```kelp
pub enum Key {
    None
    Str(val s: String)
    Int(val n: i64)
}

pub enum Align {
    Fill
    Start
    Center
    End
}

pub datac Opts(var margin: i32, var expand: bool, var align: i32, var classes: List<String>)
pub datac Child<M>(val key: Key, val node: Node<M>, val opts: Opts)

// The tree type lives in `core.kp` now, so a view is written
// `fun (S).R: core.Node<M>` and the example imports `deps/polyp/core` too.
pub enum Node<M> {
    Column(val children: List<Child<M>>, val spacing: i32)
    Row(val children: List<Child<M>>, val spacing: i32)
    Text(val text: String, val size: i32, val bold: bool)
    Spacer(val height: i32)
    Entry(val text: String, val on_change: fun (String).R: M)
    Button(val label: String, val on_click: M)
    Checkbox(val label: String, val checked: bool, val on_toggle: M)
    Progress(val permille: i32)
    Separator
    Scrolled(val children: List<Child<M>>, val spacing: i32)
}

// The builder. `column`/`row` take the trailing block; the methods on
// `Children` are the leaf and nested constructors the block calls.
pub fun column<M>(block: scoped fun(mut Children<M>)).R: Node<M>
pub fun row<M>(block: scoped fun(mut Children<M>)).R: Node<M>
fun mut Children<M>.text(t: str)
fun mut Children<M>.text_styled(t: str, size: i32, bold: bool)
fun mut Children<M>.spacer(height: i32)
fun mut Children<M>.button(label: str, on_click: move M)
fun mut Children<M>.entry(value: str, on_change: fun (String).R: M)
fun mut Children<M>.checkbox(label: str, checked: bool, on_toggle: move M)
fun mut Children<M>.progress(permille: i32)
fun mut Children<M>.separator()
fun mut Children<M>.column(block: scoped fun(mut Children<M>))
fun mut Children<M>.row(block: scoped fun(mut Children<M>))
fun mut Children<M>.scrolled(block: scoped fun(mut Children<M>))
fun mut Children<M>.keyed(key: str, block: scoped fun(mut Children<M>))
fun mut Children<M>.keyed_col(key: str, block: scoped fun(mut Children<M>))
fun mut Children<M>.keyed_int(key: i64, block: scoped fun(mut Children<M>))
fun mut Children<M>.keyed_int_col(key: i64, block: scoped fun(mut Children<M>))
fun mut Children<M>.with_key(key: str)
fun mut Children<M>.with_key_int(key: i64)
fun mut Children<M>.spacing(n: i32)
fun mut Children<M>.margin(n: i32)
fun mut Children<M>.expand()
fun mut Children<M>.align(a: Align)
fun mut Children<M>.class(name: str)

// The v0 plain constructors. `text` and `button` keep their names because
// their builder twins are methods (a separate namespace); `column`/`row` are
// the builder's free functions, and Kelp has no overloading, so the plain pair
// carries a `plain_` prefix.
pub fun plain_column<M>(children: move List<Node<M>>).R: Node<M>
pub fun plain_row<M>(children: move List<Node<M>>).R: Node<M>
pub fun text<M>(text: move String).R: Node<M>
pub fun button<M>(label: move String, on_click: move M).R: Node<M>

pub fun run<S, M>(title: str, width: i32, height: i32, init: move S,
                  view: fun(S).R: Node<M>, update: fun(mut S, M)).R: S

pub datac Stats(val created: i32, val updated: i32, val removed: i32, val live: i32)
pub fun stats().R: Stats
pub fun focus_present().R: bool
pub fun focus_survived().R: bool
pub fun entries_built().R: i32
pub fun entry_text(index: i32).R: String
pub fun css(text: str)
pub const QUIT_ID: i32
pub fun schedule_post(delay_ms: u32, id: i32)
pub fun schedule_quit(delay_ms: u32)
pub fun schedule_set_entry(delay_ms: u32, index: i32, new_text: str)
pub fun schedule_focus_entry(delay_ms: u32, index: i32)
```

- `run` opens one `GtkWindow` with the given title and default size, patches the
  first tree into it, and iterates the default GLib main context until a quit is
  posted. It **returns the final state** (`init` is moved in, so returning it is
  how the caller reads what the run left behind).
- `fun(S)` in `view`'s type is "view borrows the state": a parameter of an owned
  type is a shared borrow, so an application writes
  `fun view(state: Counter).R: Node<Msg>` with no `&` anywhere. `update` is
  written `fun update(state: mut Counter, msg: Msg)`.
- `text` is a label. `text_styled(text, size, bold)` sets Pango markup after
  escaping the text, so a `&` or `<` is shown, not parsed; `size` is points and
  `0` means GTK's default. `spacer(height)` reserves vertical pixels.
- `entry(value, on_change)` is a text field. `value` seeds the text the first
  time the widget is built; a patch rewrites it only when the model's text
  differs **and** the entry is not where the focus is, so a user's cursor and
  selection are not fought. `on_change` is a plain `fun(String).R: M` (called
  with a borrowed `String`) that turns the live text into the application's
  `Msg`.
- `checkbox(label, checked, on_toggle)` posts `on_toggle` on `toggled`; the
  application reads the new state from its own model, exactly as a button does.
  `progress(permille)` is a `GtkProgressBar`, with the permille in `0..=1000`;
  the core carries the progress as an integer because a float comparison is a
  soft-float call on a bare-metal target (see
  [Polyp on bare metal](/libraries/polyp-freestanding)). `separator()` is a
  horizontal rule.
- `scrolled(block)` puts the block's children in a `GtkScrolledWindow`, laid out
  in a vertical box inside it. The window is patched in place, so the scroll
  offset survives.
- **Keys.** `keyed(key, block)` is a keyed **row**: the block's children become
  one `Row` child with the given key, which is the shape a list of rows wants.
  `keyed_col` is the same for a column, `keyed_int`/`keyed_int_col` are the
  integer-keyed twins, and `with_key`/`with_key_int` give the next pushed node a
  key of any kind. One container uses one key type; the keys must be unique among
  its children, and a duplicate panics naming it
  (`polyp: duplicate key 'task-7' among the children of one container`). A key is
  usually the item's own id, never its index, so a row stays the same row after a
  reorder.
- **Layout and style options.** `spacing(n)` is the spacing of the box being
  built. `margin(n)`, `expand()`, `align(a)` and `class(name)` are options of the
  **next pushed child**, whatever its kind: `k.expand() k.column { ... }` expands
  the column, and `k.class("row") k.keyed(...)` classes the row. `margin < 0` and
  an unset `align` leave GTK's own default alone.
- `css(text)` loads a `GtkCssProvider` on the default display at
  `GTK_STYLE_PROVIDER_PRIORITY_APPLICATION`, so ordinary CSS applies to every
  widget that carries a matching class.
- **An id is an interactive widget's.** The core and the backend derive the same
  integer from the same rule: the nth `Entry`, `Button` or `Checkbox` a run
  creates is id n, ids only grow and are never reused, and a handler captures its
  id forever. `QUIT_ID` is `-2`, because `polyp_poll` answers `-1` for an empty
  queue. A surviving widget keeps its id; a removed one's id resolves to no path,
  so a queued id whose widget is gone is dropped instead of reaching `update`.
  An application should still carry a `Msg` rather than post a raw id.
- `schedule_post` / `schedule_quit` post an id after a delay;
  `schedule_set_entry` asks the loop to set an entry's text after a delay, which
  fires that entry's real `changed` signal; `schedule_focus_entry` sets the
  window's focus. They exist for programs that have to run with no user (the
  smoke tests are), and they are the only reason `g_timeout_add_full` is bound.
- `stats()` is a diagnostic: how many widgets the run ever built, how many
  matched widgets it patched in place, how many it destroyed, and how many are
  alive (`created - removed`). `focus_present()` says whether any patch found a
  focus widget, `focus_survived()` whether every patch kept the one it found,
  `entries_built()` how many `Entry` widgets the process built, and
  `entry_text(index)` reads the index-th entry's text as it was when `run`
  returned. A run that patches keeps `created` flat across state changes; a
  rebuild-everything implementation does not.

`Node<M>` is a generic enum that recurses through `List<Child<M>>`, which the
compiler accepts as written: a `List` element lives in the list's own heap
buffer, so the type has a finite size and no `Box` is needed. `Node<M>` itself
carries application data (`M`, `String`) and is moved apart as it is built, so
nothing keeps it after the widgets exist.

## The counter

`examples/polyp-counter/` is the minimal program, complete and buildable, and
its `src/deps/polyp` link points at `examples/polyp/`:

```kelp
impl "deps/polyp/core"
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

fun view(s: Counter).R: core.Node<Msg> {
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
var kids: List<core.Node<Msg>> = List.empty()
kids.push(polyp.text(String.from_str("hi")))
kids.push(polyp.button(String.from_str("+1"), Msg.Inc))
return polyp.plain_column(kids)
```

## The keyed todo list

`examples/polyp-todo/` is the keyed-list program: an entry and an add button at the top,
a scrolled list of keyed rows, and a progress bar of done over total. Each row is
one `keyed` child whose key is the item's own id, never its index, so a row is
the same row after a move or a removal above it. Its `view` is:

```kelp
fun view(s: Model).R: core.Node<Msg> {
    return polyp.column { k ->
        k.spacing(8)
        k.margin(12)
        k.class("todo-app")
        k.row { r ->
            r.spacing(6)
            r.expand()
            r.entry(s.draft.as_str(), changed)
            r.button("add", Msg.Add)
        }
        k.separator()
        k.expand()
        k.scrolled { sc ->
            sc.spacing(4)
            sc.margin(4)
            var i: usize = 0
            while i < s.items.len() {
                val item = s.items.get(i)
                val key = fmt.int(item.id.to_i64())
                if item.done {
                    sc.class("todo-done")
                } else {
                    sc.class("todo-pending")
                }
                sc.keyed(key.as_str()) { r ->
                    r.spacing(6)
                    r.checkbox("", item.done, Msg.Toggle(id = item.id))
                    r.expand()
                    r.text(item.title.as_str())
                    r.button("^", Msg.MoveUp(id = item.id))
                    r.button("x", Msg.Remove(id = item.id))
                }
                i += 1
            }
        }
        k.progress(permille(s))
    }
}
```

The `Msg` names an item by id too, so the same identity flows from the key into
`update`:

```kelp
enum Msg {
    Changed(val text: String)
    Add
    Toggle(val id: i32)
    MoveUp(val id: i32)
    Remove(val id: i32)
}
```

Ticking a row's checkbox patches its `checked` state; `MoveUp` reorders the
model list and the loop reorders the live row instead of rebuilding it;
`Remove` takes one row's widgets away and leaves the others untouched. The
class on each row follows `done`, and the app installs
`.todo-app`, `.todo-done` and `.todo-pending` through `polyp.css`.

## Headless testing with Xvfb

Each example is proved by its `smoke.sh`, which re-enters `dev-gtk.nix` (the
shell beside the compiler repository; override with `POLYP_DEV_GTK`), compiles
the example with the **default** (`llvm`) backend, and runs the binary under
`xvfb-run -a` with `GSK_RENDERER=cairo GDK_BACKEND=x11` and `POLYP_SMOKE=1`. In
that mode the program schedules its own input and prints a deterministic summary.
A crash, a hang (`timeout 60`) or anything else on stdout fails the script. GTK's
own Xvfb warnings go to stderr and are not the program's answer.

The counter **must print exactly** `1\ntyped\n1`: the count after the scheduled
`+1`, `+1`, `-1`, the text the entry's constructor produced, and one entry widget
built across all the patches.

The todo smoke parses the run line by line and asserts the library's counters,
not guesses:

- the final model is two items, `alpha` not done and `beta` done;
- six creation **marks** (`polyp.stats().created` recorded after each action):
  each add creates its row's five widgets, so the first four marks grow, while
  ticking, moving and removing create nothing and leave the last three equal. A
  rebuild-everything implementation keeps creating widgets and fails this
  equality;
- `created` equals the last mark, `removed == 5` (one five-widget row), and
  `live == created - removed`;
- `updated > 0`, so the run really patched widgets in place;
- `focus_present` and `focus_survived` are both true (the entry held the focus
  across every patch);
- `entries_built == 1` and `entry_text(0) == "gamma"`, so one entry widget was
  ever built and it still shows the last text typed into it even though the model
  cleared its draft;
- a final `end` marker, so the empty draft line is not lost to a shell that
  strips trailing newlines.

**Both** smoke runs build the todo again with `KELPC_ORACLE=c` and check the same
output, so the C backend and the default one behave identically.

```sh
examples/polyp-counter/smoke.sh
examples/polyp-counter-v0/smoke.sh
examples/polyp-todo/smoke.sh
```

The loop is also tested with no display at all: `examples/polyp-core-test/` runs
the same todo program on the headless backend with no GTK and no Xvfb, and
[Polyp on a framebuffer](/libraries/polyp-soft) covers the software backend's
layout, input and damage tests. Those run in the plain development shell on both
compiler backends.

## Reconciliation, exactly

Every state change calls `view` for the whole tree, but the loop keeps the live
widgets and **patches** them. For each container (and for the window's single
child):

- A child is matched to its previous self **by key** when it has one, and by
  **position and widget kind** otherwise. Kinds are part of the match, so a
  `Button` is never patched into a `Text`.
- A matched widget is **updated in place**: label markup, button label, checkbox
  label and active state, entry text (only when it differs and the entry does not
  hold the focus), progress permille, spacer height, box spacing, margins,
  expand, alignment and CSS classes. It is the same GTK object, so its focus,
  text selection and scroll offset survive by construction. Focus is checked: the
  loop records the widget focused before a patch and sets a flag if a later
  patch leaves it unfocused.
- A child the new tree does not match is created and inserted at its index
  (`gtk_box_insert_child_after`). A keyed child that only moved is reordered
  (`gtk_box_reorder_child_after`), not rebuilt. When the matched sequence is
  still in order the survivors are not touched at all, which is what keeps a
  removal from disturbing the focus.
- A child the new tree does not name is removed from its container and its id
  resolves to no path, so a queued id for it is dropped; its subtree is counted
  as destroyed.
- A programmatic write to a checkbox or an entry blocks that widget's signal
  first (`g_signal_handler_block`), so setting the widget's state to match the
  model cannot post the `Msg` that state came from.

The patch list is ordered, and the order is what makes each path valid at the
moment its patch is applied. For each container, depth first: `Update` for every
matched child in new order, each followed by that child's own subtree; `Remove`
for unmatched old children in descending old index (so a lower index is still the
index it was); `Create` for unmatched new children in new order; and `Move` for
matched children whose position changed, in increasing new index, only when the
matched sequence is not already increasing. One v2 rule was tightened: a new
child without a key takes the old child at the same index only when it is unused,
of the same kind, **and unkeyed too**, because letting it take a keyed old child
would change the node's identity from a key to a position and so cannot be
expressed as a stable path.

The old v1 rule (the `i`-th `Entry` reuses the `i`-th entry widget) is gone; the
patch subsumes it, and it works for any widget, not only an entry. The counter's
smoke run still prints one entry built across all its renders, now because the
entry is a matched child and not because an ordinal rule reused it.

## Known limits

- **No lazy or virtualized lists.** Every child in the model is a live widget on
  every backend; a list of 10,000 rows builds 10,000 widgets. A keyed patch makes
  the updates cheap, not the first build.
- **No animation and no transitions.** A patch sets a property in one step;
  there is no interpolator and no per-frame hook. The soft backend's frame
  deadline bounds one tick, it does not add animation.
- **No exclusive captures.** A builder block may read the borrowed state, but
  `state.count += 1` inside a block is still a language error
  (`plan/scoped-blocks.md`); a mutation goes through a `Msg`.
- **No library manifest.** See [Using the library](#using-the-library): the
  consumer pastes the `[extern.*]` sections and places the sources under
  `src/deps/polyp/`. This is the one thing that makes Polyp awkward to consume,
  and it is the same for every Kelp library.
- **An id still leans on creation order.** An interactive widget's id comes from
  counting interactive `make` calls, so an application that posts a raw id
  (rather than carrying a `Msg`) relies on the order widgets are created in; the
  smoke runs do, deliberately, because they have no user to click anything.
- **The soft backend's limits are its own.** No vector text or shaping, no bold
  face, no images, no accessibility, no GPU, no stylesheet parser; the full list
  is on
  [Polyp on a framebuffer](/libraries/polyp-soft#what-the-display-free-path-does-not-do).
- **A display is required to *draw* with GTK.** The GTK smoke tests run a real
  window under Xvfb, and the focus tests read the toplevel's focus widget rather
  than `gtk_widget_has_focus`, which needs a window manager to hand over global
  input focus. The loop itself needs no display: the headless backend runs the
  whole program in a test, and the soft backend runs it with no display at all.
- **Theming has two hooks.** `polyp.css` is GTK's; the soft backend's equivalent
  is the `Theme` `datac` and its `class_style` table, not a stylesheet parser or
  a selector engine.

## See also

- [Polyp on a framebuffer](/libraries/polyp-soft): the software rasterizer, the
  soft backend, the five-function `Platform` contract, the work budgets and the
  benchmark
- [Polyp on bare metal](/libraries/polyp-freestanding): the two QEMU kernels and
  the framebuffer equivalence proof
- [Coral: the manifest](/tooling/coral#extern-user-modules-that-bind-a-native-symbol)
- [User FFI](/language/externs)
- [Functions](/language/functions#trailing-blocks-and-scoped-parameters)
- [Capabilities](/language/capabilities)
- [`plan/polyp-v3.md`](https://homelabone.xenoo.dev/gitea/Juniper/kelp/src/branch/main/plan/polyp-v3.md):
  the design record
