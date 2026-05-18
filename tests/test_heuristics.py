from git_cc.changes import Changes
from git_cc.config import Config, ScopeMapping
from git_cc.heuristics import generate, guess_scope, guess_type, match


def _cfg(**overrides) -> Config:
    base = Config(
        scope_mappings=[
            ScopeMapping(prefix="src/api/", scope="api"),
            ScopeMapping(prefix="docs/", scope="docs"),
        ],
        type_docs_globs=["docs/**", "**/*.md"],
        type_ci_globs=[".github/**"],
        type_test_globs=["**/tests/**", "**/*.test.*"],
        type_build_globs=["package.json", "composer.json", "pyproject.toml"],
        type_fallback="chore",
        output_lang="en",
    )
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


def test_glob_match_double_star():
    assert match("src/api/tests/test_x.py", "**/tests/**")
    assert match("README.md", "**/*.md")
    assert match("docs/foo.md", "**/*.md")
    assert match("a/b/c/foo.spec.ts", "**/*.spec.*")
    assert not match("src/api/main.py", "**/tests/**")


def test_glob_match_simple():
    assert match("package.json", "package.json")
    assert match("docs/foo.md", "docs/**")
    assert not match("docsx/foo.md", "docs/**")


def test_scope_first_match():
    cfg = _cfg()
    assert guess_scope(["src/api/foo.py"], cfg) == "api"
    assert guess_scope(["docs/readme.md"], cfg) == "docs"
    assert guess_scope(["other/x"], cfg) is None


def test_type_docs_when_all_docs():
    cfg = _cfg()
    assert guess_type(["docs/foo.md", "README.md"], cfg) == "docs"


def test_type_not_docs_when_mixed():
    cfg = _cfg()
    assert guess_type(["docs/foo.md", "src/api/main.py"], cfg) != "docs"


def test_type_ci():
    cfg = _cfg()
    assert guess_type([".github/workflows/ci.yml"], cfg) == "ci"


def test_type_build_lockfile_language_agnostic():
    cfg = _cfg()
    assert guess_type(["package.json"], cfg) == "build"
    assert guess_type(["composer.json"], cfg) == "build"
    assert guess_type(["pyproject.toml"], cfg) == "build"


def test_type_test_glob():
    cfg = _cfg()
    assert guess_type(["src/api/tests/test_x.py"], cfg) == "test"
    assert guess_type(["app/foo.test.ts"], cfg) == "test"


def test_type_fallback():
    cfg = _cfg()
    assert guess_type(["src/api/main.py"], cfg) == "chore"


def test_generate_includes_issue_and_scope():
    cfg = _cfg()
    ch = Changes(staged=False, files=["src/api/x.py"], diff_stat="", name_status=[])
    msg = generate(ch, cfg, issue="#42")
    assert msg.startswith("chore(api): ")
    assert "#42" in msg


def test_generate_lang_ja_default_subject():
    cfg = _cfg(output_lang="ja")
    ch = Changes(staged=False, files=["src/api/x.py"], diff_stat="", name_status=[])
    msg = generate(ch, cfg, issue=None)
    assert "変更を反映" in msg


def test_generate_lang_en_default_subject():
    cfg = _cfg(output_lang="en")
    ch = Changes(staged=False, files=["src/api/x.py"], diff_stat="", name_status=[])
    msg = generate(ch, cfg, issue=None)
    assert "Update" in msg
