---
title: "`polyp` on a framebuffer: the soft backend, the rasterizer and a `Platform`"
description: "Polyp's display-free path: an integer software rasterizer, a soft backend that lays out and paints a retained tree, the five-function `Platform` contract an OS implements, and the per-frame work budgets and benchmark."
isPublished: true
tags: "library, ui"
---
[`polyp`](/libraries/polyp) has two halves. One is the GTK backend a desktop program
uses; the other is the **soft backend**, a pure-Kelp renderer that draws through an
integer software rasterizer into a framebuffer and links no GTK, no display server
and no libc. It is the half a custom operating system, a test harness or a
bare-metal image uses, and it is what makes a whole Polyp program testable with no
display at all. The original design is
[`plan/polyp-v3.md`](https://homelabone.xenoo.dev/gitea/Lilly/kelp/src/branch/main/plan/polyp-v3.md),
stages 2, 3 and 5; [`libraries/polyp.md`](/libraries/polyp)
adds clocks, animation, UTF-8, accessibility and memoisation.

The layering, from the application down:

```
application        view(S) -> core.Node<M>      update(mut S, M)
      |
polyp lib.kp       the surface a program imports: column { }, widgets, run, stats
      |
core.kp            the tree, the keyed diff, Patch, the Backend trait, the loop
      |
soft_backend.kp    a retained widget tree, measure/arrange layout, damage-only
      |            painting, input, the Theme, the class hook
soft/              the integer rasterizer: fb, draw, font, damage, debug
      |
soft/platform.kp   trait Platform: present / now_ms / now_us / poll_event /
      |            framebuffer - five functions an OS implements
platform           HeadlessPlatform, PpmPlatform, or a bare-metal FbPlatform
```

`core.kp`, the `Backend` trait and the `Patch` data are on
[the main Polyp page](/libraries/polyp). This page is the display-free half:
the rasterizer, the soft backend, the `Platform` contract, and stage 5's latency
model and benchmark. The bare-metal proof that the whole stack runs with no libc
is on [Polyp on bare metal](/libraries/polyp-freestanding).

## The software rasterizer

`backends/soft/soft/` is a self-contained, integer-only rasterizer. Its hard
constraints are fixed before its API:

- **Integer only.** No `f32` and no `f64` anywhere, so a riscv64 target with no
  FPU needs no soft-float libcall.
- **No libc and no OS call.** The only external facts are a pixel pointer and a
  stride the platform hands over.
- **No heap allocation in any drawing function.** Scratch is the caller's, a
  fixed `static` or a stack array.
- Only the modules that touch a raw pixel carry `unsafe`.

| Module | What it holds | `unsafe` |
| --- | --- | --- |
| `backends/soft/soft/fb.kp` | `Fb(pixels, width, height, stride_px)`, `Rect`, the pixel store/load, `checksum`, `checksum_rgb` | yes |
| `backends/soft/soft/draw.kp` | `ClipStack` (fixed depth 8) and every primitive: `fill_rect`, `stroke_rect`, `fill_round_rect`/`stroke_round_rect`, `hline`/`vline`, `line`, `blend_pixel`/`blend_over`, `blit_mask8` | yes |
| `backends/soft/soft/font.kp` | a hand-drawn 5x7 face for printable ASCII 32..126, `text_width`/`text_height`, `draw_text` at scale 1..4 | no |
| `backends/soft/soft/damage.kp` | `Damage`, at most 16 dirty rectangles, with `add`/`clear`/`count`/`at`/`bounds` | no |
| `backends/soft/soft/debug.kp` | `dump_ppm`, hosted only | yes |

A consumer lists only the three modules that dereference a pixel in its `[unsafe]
modules`:

```toml
[unsafe]
modules = ["deps/polyp/backends/soft/soft/fb", "deps/polyp/backends/soft/soft/draw", "deps/polyp/backends/soft/soft/debug"]
```

`font` and `damage` do all their geometry in integers over `Rect`/`Fb` values and
never dereference anything, so they need no audit entry. `debug.kp` is a separate
file so a freestanding project that does not import it never compiles `std/fs`.

A pixel is one `u32`, `0xAARRGGBB`, and `stride_px` is in **pixels**, not bytes:
the byte offset of `(x, y)` is `pixels + (y * stride_px + x) * 4`. Every primitive
takes `(fb, clip, ...)`, clips to `clip.top() ∩ fb.bounds()` before it touches a
pixel, and returns the number of pixels it wrote, so a frame's cost can be
asserted. The blend is exact source-over per channel in `u64`; `a == 255` returns
the source exactly and `a == 0` the destination exactly. `blit_mask8` takes a
`w * h` coverage mask and is the glyph path; a byte `0` touches nothing.

`checksum(fb)` is FNV-1a 64 over the pixels row by row, feeding each pixel's four
bytes little-endian by masking the `u32` (so it is endian-independent), and it
hashes the alpha byte. `checksum_rgb(fb)` is the same over blue, green and red
with a constant `0xFF` where alpha goes, because the renderer writes glyph
coverage into a text pixel's alpha; that is the checksum a screen can match.

`draw_text` advances the pen by `6 * scale` per UTF-8 unit and returns the pixels
written. Malformed runs and unsupported code points each occupy one replacement
box. The embedded font has one weight: a `bold` flag is carried and ignored.

## The soft backend

`backends/soft/soft_backend.kp` is the `core.Backend` implementation over the
rasterizer. It keeps the same retained widget tree the headless backend keeps, so
interactive ids, counters, focus and entry text cannot drift between them, and it
adds layout, painting and input:

- **Layout** is two passes, `measure` and `arrange`, in `i32`/`i64` only. A patch
  marks only the node it wrote `dirty`; `measure` recomputes a node only when its
  own flag is set or a child reported a changed size, and `arrange` runs only when
  the root's size changed, the window was resized, a `Move` reordered children, or
  the tree was never laid out. A text change whose new string has the same pixel
  width therefore re-measures one node and re-arranges none.
- **Painting** walks the tree once per damaged rectangle, clipped to it, and
  returns the rectangles it painted. An idle frame has no damage, so it walks
  nothing and calls nothing. When `arrange` moves a node, both its old and its new
  rectangle are damaged.
- **Style** is one `Theme` `datac` (colours and metrics) a platform can replace,
  plus a small `class_style` override table (`bg`, `fg`, `border`, `radius`,
  `pad`) for the shipped class names `todo-app`, `todo-done` and `todo-pending`. A
  class on a container reaches the text inside it.
- **Input** is the six-variant `Event` a platform decodes its windowing system
  into. The backend hit-tests front to back, tracks hover and pressed state, moves
  focus with Tab and Shift-Tab, activates a button on a press and release on the
  same widget, edits a focused entry with a visible byte caret, toggles a checkbox
  with Space, and scrolls the `Scrolled` under the wheel. Every handler that
  changes a pixel adds damage; one that does not adds none.

A `SoftBackend` also exposes the counters stage 5 pins: `frame_alloc_count`,
`frame_alloc_bytes`, `arena_high_water`, `measure_count`, `arrange_count`,
`pixels_written`, `last_painted` and `damage_count`.

## The `Platform` contract

The whole interface between the backend and an operating system is `trait
Platform` in `backends/soft/soft/platform.kp`: **five functions** and the
framebuffer the platform owns. `PLATFORM.md` is the plain-terms
version.

```kelp
pub trait Platform {
    fun mut Self.present(fb: fb.Fb, dirty: &damage.Damage)
    fun Self.now_ms() => u64
    fun mut Self.now_us() => u64
    fun mut Self.poll_event() => option.Option<event.Event>
    fun Self.framebuffer() => fb.Fb
}
```

| Function | What it must do |
| --- | --- |
| `framebuffer() -> Fb` | Return the surface the platform owns, valid for the frame. The backend reads the size every frame and re-lays-out when it changes. `stride_px` must be at least `width`; a padded pitch sets it to the pitch, a tightly packed buffer sets `stride_px == width`. The backend writes only inside `width x height`. |
| `present(fb, dirty) -> ()` | Show the frame. Called at the end of a frame **only when at least one pixel changed**, and never with an empty list. `dirty` is the exact list of rectangles the backend painted, in no particular order and with overlaps already merged; a platform may copy just those, present the whole surface and ignore the list, or record it for a test. |
| `now_ms() -> u64` | A monotonic clock in milliseconds. The backend uses it only to pace scripted input in `HeadlessPlatform`; a real platform may return 0 forever. |
| `now_us() -> u64` | A monotonic clock in microseconds, added for the frame deadline. A platform with only a millisecond clock returns `now_ms() * 1000` and gets millisecond-granular deadlines. The method is `mut` because a test platform's clock may advance as paint work is done. |
| `poll_event() -> Option<Event>` | The next pending input event, oldest first, or `None` when the queue is empty. The backend drains it until `None`, so returning one event per call is the whole contract. **It must not block.** |

`Event` is the six-variant enum in `backends/soft/soft/event.kp`:

```kelp
enum Event {
    PointerMove(x, y)
    PointerDown(x, y, button)
    PointerUp(x, y, button)
    Scroll(dx, dy)
    Key(code, mods)
    Char(codepoint)
}
```

`HeadlessPlatform` (`backends/soft/soft/headless_platform.kp`) is a complete implementation in
about a hundred lines: it allocates its buffer with `Ptr.alloc<u32>`, records the
presented rectangles and a checksum after each `present`, and plays a scripted
`(time_ms, Event)` list as `now_ms` advances. `PpmPlatform`
(`backends/soft/soft/ppm_platform.kp`) is the same plus a PPM dump to
`<POLYP_DUMP_DIR>/frame_<n>.ppm` on every present; with the variable unset it is a
headless platform. A bare-metal project writes one `FbPlatform` on top of a
static or memory-mapped surface; see
[Polyp on bare metal](/libraries/polyp-freestanding).

Everything else the platform must know is short: the platform owns the
framebuffer and keeps it valid; the backend allocates only when a patch creates a
widget; the application state is the caller's; and `frame` is synchronous and
non-blocking, so a tick with no call is a tick that did not repaint.

## The tick

An OS calls one function per tick:

```kelp
pub fun frame<P: platform.Platform, S, M>(
    backend: mut SoftBackend,
    platform: mut P,
    tree: move core.Node<M>,
    state: mut S,
    view: fun (S) => core.Node<M>,
    update: fun (mut S, M),
) => core.Tick<M>
```

It takes the platform's framebuffer, resizes the backend's layout to it, lays out,
drains every pending platform event into the backend, runs one
`core.frame_step_into` (which pumps one scripted `core.Event` and runs
`update`/`view`/`diff`/`apply` for every message), lays out again for the patches,
paints the accumulated damage, and calls `present` if anything changed. It returns
`core.Tick` (`Idle`/`Changed`/`Quit`, each carrying the new tree). A driver is a
loop that reads the tick and clears `running` on `Quit`.

### The frame deadline

`frame_budgeted(backend, platform, tree, state, view, update, budget_us)` is
`frame` with a deadline. It reads the platform's microsecond clock at the start
and after each damage rectangle, and returns `Frame.Deferred(tick)` with the
remaining rectangles still in the damage list once the elapsed time passes
`budget_us`. `Frame.Done(tick)` means the frame finished. A rectangle is painted
whole or not at all, so a deferred frame presents whole rectangles and the next
call paints the rest; nothing is half-painted and the state does not advance
twice, because `frame_step` already ran. `budget_us = 0` means no deadline, which
is what `frame` passes, so every existing caller is unchanged.

An operating system integrates it with its tick. A 60 Hz display passes
`budget_us = 16000`; a 144 Hz display about `6900`. When the call returns
`Deferred`, call again with the same tree and state from the tick until it returns
`Done`.

## The latency model

"Without lag" is a claim about bounded, small work per frame, so stage 5 makes the
per-frame cost explicit. `frame_budgeted` is the whole cost, in order:

1. `platform.framebuffer()`, `backend.resize`, `backend.layout()`. Layout is a
   no-op unless the surface size or a widget changed.
2. Drain `platform.poll_event()` to `None`, handling each event in the backend.
   Each is a tree walk and a small state write; each that changes pixels adds
   damage.
3. `core.frame_step_into` with the backend's reusable patch list.
4. `backend.layout()` again, for whatever the patches changed.
5. `backend.paint_until`: one clip and one tree walk per damage rectangle, then
   `platform.present` with the rectangles painted.

The counters a test can pin, with the numbers the work-budget test asserts at
800x600 (the design's table):

| Scenario | What it asserts |
| --- | --- |
| idle | an idle frame presents `0` rectangles and writes `0` pixels |
| text | a same-width label change presents exactly `1` rectangle, area `168` (the 24x7 label), and accounts for `0` allocations after warm-up |
| hover | a hover change presents `1` rectangle, the hovered widget |
| focus | a focus change presents `1` rectangle (old focus was none, new is one button) |
| type | typing one character presents `1` rectangle, the entry's `1800`-pixel box, and accounts for `1` allocation |
| checkbox | a checkbox flip presents `1` rectangle, area `504`, and allocates `0` |
| progress | a progress change presents `1` rectangle, area `720`, and allocates `0` |
| caret | a caret move presents `1` rectangle, area `1800`, and allocates `0`; the text is untouched |
| scroll | a wheel step presents `1` rectangle, area `600000`, and allocates `0` |
| remove | removing one row of 200 damages only rectangles at or below it (smallest damage `y` is `70`, the removed row's top) |
| append | appending a row damages only the new row (off-screen, `0` pixels) |
| repaint | a full repaint writes `945223` pixels for `480000`, a factor of `1.969`, under 2 |
| deadline | a 2500 us budget splits a 5-rectangle frame into `3` + `2`, every rectangle whole |

The layout counter is exact too: a same-width text change measures `1` node and
arranges `0`; removing one row of 200 measures `1` and arranges `1002` (the whole
tree, because the content height changed).

### Allocation accounting

The backend exposes three counters, all reset by `reset_counts` and read after a
frame:

- `frame_alloc_count()`: the number of allocation sites the backend executed in
  the last frame.
- `frame_alloc_bytes()`: a lower bound on the bytes those sites built, because the
  allocator's own size is not observable from Kelp and each site charges a
  documented estimate.
- `arena_high_water()`: the largest patch list `apply_diff` has produced.

A site is a place the backend builds a heap value: `make` copies a new widget's
props, an entry edit builds the new text, `set_entry_text` writes one, and
`post_id`/`schedule`/`push` append to a queue. The steady-state paths call none of
them, and a patch writes into the retained node's own `String`s instead of
replacing them.

The core's `diff` may allocate its patch list, so `core.diff_into(old, new, out)`
clears and refills a caller-owned `List<Patch>` instead. `soft_backend.apply_diff`
keeps that list in a `Box` on the backend, and `core.frame_step_into` does the same
for the loop's own diffs, so after the largest frame a smaller one reuses the
capacity.

The counter is scoped to the backend on purpose. It does **not** count the
application's `view`, which rebuilds the tree through Kelp's one allocator (libc
`malloc` hosted, the project's `[target] alloc` pair freestanding), nor the props
the core's diff builds for a changed widget. A whole-frame zero-allocation claim
would need a retained view model; see the limits below.

### Capacities, and what happens past one

- The damage list is a fixed `[Rect; 16]` (`damage.MAX_DAMAGE = 16`). It never
  exceeds 16: a touching or overlapping rectangle is merged, and when the list is
  full and nothing touches, the least-waste pair is merged first. Nothing is
  silently dropped.
- The clip stack is a fixed `[Rect; 8]`; a ninth push panics
  `clip stack depth 8 exceeded`.
- The glyph mask is a fixed `560`-byte stack array (`5 * 4 * 7 * 4`, the font's
  4x maximum); a text scale outside `1..=4` panics
  `text scale must be in 1..=4`.
- The reusable patch list has no fixed size, so the documented cap is
  `MAX_FRAME_PATCHES = 4096`: a frame that produces more patches panics
  `polyp: frame patch list exceeds MAX_FRAME_PATCHES` rather than growing without
  bound.
- The retained tree grows by one node and one parent insertion per `Create` and
  never shrinks; it is released only when the backend is dropped.

## The work-budget test and the benchmark

`examples/polyp-budget-test/` drives the backend directly and prints one number
per line. The Rust test `polyp_soft_work_budgets_hold` pins the whole output. It is the
program behind the table above.

`examples/polyp-bench/` runs five scenarios (200-row scroll, type 100 characters,
toggle 50 checkboxes, resize 800x600 to 1024x768, full repaint), each five times,
and prints per scenario: frames, pixels, presented rectangles, backend
allocations, and median and worst microseconds per frame. The counts are exact and
machine-independent; the times are the host's.

```sh
nix-shell shell.nix --run 'cd kelpc && ../target/release/kelpc build ../examples/polyp-bench -o ../target/polyp-bench'
( ulimit -v 1048576; ulimit -t 20; timeout 20 ./target/polyp-bench )
```

On the development host (7.8 GiB, LLVM backend, release `kelpc`), a full run of
`plan/polyp-v3.md`'s benchmark table:

| Scenario | frames | pixels | rects | allocs | median us/frame | worst us/frame |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| scroll-200 | 200 | 187536900 | 200 | 0 | 3973 | 4371 |
| type-100 | 500 | 16719500 | 500 | 500 | 4788 | 4859 |
| toggle-50 | 250 | 7226945 | 495 | 0 | 4558 | 4632 |
| resize | 150 | 187531425 | 2400 | 0 | 5846 | 6622 |
| repaint | 150 | 141783450 | 150 | 0 | 3575 | 3657 |

Those are the design note's numbers on one host at one moment, not a portable
guarantee: the frame counts, pixels, rectangles and allocations are exact and
machine-independent, the microseconds are not. The note records that the debug
`kelpc` build gives the same counts and times within a few percent. The test suite sets
`POLYP_BENCH_QUICK`, which shortens every scenario to one frame per run and keeps
the same counts per frame; the table above is a full run.

## What the display-free path does not do

- **No whole-frame zero-allocation claim.** The backend's own steady-state frame
  path allocates nothing and the patch list is reused, but `view` rebuilds the
  application tree through Kelp's one allocator every time a message arrives. The
  counters measure the backend, not the application.
- **No vector text, no shaping, no sub-pixel positioning.** The embedded 5x7
  face has selected Latin, Greek, Cyrillic and symbol glyphs at integer scales
  1 to 4. There is no bold face and unsupported code points use a replacement box.
- **No images.** The primitives are fills, strokes, lines, blends and the glyph
  mask blit; there is no image or texture primitive, no gradient and no pattern
  fill, and no colour type beyond `u32`.
- **No horizontal scrolling, no scrollbar dragging, no smooth scrolling.** The
  wheel moves by a fixed step and clamps.
- **No text selection, clipboard, IME or multi-line entry.** The caret is a byte
  offset kept on UTF-8 unit boundaries.
- **No GPU and no display server.** The renderer is the integer software raster
  in `backends/soft/soft/`; the only hardware fact is the platform's pixel
  pointer.
- **Theming is a `Theme` `datac` and a class table.** Colours and metrics are one
  value a platform can replace, and class overrides are `class_style`
  comparisons. There is no stylesheet parser and no selector engine; `polyp.css`
  is GTK's hook.
- **No screen-reader bridge.** The soft backend has an on-demand role tree and
  actions, but it does not connect to a host accessibility service.
- **Timing is the host's.** The benchmark's clock measures the process, not a
  display's frame pacing, and the numbers are one host's at one moment.

## See also

- [Polyp](/libraries/polyp): the core, the `Backend` trait, the `Patch` data and
  the GTK and headless backends
- [Polyp on bare metal](/libraries/polyp-freestanding): the two kernels and the
  framebuffer equivalence proof
- [Freestanding mode](/language/freestanding): the `[target]` section, the
  admitted `std` subset and the linker script
- [`plan/polyp-v3.md`](https://homelabone.xenoo.dev/gitea/Lilly/kelp/src/branch/main/plan/polyp-v3.md):
  the design record, stages 2, 3 and 5
