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

Since v5, Polyp is its own repository: [`lilly/polyp`](https://homelabone.xenoo.dev/gittea/Lilly/polyp).
The Kelp repository keeps consumer copies in `kelpc/tests/fixtures/examples/polyp*/`. The frozen copies
`polyp-v0` and `polyp-counter-v0`, which earlier revisions of this page named, are no longer in the tree. A consumer declares Polyp in its own
`coral.toml` (see [Using the library](#using-the-library) and [Polyp v5](#polyp-v5)).

There is no published version number. **v2** added the keyed patch, `scrolled`,
`checkbox`, `progress`, `separator`, the layout options and `polyp.css`.
**v3** split the library into a core and one module per backend, and added the
display-free path; the application surface is unchanged apart from the tree's
type, which is `core.Node<M>` now that it lives in the core. The design is
[`design/polyp-v3`](/design/polyp-v3).
**v4** adds timers and integer animation, UTF-8 text in the soft backend, an
on-demand accessibility tree, and memoised pure subtrees. Its implementation
record is [`libraries/polyp.md`](/libraries/polyp).

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
pub fun diff<M>(old: &Node<M>, new: &Node<M>) => List<Patch>
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
    fun mut Self.poll() => Event
    fun Self.path_of(id: i32) => option.Option<Path>
    fun Self.focus() => option.Option<i32>
    fun mut Self.set_focus(id: i32)
    fun mut Self.set_entry_text(id: i32, text: &str)
    fun Self.entry_text(id: i32) => String
    fun Self.entry_ids() => List<i32>
    fun Self.entries_built() => i32
    fun Self.stats() => Stats
    fun Self.scroll_at(path: &Path) => i32
    fun mut Self.set_scroll(path: &Path, offset: i32)
    fun mut Self.take_list_moved() => bool
}
```

`apply` is implemented once per backend as a one-line delegation to
`core.apply_patches`, so the walk that turns a path into a widget call, and the
id rule, live in one place and cannot drift between backends. `run<B: Backend,
S, M>(backend, init, view, update) -> S` owns the state, the path-to-id table,
the focus check and the counters, and it names no backend.

The **headless** backend (`backends/headless/headless_backend.kp`) applies the same
patches to an in-memory tree and prints a text dump; it needs no display, so a
whole program can run in a test. `kelpc/tests/fixtures/examples/polyp-core-test/` asserts the pure
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
- `view`: `fun(State) => Node<Msg>`, a pure function of the state.
- `update`: `fun(mut State, Msg)`, where the application writes one exhaustive
  `when`.

This is not a style choice. It is the one architecture Kelp's ownership rules
allow:

- A Kelp closure **owns** its captures and cannot capture a borrow
  (`syntax.md` §7.4), and Kelp has no shared-ownership type to put the
  application state behind.
- So no callback captures the state at all. A button's handler is a closure
  whose entire environment is one small integer. It posts that integer to the
  backend's event queue (the GTK backend's is a fixed-size ring written in Kelp,
  `backends/gtk/queue.kp`, as the headless and soft backends' queues are), and
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

Coral fetches Polyp. A consumer names it in `coral.toml`:

```toml
[dependencies]
polyp = "fpl/polyp"
```

`fpl/polyp` is coral's first-party catalog entry; it resolves to the Polyp repository and lands in
`src/deps/polyp/`. Coral's manifest rules are on the [Coral page](/tooling/coral).

The consumer then does two things by hand.

1. **Import the facade and grant the domain.** Every GTK and queue call is in the `ui` domain, so the
   consumer's import of the facade delegates it. The program's namespace is `polyp`:

   ```kelp
   impl "deps/polyp/backends/gtk/polyp/lib" caps(ui = ["*"])
   ```

   The facade holds `ui`, and `main` never names a GTK call.

2. **Paste the `[extern.*]` sections into `coral.toml`.** The native symbols and the `pkg-config`
   package live in the consumer's manifest. The section id is the `impl` path the library uses:
   `deps/polyp/backends/gtk/gtk` (GTK, `pkg_config = "gtk4"`). The complete block is
   in the Polyp README under "Add Polyp to a project", and is kept there so it has one source.

   The `extern fun` declarations in the binding carry the signatures. The README block
   still has a `header` key, which is accepted and not read, because kelpc compiles no
   C. The message queue is plain Kelp, so it has no section. See
   [Coral: the manifest](/tooling/coral#user-modules-that-bind-a-native-symbol-extern).

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

pub datac Opts(
    var margin: i32, var expand: bool, var align: i32, var classes: List<String>,
    var opacity: i32, var offset_x: i32, var offset_y: i32,
    var anim_main: anim.Anim, var anim_opacity: anim.Anim, var anim_ox: anim.Anim, var anim_oy: anim.Anim,
    var disabled: bool, var min_h: i32,
)
pub datac Child<M>(val key: Key, val node: Node<M>, val opts: Opts)

// The tree type lives in `core.kp` now, so a view is written
// `fun (S) => core.Node<M>` and the example imports `deps/polyp/core` too.
pub enum Node<M> {
    Column(val children: List<Child<M>>, val spacing: i32)
    Row(val children: List<Child<M>>, val spacing: i32)
    Text(val text: String, val size: i32, val bold: bool)
    Spacer(val height: i32)
    Entry(val text: String, val on_change: closure(String) => M)
    Button(val label: String, val on_click: M)
    Checkbox(val label: String, val checked: bool, val on_toggle: M)
    Progress(val permille: i32)
    Separator
    Scrolled(val children: List<Child<M>>, val spacing: i32)
    Image(val w: i32, val h: i32, val pixels: List<u32>)
    Memo(val deps: Deps, val build: fun (&Deps) => List<Child<M>>)
    VList(val count: i32, val row_h: i32, val viewport_h: i32, val deps: Deps, val build: fun (&Deps, i32) => List<Child<M>>)
    Viewport(val children: List<Child<M>>, val rows: i32, val viewport_h: i32)
}

// The builder. `column`/`row` take the trailing block; the methods on
// `Children` are the leaf and nested constructors the block calls.
pub fun column<M>(block: scoped fun(mut Children<M>)) => Node<M>
pub fun row<M>(block: scoped fun(mut Children<M>)) => Node<M>
fun mut Children<M>.text(t: str)
fun mut Children<M>.text_styled(t: str, size: i32, bold: bool)
fun mut Children<M>.spacer(height: i32)
fun mut Children<M>.button(label: str, on_click: move M)
fun mut Children<M>.entry(value: str, on_change: closure(String) => M)
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
fun mut Children<M>.image(w: i32, h: i32, pixels: List<u32>)
fun mut Children<M>.memo(key: str, deps: Deps, build: fun (&Deps) => List<Child<M>>)
fun mut Children<M>.memo_int(key: i64, deps: Deps, build: fun (&Deps) => List<Child<M>>)
fun mut Children<M>.virtual_list(count: i32, row_h: i32, viewport_h: i32, deps: Deps, build: fun (&Deps, i32) => List<Child<M>>)
fun mut Children<M>.anim(a: Anim)
fun mut Children<M>.disabled()
fun mut Children<M>.opacity(permille: i32)
fun mut Children<M>.opacity_anim(a: Anim)
fun mut Children<M>.offset(x: i32, y: i32)
fun mut Children<M>.offset_x_anim(a: Anim)
fun mut Children<M>.offset_y_anim(a: Anim)

// The v0 plain constructors. `text` and `button` keep their names because
// their builder twins are methods (a separate namespace); `column`/`row` are
// the builder's free functions, and Kelp has no overloading, so the plain pair
// carries a `plain_` prefix.
pub fun plain_column<M>(children: move List<Node<M>>) => Node<M>
pub fun plain_row<M>(children: move List<Node<M>>) => Node<M>
pub fun text<M>(text: move String) => Node<M>
pub fun button<M>(label: move String, on_click: move M) => Node<M>

pub fun run<S, M>(title: str, width: i32, height: i32, init: move S,
                  view: fun(S) => Node<M>, update: fun(mut S, M)) => S

pub datac Stats(val created: i32, val updated: i32, val removed: i32, val live: i32, val memo_hits: i32, val memo_misses: i32, val view_calls: i32)
pub fun stats() => Stats
pub fun focus_present() => bool
pub fun focus_survived() => bool
pub fun entries_built() => i32
pub fun entry_text(index: i32) => String
pub fun css(text: str)
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
  `fun view(state: Counter) => Node<Msg>` with no `&` anywhere. `update` is
  written `fun update(state: mut Counter, msg: Msg)`.
- `text` is a label. `text_styled(text, size, bold)` sets Pango markup after
  escaping the text, so a `&` or `<` is shown, not parsed; `size` is points and
  `0` means GTK's default. `spacer(height)` reserves vertical pixels.
- `entry(value, on_change)` is a text field. `value` seeds the text the first
  time the widget is built; a patch rewrites it only when the model's text
  differs **and** the entry is not where the focus is, so a user's cursor and
  selection are not fought. `on_change` is a closure, `closure(String) => M` (called
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
  id forever. The GTK backend's `QUIT_ID` is `-2` (in `backends/gtk/gtk_backend.kp`, not exported by the facade), because `polyp_poll` answers `-1` for an empty
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

The counter program (`polyp-counter`) is no longer in the Kelp tree at this revision, so the listing below
is kept for reference. Its `coral.toml` fetched Polyp with `polyp = "fpl/polyp"`, and its imports were:

```kelp project
impl "deps/polyp/core/core"
impl "deps/polyp/backends/gtk/polyp/lib" caps(ui = ["*"])
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

fun changed(text: String) => Msg = Msg.Changed(text = String.from_str(text.as_str()))

fun view(s: Counter) => core.Node<Msg> {
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

fun smoke_enabled() => bool {
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

`kelpc/tests/fixtures/examples/polyp-todo/` is the keyed-list program: an entry and an add button at the top,
a scrolled list of keyed rows, and a progress bar of done over total. Each row is
one `keyed` child whose key is the item's own id, never its index, so a row is
the same row after a move or a removal above it. Its `view` is:

```kelp
fun view(s: Model) => core.Node<Msg> {
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

**Status on current `main`.** The GTK backend compiles and links on `main`. Its
runtime has not been verified on the build host, which has no display, so the smoke
runs below have not been run on `main` for this page. The smoke scripts are the
procedure for a host with a display.

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

```sh
kelpc/tests/fixtures/examples/polyp-todo/smoke.sh
```

The loop is also tested with no display at all: `kelpc/tests/fixtures/examples/polyp-core-test/` runs
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

## Polyp v4

The core can drive timers through `subscriptions(state)`: `core.every(ms, msg)`
repeats and `core.after(ms, msg)` fires once. A platform supplies monotonic
`Tick(now_us)` events; no tick means no timer or animation advances. The soft
backend exposes `wants_frames()` for active animation or paint work and
`core.next_wake_us()` for the next timer deadline.

`anim.lerp(from, to, ms, ease)` supplies integer linear, ease-in, ease-out and
ease-in-out animation. Builder options animate progress or spacer values and can
animate opacity and paint offsets. The backend damages only the rectangles whose
animation changed; layout still uses the unanimated rectangle for hit testing.

Soft text is UTF-8 by code point rather than byte. The bundled face covers ASCII,
Latin, Greek, Cyrillic, selected punctuation, arrows and box drawing; unsupported
or malformed units draw as one replacement box and take one caret step.

`SoftBackend.a11y_tree()` constructs an accessibility tree only when requested.
It has roles, names, values, state, bounds and actions for interactive widgets;
`a11y_act` and `a11y_set_value` drive the same message path as input. The new
`k.disabled()` mutes and removes a soft-backend interactive widget from pointer,
keyboard and accessibility actions. GTK currently ignores that option.

For a large pure region, `k.memo(key, deps, build)` stores its last subtree in a
caller-owned `MemoStore`. Equal explicit dependencies keep the retained subtree;
keyed reorders preserve hits. The dependency list is the contract: omitting a
value read by `build` can leave stale pixels. `MemoStore` reports hits, misses and
view calls, but is a small linear cache with no eviction beyond removing a memo.

## Polyp v5

v5 is a layout and packaging release. The library's behaviour is the v4 behaviour, with these changes.

- **Repository.** Polyp lives in its own repository. Coral fetches it as `polyp = "fpl/polyp"`.
- **Layout.** `core/` holds the backend-neutral loop, tree, diff, diagnostics and animation maths.
  `backends/gtk/` holds the desktop backend and its facade `polyp/lib.kp`. `backends/headless/` holds the
  in-memory backend. `backends/soft/` holds the framebuffer backend and its integer rasterizer in
  `soft/`. `tools/`, `docs/plan/` and `tests/` hold the rest. The file names in the layering diagram
  above are the v3 names. Use the paths in this section.
- **Namespace.** Programs still write `polyp.column { ... }`. The facade's directory is `polyp`, and a
  module's namespace is its directory name, so the facade is reached through
  `deps/polyp/backends/gtk/polyp/lib`. The old `gtk.` form is not a Polyp namespace.
- **WebKelp.** The WebKelp compiler is in the repository under `web/`. Its own repository is archived, and
  its demo and playground sites were removed. See [WebKelp](/family/webkelp).
- **HTML output.** `kelpc` writes a Polyp app's first frame as static HTML when `coral.toml` sets
  `[build] emit = "html"` and `emit_entry`. The entry file calls `polyp.emit_html(init, view)`, and the
  normal program needs no extra grant. The emitter writes column, row, text, button and spacer as their
  HTML elements, and every other node as a `div` with a `data-kind` attribute. The page has no event
  wiring and shows the first frame only. This is in Kelp `main` and ships in 26.10.4.
  `polyp.emit_html(init, view)` is defined in the facade `backends/gtk/polyp/lib.kp` of the
  Polyp repository's `main` (commit `44dde2a`, "polyp: restore emit_html and the HTML backend"),
  so a project that fetches Polyp from that repository gets it there.
  The HTML is written as `index.html` beside the built binary.
- **Plan.** The design and open decisions are in the Polyp repository at `docs/plan/polyp-v5.md`. See
  [Polyp v5 plan](/meta/polyp-v5-plan).
- **Release notes.** Every release is listed in the [Polyp changelog](/changelog/polyp).

## Known limits

- **No lazy or virtualized lists.** Every child in the model is a live widget on
  every backend; a list of 10,000 rows builds 10,000 widgets. A keyed patch makes
  the updates cheap, not the first build.
- **A stored callback cannot write state.** A builder block may now write a
  `var` or `mut` parameter it captures
  ([Exclusive captures](/language/functions#exclusive-captures)), but only during
  the call that runs it. A widget's `on_click` outlives the call that built it, so
  it stays a `Msg` value, and a mutation still goes through the update function.
- **The `[extern.*]` sections are pasted by hand.** Coral fetches the sources (`polyp = "fpl/polyp"`),
  but the native symbol list stays in the consumer's manifest, as it does for any Kelp library with native code.
- **An id still leans on creation order.** An interactive widget's id comes from
  counting interactive `make` calls, so an application that posts a raw id
  (rather than carrying a `Msg`) relies on the order widgets are created in; the
  smoke runs do, deliberately, because they have no user to click anything.
- **The soft backend's limits are its own.** No vector text or shaping, no bold
  face, no images, no GPU, no stylesheet parser or screen-reader bridge; the full list
  is on
  [Polyp on a framebuffer](/libraries/polyp-soft#what-the-display-free-path-does-not-do).
- **GTK widgets are found by position.** The GTK backend's records hold no GTK
  handles: a `gtk.Widget` is a resource, and a `List` of resources is refused. Each
  widget is found by its position among its parent's children, which GTK keeps in
  tree order, so a lookup costs one step per sibling at each level. A child appended
  to a container lands last. A scalar handle table would need a compiler decision.
- **A display is required to *draw* with GTK.** The GTK smoke tests run a real
  window under Xvfb, and the focus tests read the toplevel's focus widget rather
  than `gtk_widget_has_focus`, which needs a window manager to hand over global
  input focus. The loop itself needs no display: the headless backend runs the
  whole program in a test, and the soft backend runs it with no display at all.
- **Theming has two hooks.** `polyp.css` is GTK's; the soft backend's equivalent
  is the `Theme` `datac` and its `class_style` table, not a stylesheet parser or
  a selector engine.

## See also

- [Polyp repository](https://homelabone.xenoo.dev/gittea/Lilly/polyp): the library source and its README
- [Polyp v5 plan](/meta/polyp-v5-plan): where the v5 plan lives
- [Polyp on a framebuffer](/libraries/polyp-soft): the software rasterizer, the
  soft backend, the five-function `Platform` contract, the work budgets and the
  benchmark
- [Polyp on bare metal](/libraries/polyp-freestanding): the two QEMU kernels and
  the framebuffer equivalence proof
- [Coral: the manifest](/tooling/coral#user-modules-that-bind-a-native-symbol-extern)
- [User FFI](/language/externs)
- [Functions](/language/functions#trailing-blocks-and-scoped-parameters)
- [Capabilities](/language/capabilities)
- [`design/polyp-v3`](/design/polyp-v3):
  the design record
