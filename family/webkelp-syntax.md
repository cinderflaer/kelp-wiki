---
title: "WebKelp syntax reference"
description: "Every WebKelp construct: Markdown blocks and inline spans, attributes, ::: containers, raw HTML rules, CSS collection, front matter keys, and the features that are deliberately not supported."
isPublished: true
tags: "family, reference"
---

> # ARCHIVED PROJECT: WEBKELP MOVED TO POLYP
>
> WebKelp now lives in the Polyp repository, in the `web/` folder:
> https://homelabone.xenoo.dev/gittea/Juniper/polyp
>
> The WebKelp repository is archived, and its demo and playground sites have been removed.
> This page is kept for reference only and may be out of date.
WebKelp is Markdown plus three additions: **attributes** on anything, **containers** that
make any element, and **CSS blocks**. Raw HTML is always allowed. This page is the
complete reference; the [overview](/family/webkelp) is the short version.

## Blocks

| Construct | Source | Output |
| --- | --- | --- |
| Heading | `## Title` (also `## Title ##`) | `<h2 id="title">Title</h2>` |
| Paragraph | consecutive lines | `<p>…</p>` |
| Rule | `---`, `***`, `___`, or spaced `- - -` | `<hr>` |
| Quote | `> text`, nests, holds any block | `<blockquote>` |
| Bullet list | `-`, `*` or `+` | `<ul>` |
| Numbered list | `1.` or `1)`, starting number kept | `<ol>` or `<ol start="5">` |
| Code | ```` ``` ```` or `~~~` fences, info string `lang` | `<pre><code class="language-lang">` |
| Table | pipe rows plus a `\|:--\|--:\|` separator | `<table>` with `text-align` styles |

Details worth knowing:

- **Heading ids are generated** from the text (`## Why so easy` → `id="why-so-easy"`), and
  made unique within a page by appending `-2`, `-3`. An id you write with `{#id}` wins and
  is reserved. The first `#` heading is the default page title.
- **Lists nest** by indentation under the item's text. A list is **tight** (no `<p>` inside
  items) unless a blank line separates items or a blank line splits one item's content, in
  which case it is **loose** and each item's paragraphs get `<p>`.
- **Code fences** are closed by a fence of the same character and at least the same length.
  The contents are escaped and never parsed. Attributes after the language go on the `<pre>`:
  ```` ```js {#demo .wide} ````.
- **Tables** take alignment from the separator row: `:--` left, `--:` right, `:-:` centre.
  Use `\|` for a literal pipe inside a cell. Cells hold inline Markdown.
- Leading tabs are expanded to four spaces before parsing.

## Inline

| Construct | Source | Output |
| --- | --- | --- |
| Emphasis | `*em*`, `_em_` | `<em>` |
| Strong | `**strong**`, `__strong__` | `<strong>` |
| Both | `***both***` | `<strong><em>` |
| Strikethrough | `~~gone~~` | `<del>` |
| Code | `` `code` ``, ``` `` a ` b `` ``` | `<code>`, contents escaped |
| Link | `[text](url "title")` | `<a href title>` |
| Image | `![alt](src "title")` | `<img src alt title>` |
| Autolink | `<https://example.com>` | `<a href>` (also `http:` and `mailto:`) |
| Span | `[text]{.hl}` | `<span class="hl">` |
| Line break | two trailing spaces, or `\` at the end of a line | `<br>` |
| Escape | `\*`, `\_`, `\[`, `\<` … | the literal character |

- `_` emphasis does not trigger inside a word, so `snake_case_word` is left alone.
  `*` does, as in `un*frigging*believable`.
- `2 * 3 * 4` is untouched: an opening `*` has to be followed by a non-space.
- **`.wk` links become `.html`**: `[a](page.wk#part)` → `href="page.html#part"`. The rewrite
  applies when `.wk` ends the path, or is followed by `#` or `?`.
- `&`, `<` and `>` in text are escaped, except existing entities (`&copy;` stays as written)
  and real HTML tags (see [Raw HTML](#raw-html)).

## Attributes

A `{…}` block adds attributes to the element it is attached to:

```markdown
## Title {#top .big}
[Buy](/shop.wk){.btn data-track=buy}
![logo](l.png){width=120 loading=lazy}
[note]{.hl}

{.lead}
A paragraph that gets the class.

- item {.done}
```

| Token | Meaning |
| --- | --- |
| `#name` | `id="name"` |
| `.name` | adds to `class` (several are merged, in order) |
| `key=value`, `key="a b"`, `key='a b'` | `key="value"`, escaped |
| `flag` | a boolean attribute: `hidden`, `defer`, … |

**Where a block attaches:**

| Position | Attaches to |
| --- | --- |
| glued right after `)` of a link or image, or after `]` of a span | that inline element |
| at the end of a heading, paragraph, list item or code-fence line, after a space | that block |
| alone on the line above a block | the block below (paragraph, list, quote, table, code, container) |

**When braces are attributes.** The content must start with `#` or `.`, or contain `=`.
Prose like `{ not attrs }` is left alone. Braces **inside a quoted value are ignored**, so
attributes for Alpine, htmx or Vue work as written:

```markdown
[toggle]{x-data="{ open: false }" @click="open = !open"}
```

A quote only counts as opening a value when it follows `=`, so an apostrophe elsewhere does
not swallow the closing brace.

## Containers

```markdown
::: section #hero .dark {data-role=banner}
# Hi

Markdown *inside*.
:::
```

- `::: tag attrs` opens and a bare `:::` closes. The tag is any name (letters, digits and
  `-`), so `::: my-widget` makes a custom element. **No tag means `div`**: `::: .card`.
- Attributes are written bare or wrapped in braces, in any mix: `::: article .card {data-x=1}`.
- **Containers nest.** The closer that matches is found by counting openers, so nesting works
  with the same colon count; a longer run such as `::::` is also accepted, for readability.
- An unclosed container runs to the end of the file.
- The body is parsed as blocks, so headings, lists and further containers work inside.

Two tags are special:

| Tag | Behaviour |
| --- | --- |
| `::: style` | the body is CSS; it is collected into the page's stylesheet and **not** emitted in the HTML |
| `::: script` | the body is emitted verbatim inside `<script>`, with the attributes you gave (`::: script type=module`) |

## Raw HTML

HTML is never escaped or rewritten.

**Inline.** A tag, closing tag, comment or `<!doctype>`-style declaration inside a paragraph
passes through as written. A `<` that does not start a tag is escaped to `&lt;`.

**Block.** A line that begins with a tag starts a raw block, unless the tag is a text-level
one. The text-level tags, which stay inside a paragraph, are:

```text
a abbr b bdi bdo br cite code data dfn del em i img ins kbd label
mark q s samp small span strong sub sup time u var wbr
```

Every other tag at the start of a line (`<div>`, `<button>`, `<input>`, `<search>`,
`<my-card>`, …) begins a raw block, and so does a closing tag.

A raw block runs to the **next blank line**, with three exceptions that run to their
closing marker even across blank lines: `<script>`, `<style>`, `<pre>` and `<textarea>` (to
the matching `</…>`), and `<!-- -->` comments (to `-->`).

**Markdown inside a raw block is not processed**, as in CommonMark:

```markdown
<div class="raw">
**left alone**
</div>
```

Leave blank lines around the content, or use a `:::` container, when you want Markdown
inside an element.

## CSS

Every `::: style` block on the page is collected, in order, into one stylesheet. The output
order is:

1. `@charset` and `@import` lines from `::: style` blocks, hoisted to the top, because CSS
   ignores them anywhere else;
2. the default theme, unless the page says `theme: none`;
3. the rest of the page's CSS, in source order.

The stylesheet is written to `<name>.css` and linked from the page. With `--inline` it goes
in a `<style>` block instead. A page with no CSS at all, and `theme: none`, gets neither.

Extra stylesheets are linked with `css: a.css, b.css` in the front matter. A raw `<style>`
element in the body is HTML like any other and is left in place.

## Front matter

An optional block at the very top of the file, opened and closed by `---` lines. The
front matter is recognised only when the closing line exists.

```markdown
---
title: My page
lang: en
description: For search engines
theme: auto
css: a.css, b.css
js: app.js
head: |
  <link rel="icon" href="/f.ico">
body: {.home}
html: {class=app dir=rtl}
shell: none
---
```

| Key | Default | Effect |
| --- | --- | --- |
| `title` | the first `#` heading, else `Untitled` | `<title>` |
| `lang` | `en` | `<html lang>` |
| `description` | none | `<meta name="description">` |
| `theme` | `auto` | `auto`: light, and dark from `prefers-color-scheme`. `light` or `dark`: forced, via `data-theme` on `<html>`. `none`: no default stylesheet |
| `css` | none | comma-separated stylesheets, each a `<link rel="stylesheet">` |
| `js` | none | comma-separated scripts, each `<script defer src>` at the end of `<body>` |
| `head` | none | raw HTML appended to `<head>`; `head: |` takes an indented block, dedented by two spaces |
| `body` | none | attributes for `<body>`, with or without braces |
| `html` | none | attributes for `<html>`, in addition to `lang` |
| `shell` | `page` | `none` emits only the body markup: no doctype, `<html>`, `<head>` or `<body>` |

A value runs from the first `:` to the end of the line, so values may contain colons
and quotes.

With `shell: none` the output is a fragment, for embedding in another page. The page's
CSS is still written to its `.css` file, or, with `--inline`, put in a `<style>` block at the
start of the fragment.

## The default theme

| Variable | Light | Purpose |
| --- | --- | --- |
| `--wk-bg` | `#ffffff` | page background |
| `--wk-fg` | `#1f2328` | text |
| `--wk-muted` | `#59636e` | secondary text |
| `--wk-accent` | `#0b6bcb` | links, buttons |
| `--wk-border` | `#d1d9e0` | rules, table borders |
| `--wk-code` | `#f3f4f6` | code background |
| `--wk-max` | `46rem` | page width |

Helper classes: `.center`, `.muted`, `.hero`, `.grid` (responsive columns), `.card`,
`.btn`. To widen a page: `::: style` with `body { max-width: none }`.

## Not supported

| Missing | Use instead |
| --- | --- |
| attributes on `**strong**` or `` `code` `` | `[**text**]{.x}` (a span) or raw HTML |
| attributes on one table cell or `<hr>` | raw HTML, or a `{…}` line above the whole table |
| reference links `[a][ref]`, footnotes | inline links, or raw HTML |
| bare URLs turned into links | `<https://…>` |
| task lists `- [x]`, setext headings (`===` underlines) | `<input type=checkbox>` in raw HTML; `#` headings |
| Markdown inside a raw HTML block | a `:::` container |
| a `.wk` link that stays `.wk` | raw `<a href>` |
| variables, includes, loops | generate the `.wk` with a script |

## See also

- [WebKelp](/family/webkelp)
- [How WebKelp is built](/family/webkelp-internals)
