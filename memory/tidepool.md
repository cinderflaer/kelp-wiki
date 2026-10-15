---
title: "Tidepool memory design"
description: "Index of the Tidepool memory design pages. Tidepool is in design, and its pages are empty placeholders."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool memory design

Tidepool is the memory design for Kelp. It puts blocks beside a shared pool. Steps 1 and 2
are on `main`. The later steps are in design, and nothing on these pages is final.

On `main`, every hosted build links the base collector, a non-moving mark-region
collector, and caps its heap with `[target] heap_max`. Steps 1 and 2 are on `main`: the
runtime registers thread arguments and results, closure environments and lock values as
collector roots, the root table grows in chunks of 1024 slots that double, and
`[tidepool]` in `coral.toml` sets the start guesses, the headroom and the trigger rule.
Block regions are not on `main`. Channels build on `main` when a channel stays in one
thread. A channel end and the pool do not cross to a worker thread, because a channel end
is a resource (see [Common refusals](/memory/refusals)).

## Pages

- [The idea](/memory/tidepool/idea)
- The boundary (not written yet)
- Blocks at runtime (not written yet)
- The budget (not written yet)
- [Settings in `[tidepool]`](/memory/tidepool/settings)
- Safety rules (not written yet)
- The allocation path (not written yet)
- Safety tests (not written yet)
- Build order (not written yet)
- Performance claims and how they are measured (not written yet)
- What the programmer writes, reads and sees (not written yet)
- Test plan (not written yet)
- Tooling and release (not written yet)
- Failure and recovery (not written yet)

Most of these pages are placeholders until the design is settled, so they are listed
without a link and are not published. The settings page describes the `[tidepool]` keys
on `main`, and the idea page describes the later parts.
