# Kelp documentation — build and deploy notes
#
# The site is MkDocs Material. Everything under docs/ is markdown; mkdocs.yml
# owns the navigation tree; hooks/kelp_lexer.py teaches Pygments the `kelp` fence
# language so Kelp code blocks are highlighted.
#
#   python3 -m venv .venv
#   .venv/bin/pip install mkdocs-material
#   .venv/bin/mkdocs serve            # http://127.0.0.1:8000
#   .venv/bin/mkdocs build --strict    # --strict fails on a broken link
#
# On homelabone (thinkbox) the site is built by the `kelp-wiki-build` systemd
# unit and served by nginx at https://homelabone.xenoo.dev/kelp/.
#
# Page conventions:
#   * one page per topic, chapters as directories, chapter index as index.md
#   * "See also" at the end of a page links only to pages that exist
#   * a claim about the language cites the plan document it came from, e.g.
#     `syntax.md §6.3`, linked to
#     https://homelabone.xenoo.dev/gittea/Juniper/kelp/src/branch/main/plan/syntax.md
