#!/bin/sh
# Checks every Kelp example in the wiki with the Kelp release compiler.
#
# Run it from anywhere, with no arguments, to check every tracked Markdown page:
#
#     scripts/check-examples.sh
#
# Pass page paths to check only those pages (relative to the repository root):
#
#     scripts/check-examples.sh tutorial/01-hello.md examples/recursive-fibonacci.md
#
# Each ```kelp fence is handled as follows. The fence may carry the attribute
# refused or norun (or both), or the attribute project alone:
#
#   program   no attribute, and the block has a `fun main` line. The block is
#             built with `kelpc build example.kp -o example`, and the build must
#             succeed. Its output is checked when the next fence on the page is
#             a ```text block (see "Output" below).
#   fragment  no attribute, and no `fun main`. The block is not compiled. Each
#             fragment is printed in the report as skipped, so none is skipped
#             silently.
#   refused   ```kelp refused. The block must be a program, and the compiler
#             must refuse it: the command must exit with status 1.
#   project   ```kelp project. The block is one file of a multi-file project, or
#             imports a package or a module of its own project, so it cannot
#             compile on its own. It is parsed with `kelpc fmt`, which catches
#             syntax errors, and listed in the report as not compiled, so the
#             report always shows how many files were parsed rather than built.
#   norun     ```kelp norun. The program is built (or refused, with refused) but
#             not run, and its output is not compared. Use it when the output
#             depends on the network, the clock or the machine.
#
# Output: when the next fence on the same page is a ```text block, it is the
# output of the program or refused block before it. The next fence is the only
# candidate, so prose between the two does not matter, but a text block that
# belongs to something else must not follow a program directly.
#
#   * A text block whose first line is `$ kelpc run ...`, `$ kelpc check ...` or
#     `$ kelpc build ...` is a transcript. That command is run in a scratch
#     directory, with the program saved under the file name the command gives,
#     and its exit status must be 0 (1 for a refused block). Its output must
#     equal the rest of the text block, line for line.
#   * Any other text block is the program's output. The program is built, then
#     run, and its output must equal the text block. For a refused block the
#     build's diagnostics must equal the text block instead. The program's own
#     exit status is not compared for this kind of output, because a program can
#     end with a panic that is the output itself.
#   * A text block that starts with `$` but is not a kelpc command, such as
#     `$ ./prog`, is not compared, and the report says so as a NOTE.
#
#   Programs and transcripts run in a pseudo-terminal (script(1), util-linux),
#   so stdout and stderr interleave in the order a reader's terminal shows them.
#   Carriage returns from the terminal are dropped. The scratch directory is cut
#   from paths in the output, so a diagnostic names the file as the page does.
#
# Every failure prints file, line, and for a mismatch a unified diff of the
# expected output (the page) against the actual output (the compiler). The
# script exits 0 when every check passes and 1 otherwise, and 2 when it cannot
# run (no compiler, not a Git checkout, and so on).
#
# Settings, all optional:
#
#   KELPC       the compiler to run (default: kelpc on PATH)
#   KELPC_LOCK  a lock file. When set, every compiler run is wrapped in
#               `flock KELPC_LOCK`, so runs from several jobs on one machine do
#               not overlap. Leave it unset to lock the whole run from outside
#               instead, for example `flock LOCK scripts/check-examples.sh`.
#   TMPDIR      where the scratch directory is made (default: /tmp)
#
# It needs sh, awk, sed, grep, diff, git (only when run with no arguments),
# script (util-linux), and a C compiler and linker (cc) on PATH that kelpc can
# use, the same as kelpc itself. Examples that use the TLS or HTTP modules also
# need the OpenSSL headers on the C include path (the Kelp dev shell provides
# them). The script writes only under TMPDIR and removes that directory on exit.
#
# Checking the examples in CI: run this one command from a checkout with kelpc
# on PATH. The exit status is the result.
#
#     scripts/check-examples.sh

cd "$(dirname "$0")/.." || exit 2

KELPC=${KELPC:-kelpc}
if ! command -v "$KELPC" >/dev/null 2>&1; then
    echo "check-examples: compiler not found: $KELPC (set KELPC)" >&2
    exit 2
fi
if ! command -v script >/dev/null 2>&1; then
    echo "check-examples: script (util-linux) not found; the programs run in a terminal" >&2
    exit 2
fi
if [ $# -eq 0 ] && ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "check-examples: not a Git checkout; pass the pages to check as arguments" >&2
    exit 2
fi

work=$(mktemp -d "${TMPDIR:-/tmp}/check-examples.XXXXXX") || exit 2
trap 'rm -rf "$work"' EXIT INT TERM
mkdir -p "$work/blocks" "$work/run"

# Compiler runs go through here so KELPC_LOCK applies to every one of them.
kelpc() {
    if [ -n "${KELPC_LOCK:-}" ]; then
        flock "$KELPC_LOCK" "$KELPC" "$@"
    else
        "$KELPC" "$@"
    fi
}

# Runs a command line in a pseudo-terminal, as a reader's terminal would, so that
# stdout and stderr interleave in the order the reader sees. The output goes to
# the file named second, with the terminal's CR LF line ends made LF. The result
# is the command's exit status.
in_terminal() {
    script -qefc "$1" /dev/null > "$2.raw" 2>/dev/null
    st=$?
    tr -d '\r' < "$2.raw" > "$2"
    rm -f "$2.raw"
    return $st
}

# A lock for the compiler runs in transcripts, when KELPC_LOCK is set.
lock_prefix=""
if [ -n "${KELPC_LOCK:-}" ]; then
    lock_prefix="flock $KELPC_LOCK "
fi

if [ $# -gt 0 ]; then
    pages=$(printf '%s\n' "$@")
else
    pages=$(git ls-files '*.md' | grep -v '^README\.md$')
fi

# Pass 1: pull every fenced block out of every page. Block N is written as
# $work/blocks/N.{page,line,info,body}, numbered in page order, so block N+1 is
# the next fence after block N whenever both are on the same page.
n=0
for page in $pages; do
    [ -f "$page" ] || { echo "check-examples: no such page: $page" >&2; exit 2; }
    n=$(awk -v dir="$work/blocks" -v page="$page" -v n="$n" '
        BEGIN { inb = 0 }
        {
            if (!inb) {
                if ($0 ~ /^[ \t]*`{3,}/) {
                    lead = $0; sub(/[^ \t].*$/, "", lead); ind = length(lead)
                    fence = $0; sub(/^[ \t]*/, "", fence); sub(/[^`].*$/, "", fence)
                    info = $0; sub(/^[ \t]*`+/, "", info)
                    sub(/^[ \t]+/, "", info); sub(/[ \t]+$/, "", info)
                    n++; inb = 1; start = NR
                    base = dir "/" n
                    printf "" > (base ".body")
                }
                next
            }
            t = $0; sub(/^[ \t]*/, "", t); sub(/[ \t]*$/, "", t)
            if (t ~ /^`+$/ && length(t) >= length(fence)) {
                inb = 0
                close(base ".body")
                printf "%s\n", page > (base ".page"); close(base ".page")
                printf "%d\n", start > (base ".line"); close(base ".line")
                printf "%s\n", info > (base ".info"); close(base ".info")
                next
            }
            line = $0; k = 0
            while (k < ind && substr(line, 1, 1) == " ") { line = substr(line, 2); k++ }
            print line >> (base ".body")
        }
        END { print n }
    ' "$page")
done
# A block with an empty body never gets a body file, so make one for each block.
i=1
while [ "$i" -le "$n" ]; do
    [ -f "$work/blocks/$i.body" ] || : > "$work/blocks/$i.body"
    i=$((i + 1))
done

failures=0
programs=0
programs_run=0
refused=0
projects=0
fragments=0
outputs=0
notes=0
report="$work/report"
: > "$report"

fail() {
    failures=$((failures + 1))
    printf 'FAIL %s\n' "$1"
}

# Prints the first 40 lines of a compiler or program output, indented, with the
# scratch directory cut from paths as in the comparison.
shown_lines() {
    sed "s|$1/||g" "$2" | sed 's/^/    | /' | head -n 40
}

# Pass 2: check each kelp block.
i=1
while [ "$i" -le "$n" ]; do
    info=$(cat "$work/blocks/$i.info")
    case "$info" in
        kelp|"kelp "*) ;;
        *) i=$((i + 1)); continue ;;
    esac
    page=$(cat "$work/blocks/$i.page")
    line=$(cat "$work/blocks/$i.line")
    where="$page:$line"

    # Attributes: any of refused, norun, or project alone.
    attrs=${info#kelp}
    refuse=0
    norun=0
    project=0
    bad_attr=""
    for word in $attrs; do
        case "$word" in
            refused) refuse=1 ;;
            norun) norun=1 ;;
            project) project=1 ;;
            *) bad_attr=$word ;;
        esac
    done
    if [ -n "$bad_attr" ]; then
        fail "$where: unknown attribute '$bad_attr' in fence '$info' (the attributes are refused, norun and project)"
        i=$((i + 1)); continue
    fi
    if [ "$project" -eq 1 ] && { [ "$refuse" -eq 1 ] || [ "$norun" -eq 1 ]; }; then
        fail "$where: project cannot be combined with refused or norun"
        i=$((i + 1)); continue
    fi

    # Project files are parsed only. A file that imports its own project's
    # modules or packages cannot be compiled alone.
    if [ "$project" -eq 1 ]; then
        projects=$((projects + 1))
        dir="$work/run/$i"
        mkdir -p "$dir"
        cp "$work/blocks/$i.body" "$dir/example.kp"
        if (cd "$dir" && kelpc fmt example.kp < /dev/null) > "$dir/actual" 2>&1; then
            printf 'project file (parsed, not compiled): %s\n' "$where" >> "$report"
        else
            fail "$where: project file does not parse"
            shown_lines "$dir" "$dir/actual"
        fi
        next=$((i + 1))
        if [ "$next" -le "$n" ] && [ "$(cat "$work/blocks/$next.page")" = "$page" ] \
            && [ "$(cat "$work/blocks/$next.info")" = "text" ]; then
            printf 'NOTE %s: the text block at %s:%s follows a project file, not compared\n' \
                "$where" "$page" "$(cat "$work/blocks/$next.line")" >> "$report"
            notes=$((notes + 1))
        fi
        i=$((i + 1)); continue
    fi

    if ! grep -Eq '(^|[^A-Za-z0-9_])fun main([^A-Za-z0-9_]|$)' "$work/blocks/$i.body"; then
        if [ "$refuse" -eq 1 ]; then
            fail "$where: refused block has no 'fun main', so there is nothing for the compiler to refuse"
        else
            fragments=$((fragments + 1))
            printf 'skipped fragment (no fun main): %s\n' "$where" >> "$report"
        fi
        i=$((i + 1)); continue
    fi

    # The output block: the next fence, when it is a text block on the same page.
    out_block=0
    next=$((i + 1))
    if [ "$next" -le "$n" ] && [ "$(cat "$work/blocks/$next.page")" = "$page" ] \
        && [ "$(cat "$work/blocks/$next.info")" = "text" ]; then
        out_block=$next
    fi
    transcript=""
    plain=0
    if [ "$out_block" -ne 0 ]; then
        first=$(head -n 1 "$work/blocks/$out_block.body")
        outline=$(cat "$work/blocks/$out_block.line")
        case "$first" in
            '$ kelpc '*)
                transcript=${first#'$ kelpc '}
                case "$transcript" in
                    run\ *|check\ *|build\ *) ;;
                    *) transcript=""
                       printf 'NOTE %s: the text block at %s:%s is not a run, check or build command, not compared\n' \
                           "$where" "$page" "$outline" >> "$report"
                       notes=$((notes + 1)) ;;
                esac
                if [ -n "$transcript" ] && printf '%s' "$transcript" | grep -q '[;|&$<>`()\\"'"'"']'; then
                    transcript=""
                    printf 'NOTE %s: the text block at %s:%s is not a plain kelpc command, not compared\n' \
                        "$where" "$page" "$outline" >> "$report"
                    notes=$((notes + 1))
                fi ;;
            '$ '*)
                printf 'NOTE %s: the text block at %s:%s is not a kelpc command, not compared\n' \
                    "$where" "$page" "$outline" >> "$report"
                notes=$((notes + 1)) ;;
            *) plain=1 ;;
        esac
    fi

    # The file name comes from the command when there is one, so messages that
    # print the name match the page. Otherwise it is example.kp.
    name="example.kp"
    for word in $transcript; do
        case "$word" in
            *.kp) name=$word ;;
        esac
    done
    case "$name" in
        */*|-*) fail "$where: the command names a file this check cannot place: '$name'"
                i=$((i + 1)); continue ;;
    esac

    dir="$work/run/$i"
    mkdir -p "$dir"
    cp "$work/blocks/$i.body" "$dir/$name"
    if [ "$refuse" -eq 1 ]; then
        refused=$((refused + 1))
        expect_status=1
    else
        programs=$((programs + 1))
        expect_status=0
    fi

    if [ -n "$transcript" ] && [ "$norun" -eq 0 ]; then
        shown="kelpc $transcript"
        (cd "$dir" && in_terminal "$lock_prefix$KELPC $transcript" "$dir/actual")
        status=$?
        if [ "$status" -ne "$expect_status" ]; then
            if [ "$refuse" -eq 1 ]; then
                fail "$where: refused block was not refused: '$shown' exited $status, expected 1"
            else
                fail "$where: '$shown' exited $status, expected 0"
            fi
            shown_lines "$dir" "$dir/actual"
            i=$((i + 1)); continue
        fi
        compare_with="$work/blocks/$out_block"
        expected_from=2
    else
        shown="kelpc build $name -o example"
        (cd "$dir" && kelpc build "$name" -o example < /dev/null) > "$dir/build.out" 2>&1
        status=$?
        if [ "$status" -ne "$expect_status" ]; then
            if [ "$refuse" -eq 1 ]; then
                fail "$where: refused block was not refused: '$shown' exited $status, expected 1"
            else
                fail "$where: '$shown' exited $status, expected 0"
            fi
            shown_lines "$dir" "$dir/build.out"
            i=$((i + 1)); continue
        fi
        compare_with=""
        if [ "$refuse" -eq 1 ]; then
            # A refused block's output is the compiler's diagnostics.
            if [ "$plain" -eq 1 ]; then
                cp "$dir/build.out" "$dir/actual"
                shown="kelpc build $name -o example (diagnostics)"
                compare_with="$work/blocks/$out_block"
                expected_from=1
            fi
        elif [ "$plain" -eq 1 ] && [ "$norun" -eq 0 ]; then
            (cd "$dir" && in_terminal ./example "$dir/actual")
            shown="$name (run)"
            compare_with="$work/blocks/$out_block"
            expected_from=1
        fi
        if [ "$plain" -eq 1 ] && [ "$norun" -eq 1 ] && [ "$refuse" -eq 0 ]; then
            printf 'NOTE %s: the text block at %s:%s is not compared, the block is norun\n' \
                "$where" "$page" "$outline" >> "$report"
            notes=$((notes + 1))
        fi
    fi

    if [ -n "$compare_with" ]; then
        outputs=$((outputs + 1))
        tail -n +"$expected_from" "$compare_with.body" > "$dir/expected"
        # The compiler prints the path it was given as an absolute path, so the
        # scratch directory is cut from the output: a file shows as the page
        # names it, for example err.kp:2:5.
        sed "s|$dir/||g" "$dir/actual" > "$dir/actual.rel"
        if diff -u --label "expected (page $page:$outline)" --label "actual ($shown)" \
            "$dir/expected" "$dir/actual.rel" > "$dir/diff"; then
            :
        else
            fail "$where: output of '$shown' does not match the text block at $page:$outline"
            cat "$dir/diff"
        fi
    fi
    if [ "$norun" -eq 0 ] && [ "$refuse" -eq 0 ] && [ -n "$compare_with" ]; then
        programs_run=$((programs_run + 1))
    fi
    i=$((i + 1))
done

if [ -s "$report" ]; then
    cat "$report"
fi
printf '\ncheck-examples: %s pages, %s fences of any language\n' \
    "$(printf '%s\n' "$pages" | wc -l | tr -d ' ')" "$n"
printf '  programs compiled: %s\n' "$programs"
printf '  programs run with output compared: %s\n' "$programs_run"
printf '  refused blocks checked: %s\n' "$refused"
printf '  output blocks compared: %s\n' "$outputs"
printf '  project files parsed, not compiled: %s\n' "$projects"
printf '  fragments skipped: %s\n' "$fragments"
printf '  notes: %s\n' "$notes"
printf '  failures: %s\n' "$failures"
[ "$failures" -eq 0 ]
