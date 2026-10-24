---
title: "Build something"
description: "Put the tutorial together into a command-line word counter: it reads its arguments, reads a file, counts words in a Map, sorts them, and exits with a status code on a usage error."
isPublished: true
tags: "tutorial, getting-started, cli"
---
**You will learn:** how the chapters combine into a small command-line tool that
reads a file named on its command line, and how to build it into an executable.

The program counts the words in a text file and prints each word with its count,
in alphabetical order. It uses a `Map` from [Collections](/tutorial/08-collections),
loops from [Control flow](/tutorial/03-control-flow), and text from
[Text](/tutorial/04-text). It also uses the file and process modules, whose
powers are described in [Modules and capabilities](/tutorial/11-projects). The entry
file of a program holds every capability by default, so this one needs no grant.

## The program

Create `wordcount.kp`:

```kelp
impl "std/fs"
impl "std/process"
impl "std/str"

// Count the words in a text file and print each one with its count, sorted.
// Words are separated by spaces, and case is ignored.

fun count_words(path: &str, counts: mut Map<String, i64>) {
    val lines = fs.read_lines(path)
    var i: int = 0
    while i < lines.len() {
        val words = str.split(lines.get(i).as_str(), " ")
        var j: int = 0
        while j < words.len() {
            val word = str.to_lower(words.get(j).as_str())
            if !word.is_empty() {
                if counts.has(key = word.as_str()) {
                    val seen = counts.get(key = word.as_str())
                    counts.insert(key = word.as_str(), v = seen + 1)
                } else {
                    counts.insert(key = word.as_str(), v = 1)
                }
            }
            j += 1
        }
        i += 1
    }
}

fun main() {
    val argv = process.args()
    if argv.len() < 2 {
        print("usage: wordcount <file>")
        process.exit(2)
    }

    var counts: Map<String, i64> = Map.new()
    count_words(argv.get(1).as_str(), counts)

    var words = counts.keys()
    words.sort()
    var k: int = 0
    while k < words.len() {
        val w = words.get(k)
        print("${w} ${counts.get(key = w.as_str())}")
        k += 1
    }
}
```

## How it works

- `process.args()` returns the command-line arguments as a list. Element 0 is the
  program's own name, so the file name is element 1. The `argv.len() < 2` check
  catches a missing file name.
- `count_words` takes the map as a `mut` parameter. It changes the map the caller
  owns, so `main` sees the counts afterwards without any return value.
- `str.split` breaks each line at spaces. An empty piece, which happens with two
  spaces in a row, is skipped by the `is_empty` check.
- `keys()` returns the words, and `sort()` puts them in order. The counts are
  read back with `get`, which takes the key as a `str`.

## Build it and run it

Create a small input file:

```sh
printf 'the cat sat\nthe dog sat\nThe end\n' > words.txt
```

Build the executable, then run it with the file name:

```sh
kelpc build wordcount.kp -o wordcount
./wordcount words.txt
```

```text
cat 1
dog 1
end 1
sat 2
the 3
```

With no file name, the tool prints its usage and exits with status 2, which is the
convention for a usage error:

```sh
./wordcount
echo "exit status $?"
```

```text
usage: wordcount <file>
exit status 2
```

If the file does not exist, `fs.read_lines` panics and the program exits with
status 1:

```text
./wordcount nope.txt
panic: fs.read: cannot open file
  errno 2: No such file or directory
```

A tool that should report a missing file politely would use the fallible
`fs.try_read_text`, which returns a `Result`. The
[first real tool](/getting-started/first-tool) page writes that version step by
step.

## Try it

1. Add a line to `words.txt` with a word in capital letters. Does the count
   change? Why?
2. Print only the words that appear more than once. Use an `if` inside the final
   loop, with `counts.get(key = w.as_str()) > 1`.
3. Change the separator in `str.split` from `" "` to `","`, and create a comma
   separated file. What happens to a line that has no commas?

## Where to go next

- [Language reference](/language) for every rule the chapters touched.
- [Standard library](/stdlib) for the modules this program imports, and the rest.
- [Examples](/examples) for longer programs built the same way, each with its
  full source and output.
- [Install](/getting-started/install) and [Projects](/getting-started/projects)
  when you want to split a tool into several files and add dependencies.
