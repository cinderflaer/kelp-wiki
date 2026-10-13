---
title: "Tidepool: the idea"
description: "Empty placeholder for a Tidepool design area. Tidepool is in design."
isPublished: true
tags: "memory, tidepool"
---
# Tidepool: the idea

Tidepool is the memory design for Kelp. Steps 1 and 2 are on `main`. The later parts are
in design, and nothing here is final.

- Most values go into a shared pool. Tidepool clears the pool when it fills, and nothing
  in the program reaches a value that the pool has cleared.
- A named block frees the values it owns when the block ends. The compiler writes each
  free. A value that could outlive its block is refused.
- One limit, `heap_max`, covers the shared pool and the block memory together.
- The first clearing is sized from two guesses. Later clearings follow the measured live
  size plus a headroom percentage.

Today `main` has the collector, the collector roots for thread and lock values, and the
`[tidepool]` settings for the first trigger, the headroom and the trigger rule. Block
regions are not on `main`. See [Tidepool](/memory/tidepool).
