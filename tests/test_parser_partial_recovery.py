"""GH #95 fast-follow: graceful partial-parse recovery across all parsers.

The TypeScript parser was fixed first (test_typescript_parser.py). The same
`has_error` early-bail existed in base/python/java/php/objc — one unsupported
or malformed construct dropped the whole file to `symbols: []`. tree-sitter
error recovery is local, so a valid declaration followed by a broken tail must
still yield the valid symbol, flagged `partial`.
"""

import pytest

from codeindex.parser import parse_file

# (extension, valid source whose symbol must survive, expected symbol substring,
#  garbage tail that makes root_node.has_error True)
CASES = [
    ("py", "def good_func():\n    return 1\n", "good_func", "\n!!! not python @#$ %%%\n"),
    (
        "java",
        "class Good {\n    void m() {}\n}\n",
        "Good",
        "\n@@@ not java ### }}}{{{\n",
    ),
    (
        "php",
        "<?php\nfunction goodFn() { return 1; }\n",
        "goodFn",
        "\nfunction broken( { @#$ \n",
    ),
    # swift uses BaseLanguageParser.parse() (no override) — covers base.py
    (
        "swift",
        "func goodFunc() -> Int { return 1 }\n",
        "goodFunc",
        "\nfunc broken( { @#$ %%%\n",
    ),
    # objc overrides parse() with source preprocessing
    (
        "m",
        "@interface Good : NSObject\n- (void)doThing;\n@end\n",
        "Good",
        "\n@@@ not objc ### }}}{{{\n",
    ),
]


@pytest.mark.parametrize("ext,valid,symbol,garbage", CASES, ids=[c[0] for c in CASES])
def test_partial_recovery_keeps_valid_symbol(tmp_path, ext, valid, symbol, garbage):
    f = tmp_path / f"sample.{ext}"
    f.write_text(valid + garbage)
    r = parse_file(f)

    names = " ".join(s.name for s in r.symbols)
    assert symbol in names, f"{ext}: expected '{symbol}' recovered, got {names!r}"
    assert r.error is None, f"{ext}: partial parse must not set a hard error"
    assert r.partial is True, f"{ext}: tree had errors → partial must be True"


@pytest.mark.parametrize("ext,valid,symbol", [(c[0], c[1], c[2]) for c in CASES], ids=[c[0] for c in CASES])
def test_clean_file_not_partial(tmp_path, ext, valid, symbol):
    f = tmp_path / f"clean.{ext}"
    f.write_text(valid)
    r = parse_file(f)
    assert r.error is None
    assert r.partial is False
    assert symbol in " ".join(s.name for s in r.symbols)
