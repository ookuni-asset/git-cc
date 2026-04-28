import os

from git_scribe import config as cfg_mod


def test_load_default_only(tmp_path):
    cfg = cfg_mod.load(repo_root=tmp_path)
    assert cfg.type_fallback == "chore"
    assert "package.json" in cfg.type_build_globs
    assert "pyproject.toml" in cfg.type_build_globs
    assert "composer.json" in cfg.type_build_globs


def test_repo_overrides_default(tmp_path):
    (tmp_path / ".gitscribe.toml").write_text(
        '[llm]\ncommand = "codex"\ntimeout_sec = 30\n[type]\nfallback = "fix"\n',
        encoding="utf-8",
    )
    cfg = cfg_mod.load(repo_root=tmp_path)
    assert cfg.llm_command == "codex"
    assert cfg.llm_timeout_sec == 30
    assert cfg.type_fallback == "fix"
    # bundled defaults that weren't overridden persist
    assert "package.json" in cfg.type_build_globs


def test_explicit_path_wins(tmp_path):
    custom = tmp_path / "custom.toml"
    custom.write_text('[llm]\ncommand = "llm-cli"\n', encoding="utf-8")
    (tmp_path / ".gitscribe.toml").write_text(
        '[llm]\ncommand = "should-not-win"\n', encoding="utf-8"
    )
    cfg = cfg_mod.load(repo_root=tmp_path, explicit=custom)
    assert cfg.llm_command == "llm-cli"


def test_env_var_overrides_command(tmp_path, monkeypatch):
    (tmp_path / ".gitscribe.toml").write_text(
        '[llm]\ncommand = "claude"\n', encoding="utf-8"
    )
    monkeypatch.setenv("GIT_SCRIBE_LLM_COMMAND", "from-env")
    cfg = cfg_mod.load(repo_root=tmp_path)
    assert cfg.llm_command == "from-env"


def test_env_var_overrides_timeout(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_SCRIBE_LLM_TIMEOUT_SEC", "120")
    cfg = cfg_mod.load(repo_root=tmp_path)
    assert cfg.llm_timeout_sec == 120


def test_scope_mappings(tmp_path):
    (tmp_path / ".gitscribe.toml").write_text(
        '[scope]\nmappings = [\n  { prefix = "src/api/", scope = "api" },\n  { prefix = "docs/",    scope = "docs" },\n]\n',
        encoding="utf-8",
    )
    cfg = cfg_mod.load(repo_root=tmp_path)
    prefixes = [m.prefix for m in cfg.scope_mappings]
    scopes = [m.scope for m in cfg.scope_mappings]
    assert prefixes == ["src/api/", "docs/"]
    assert scopes == ["api", "docs"]
