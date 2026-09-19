# cli_tool

A small `wc` with flags, an option that has a default, positionals and a help
text. It is the example to read before writing anything with a command line.

| | |
| --- | --- |
| Source | [`src/cli_tool.kp`](src/cli_tool.kp) |
| Needs | `argparse = "Juniper/fpl/argparse"` |
| Shows | flags against options, defaults, positionals, `--help`, exit codes, `argv[0]` |

## The dependency

```toml
[dependencies]
argparse = "Juniper/fpl/argparse"
```

## The rules this tool follows

- `--lines` is a **flag**: present or absent, never a value.
- `--label` is an **option**: `--label=counted` and `--label counted` both work,
  and it has a declared default.
- Anything else is a **positional**. There are no short flags and no subcommands.
- An unknown `--name` is a parse error, and the tool prints the message the parser
  produced and exits 2.
- No positionals means help text and exit 2, which is the convention a shell user
  expects.

## The program

```kelp
impl "deps/argparse/lib" as argparse
impl "std/fs"
impl "std/str"
impl "std/fmt"
impl "std/process"
impl "std/path" as p

fun is_space(c: u8).R: bool = c == ' ' || c == '\t' || c == '\n' || c == '\r'

fun count_lines(s: &str).R: i64 {
    val bytes = str.len(s)
    var lines: i64 = 0
    var i: usize = 0
    while i < bytes {
        if str.byte(s, i) == '\n' {
            lines += 1
        }
        i += 1
    }
    if bytes > 0 && str.byte(s, bytes - 1) != '\n' {
        lines += 1
    }
    return lines
}

fun count_words(s: &str).R: i64 {
    val bytes = str.len(s)
    var words: i64 = 0
    var in_word = false
    var i: usize = 0
    while i < bytes {
        if is_space(str.byte(s, i)) {
            in_word = false
        } else if !in_word {
            words += 1
            in_word = true
        }
        i += 1
    }
    return words
}

fun measure(path: &str, label: &str, want_lines: bool, want_words: bool, want_bytes: bool) {
    val text = fs.read_text(path)
    val s = text.as_str()
    val prefix = str.concat(label, " ")
    // The file name, not the full path: the output is a report, and the caller
    // already knows which path it passed.
    val line = str.concat(prefix.as_str(), p.file_name(path))

    var out = String.empty()
    out.push_str(line.as_str())
    if want_lines {
        out.push_str(" lines=")
        val n = fmt.int(count_lines(s))
        out.push_str(n.as_str())
    }
    if want_words {
        out.push_str(" words=")
        val n = fmt.int(count_words(s))
        out.push_str(n.as_str())
    }
    if want_bytes {
        out.push_str(" bytes=")
        val n = fmt.int(str.len(s).to_i64())
        out.push_str(n.as_str())
    }
    print(out)
}

// Everything the parsed arguments need happens in `run`, so that no owned local
// is declared inside the `if let` arm below.
fun run(parser: &argparse.Parser, pa: &argparse.ParsedArgs) {
    if argparse.has_flag(pa, "help") {
        print(argparse.help_text(parser))
        return
    }

    val names = argparse.positionals(pa)
    if names.len() == 0 {
        print(argparse.help_text(parser))
        process.exit(2)
    }

    var want_lines = argparse.has_flag(pa, "lines")
    var want_words = argparse.has_flag(pa, "words")
    var want_bytes = argparse.has_flag(pa, "bytes")
    if !want_lines && !want_words && !want_bytes {
        want_lines = true
        want_words = true
    }

    val label = argparse.get_option(parser, pa, "label")
    var i: usize = 0
    while i < names.len() {
        val name = names.get(i)
        if !p.is_absolute(name.as_str()) {
            print("error: cli_tool takes absolute paths (this language has no cwd accessor)")
            process.exit(2)
        }
        measure(name.as_str(), label.as_str(), want_lines, want_words, want_bytes)
        i += 1
    }
}

// `process.args()` includes `argv[0]`, the program's own path, exactly as a C
// program sees it, so a tool that parses its arguments drops the first entry.
// Without this, `./cli_tool file.txt` would treat `./cli_tool` as a file to read.
fun without_program_name(argv: &List<String>).R: List<String> {
    var out: List<String> = List.empty()
    var i: usize = 1
    while i < argv.len() {
        out.push(argv.get(i).clone())
        i += 1
    }
    return out
}

fun main() {
    var parser = argparse.new("wc")
    argparse.add_flag(parser, "lines", "print the line count")
    argparse.add_flag(parser, "words", "print the word count")
    argparse.add_flag(parser, "bytes", "print the byte count")
    argparse.add_flag(parser, "help", "print this help and exit")
    argparse.add_option(parser, "label", "counts", "a label in front of each line")

    val argv = without_program_name(process.args())
    val parsed = argparse.parse(&parser, argv)
    if let Err(e) = parsed {
        print(argparse.err_message(e))
        process.exit(2)
    }

    if let Ok(pa) = parsed {
        run(&parser, pa)
    }
}
```

## Run it

`kelpc run` takes no arguments, so arguments mean building first (or using a
project, where `coral run -- <args>` forwards them):

```sh
kelpc build cli_tool.kp -o cli_tool
./cli_tool --label counted /absolute/path/to/input.txt
./cli_tool --help
```

## Output

```
counted input.txt lines=3 words=11
```

```
usage: wc [flags] [options] [args]

flags:
  --lines	print the line count
  --words	print the word count
  --bytes	print the byte count
  --help	print this help and exit

options:
  --label=<value> (default: counts)	a label in front of each line
```

## What to take from it

- **`process.args()` includes `argv[0]`.** Every command line tool here drops it
  first; forgetting this is a trap that shows up as "it tried to read itself".
- **A flag and an option are different things,** and the parser does not guess:
  `--lines` never takes a value, `--label` always does. `--help` had to become a
  declared flag, because an undeclared `--name` is an error rather than a help
  request.
- **`get_option` returns an owned `String`** because the value can come from the
  arguments or from the declared default, and a borrow-returning function may only
  derive from its first reference parameter.
- **`get_option` panics on a name that was never declared.** That is a caller bug,
  not user input, and the program should not try to catch it.
- **Flags are additive and free**: `want_lines` starts as the flag's value, and
  only if none of the three are set does the tool default to lines and words.
- **Exit codes come from `process.exit`,** and 2 says "you called me wrong" while
  `panic` says "something is broken". Both are non-zero.

## See also

- [`argparse`](../libraries/argparse.md) for the full surface and the help format
- [`std/process`](../stdlib/process.md) for `args`, `spawn` and `exit`
- [wordcount](wordcount.md), which is this tool without a command line
