---
title: "Pending changes"
description: "Changes that are in kelp but not in a released version yet. The release procedure reads this page; it replaces plan/CHANGELOG.pending.md."
isPublished: true
tags: "changelog, release"
---
> **Moved 2026-10-16.** This page replaces `plan/CHANGELOG.pending.md` in the kelp repository, which is removed. The release procedure now reads this page, not the kelp repository. Add a line here for every user-visible change, and wipe the lines back to this header when a version is released.

# Pending changes

Scratch file for changes that are not released yet. It lives on this page now: an edit here is the edit, and the wiki sync carries it.

Add a line here when a user-visible change lands in `kelp`. **Do not touch
`wiki/changelog.md` until a version is released**: the changelog page carries
releases only.

When a version drops, write that release's entry in `wiki/changelog.md` from
this file plus the tag's commits and the Gitea release body, then wipe this file
back to this header. No need to ask first.

Keep each line short and factual: what changed, and why it matters to someone
writing Kelp. Group under the headings below; delete the headings that stay
empty on release.

## Documentation

- The Coral, Polyp, fpl and Lighthouse pages match their `main` branches: Coral has no version pins and records `coral.lock`, Polyp exports no `QUIT_ID` and its API lists the v4 and v5 nodes, fpl has 32 libraries, and Lighthouse has a Kelp port of the server in progress.

## Added

- A multi-line string literal: `"""` opens a block, a line holding only `"""` closes it, and the closing line's indentation is removed from the lines between. The value always ends with a newline and uses the string escapes, so a block equals the same text written with `\n` (issue 260). An unterminated block is refused at its opening.

## Changed

- The example pages match their programs: `count-lines-words-bytes` passes an absolute path, the `sandbox-directory-grant` panic line is current, and the `count-lines-in-kelp-tree` listing is the current `examples/src`.
- The bench runner (`bench/gc/run.sh`) and the Tidepool step 0, step 1 and block test comments describe the hosted build and the checked blocks. No behaviour changed.
