"""Teach Pygments the `kelp` fence language.

Kelp is Rust-shaped (`datac`, `enum`, `fun`, `impl`, `val`, `var`, `mut`, `move`,
`when`), so this lexes as Rust with Kelp's own keywords promoted to keywords.

Pygments resolves a language name through its `LEXERS` mapping, whose entry names
an importable module, that module's `__all__`, and the lexer's *name*. mkdocs
loads a `hooks:` file without registering it in `sys.modules`, so the mapping is
pointed at a synthetic module built here rather than at this file.
"""

import sys
import types

from pygments.lexer import inherit
from pygments.lexers import RustLexer, _mapping
from pygments.token import Keyword

KELP_KEYWORDS = (
    r"\b(fun|datac|enum|impl|pd|const|val|var|mut|move|when|closure|as|with|caps)\b"
)


class KelpLexer(RustLexer):
    """Kelp source."""

    name = "Kelp"
    aliases = ["kelp"]
    filenames = ["*.kp"]
    mimetypes = ["text/x-kelp"]

    tokens = {
        "root": [
            (KELP_KEYWORDS, Keyword),
            inherit,
        ]
    }


_module = types.ModuleType("kelp_lexer")
_module.KelpLexer = KelpLexer
_module.__all__ = ["KelpLexer"]
sys.modules["kelp_lexer"] = _module

# Pygments caches a loaded lexer under `cls.name` and looks it up by this second
# element, so the two have to agree: it is "Kelp", not "KelpLexer".
_mapping.LEXERS["Kelp"] = ("kelp_lexer", "Kelp", ("kelp",), ("*.kp",), ("text/x-kelp",))
