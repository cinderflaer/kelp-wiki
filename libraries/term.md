---
title: "`term`: ANSI SGR colors, cursor control, clearing"
description: "Colors, cursor motion and screen/line clearing, plus NO_COLOR handling for the color functions specifically."
isPublished: true
tags: "library, cli"
---
Colors, cursor motion and screen/line clearing, plus `NO_COLOR` handling for the
color functions specifically.

**Gated on `env`** for that one name:

```toml
[dependencies]
term = "Juniper/fpl/term"
```

```kelp
impl "deps/term/lib" with caps(env = ["NO_COLOR"])
```

`NO_COLOR` follows [no-color.org](https://no-color.org): the variable's mere
*presence* disables color, regardless of its value.

## Colors

| Function | Returns | SGR code |
| --- | --- | --- |
| `red(s: &str)` | `String` | `31` |
| `green(s: &str)` | `String` | `32` |
| `yellow(s: &str)` | `String` | `33` |
| `blue(s: &str)` | `String` | `34` |
| `bold(s: &str)` | `String` | `1` |
| `dim(s: &str)` | `String` | `2` |
| `wrap(s: &str, code: &str)` | `String` | any code, wrapped as `ESC[<code>m…ESC[0m` |
| `reset_code()` | `String` | the bare `ESC[0m` |
| `no_color()` | `bool` | whether `NO_COLOR` is set |

With `NO_COLOR` set, every color function returns its argument unchanged (no
escapes at all). Without it, the text is wrapped as
`ESC[<code>m` + `s` + `ESC[0m`.

`wrap` is the general form: pass `"1;31"` to mix bold and red.

## Cursor and clearing

These **do not** consult `NO_COLOR`: clearing and cursor motion are not color,
and disabling them would silently break a caller that depends on the cursor
actually moving.

| Function | Escape | Meaning |
| --- | --- | --- |
| `clear_screen()` | `ESC[2J` | clear the screen |
| `clear_line()` | `ESC[2K` | clear the whole line |
| `cursor_up(n)` | `ESC[<n>A` | move up `n` |
| `cursor_down(n)` | `ESC[<n>B` | move down `n` |
| `cursor_to(row, col)` | `ESC[<row>;<col>H` | 1-based, matching every terminal's own convention |

## Returned, not printed

Every function returns an owned `String`; nothing writes. The escape sequences
are built from a dynamic byte (`ESC`, 27) that no string literal can spell.
`syntax.md`'s string escape set is closed and has no `\x1b`, so nothing here has
static storage to borrow from.

## Example

```kelp
impl "deps/term/lib" with caps(env = ["NO_COLOR"])
impl "std/env"

fun main() {
    print(term.no_color())
    print(term.red("red text"))
    print(term.bold("bold text"))
    print(term.clear_line())
    print(term.cursor_up(2))
    print(term.cursor_to(1, 1))
    env.set("NO_COLOR", "1")
    print(term.no_color())
    print(term.red("no escapes now"))
}
```

Output (`cat -A` shows the `ESC` bytes as `^[` and line ends as `$`):

```
false$
^[[31mred text^[[0m$
^[[1mbold text^[[0m$
^[[2K$
^[[2A$
^[[1;1H$
true$
no escapes now$
```

## Notes

- No width/height detection: that needs an `ioctl` extern this compiler does not
  expose. Nothing here knows the terminal size.
- No named 256-color or truecolor forms, no underline/italic/reverse; use `wrap`
  with the SGR code you want.
- No `env.has` dependency beyond `NO_COLOR`, so a program that only colors text
  needs no other environment access.
- `no_color()` is checked at each color call, so setting `NO_COLOR` mid-run takes
  effect immediately.
