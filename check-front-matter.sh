#!/bin/sh
# Checks every page's front matter against what the Wiki.js git storage module
# can import (see "Front matter" in README.md). A page that fails one of these
# is dropped by the sync without an error a reader can see, so run this before a
# commit that touches a page and at every release:
#
#     ./check-front-matter.sh
#
# Exit status is 0 when every page passes and 1 otherwise; each failure prints as
# `path: what is wrong`.
cd "$(dirname "$0")" || exit 2
status=0
for page in $(git ls-files '*.md' | grep -v '^README\.md$'); do
    awk -v page="$page" '
        function bad(msg) { printf "%s: %s\n", page, msg; failed = 1 }
        NR == 1 { if ($0 != "---") { bad("no front matter"); exit } ; next }
        /^---[ \t]*$/ { closed = 1; exit }
        /^title:/ { has_title = 1 }
        /^description:/ {
            has_desc = 1
            v = $0; sub(/^description:[ \t]*/, "", v)
            if (v !~ /^".*"$/) { bad("description is not a quoted string") }
            else {
                v = substr(v, 2, length(v) - 2)
                gsub(/\\./, "x", v)
                if (length(v) > 255) { bad("description is " length(v) " characters, the limit is 255") }
            }
        }
        /^isPublished:/ {
            has_pub = 1
            if ($0 !~ /^isPublished:[ \t]*(true|false)[ \t]*$/) { bad("isPublished is not a boolean") }
        }
        /^published:/ { bad("`published:` is not read; use isPublished") }
        /^tags:/ {
            has_tags = 1
            if ($0 !~ /^tags:[ \t]*"[^"]*"[ \t]*$/) { bad("tags is not a quoted, comma-space separated string") }
        }
        END {
            if (failed && !closed && NR < 1) exit
            if (NR >= 1 && !closed && !failed) { bad("front matter is never closed") }
            if (closed) {
                if (!has_title) bad("no title")
                if (!has_desc) bad("no description")
                if (!has_pub) bad("no isPublished")
                if (!has_tags) bad("no tags")
            }
            exit failed ? 1 : 0
        }
    ' "$page" || status=1
done
exit $status
