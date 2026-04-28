from git_scribe.changes import Changes
from git_scribe.prompt import build, resolve_rules_text
from git_scribe.config import Config


def test_build_includes_rules_files_and_diff():
    ch = Changes(
        staged=True,
        files=["a.py", "b.md"],
        diff_stat="files | 2 +-",
        name_status=[("M", "a.py")],
    )
    out = build(rules_text="RULES_HERE", changes=ch, issue="#10", patch="DIFF_HERE")
    assert "RULES_HERE" in out
    assert "- a.py" in out
    assert "- b.md" in out
    assert "DIFF_HERE" in out
    assert "issue: #10" in out
    assert "diff_source: staged" in out


def test_build_marks_unstaged():
    ch = Changes(staged=False, files=["a.py"], diff_stat="", name_status=[])
    out = build(rules_text="r", changes=ch, issue=None, patch="")
    assert "diff_source: mixed/unstaged" in out


def test_resolve_rules_uses_repo_file_when_present(tmp_path):
    rules = tmp_path / "COMMIT_GUIDELINES.md"
    rules.write_text("# project rules\n", encoding="utf-8")
    cfg = Config(rules_search=["COMMIT_GUIDELINES.md"])
    text = resolve_rules_text(tmp_path, cfg)
    assert "project rules" in text


def test_resolve_rules_falls_back_to_bundled(tmp_path):
    cfg = Config(rules_search=["nonexistent.md"])
    text = resolve_rules_text(tmp_path, cfg)
    assert "Git commit message rules" in text
