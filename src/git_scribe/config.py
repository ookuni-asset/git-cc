"""Configuration loading and merging."""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_FILENAME = ".gitscribe.toml"


@dataclass
class ScopeMapping:
    prefix: str
    scope: str


@dataclass
class Config:
    rules_search: list[str] = field(default_factory=list)
    llm_command: str = "claude"
    llm_timeout_sec: int = 60
    llm_required: bool = False
    commit_trailer: str = ""
    push_enabled: bool = True
    require_gh: bool = False
    fallback_lang: str = "ja"
    scope_mappings: list[ScopeMapping] = field(default_factory=list)
    type_docs_globs: list[str] = field(default_factory=list)
    type_ci_globs: list[str] = field(default_factory=list)
    type_test_globs: list[str] = field(default_factory=list)
    type_build_globs: list[str] = field(default_factory=list)
    type_fallback: str = "chore"


def load(repo_root: Path | None = None, explicit: Path | None = None) -> Config:
    bundled = _load_toml(_bundled_default_path())
    user = _load_toml(_user_config_path())
    repo: dict[str, Any] = {}
    if explicit is not None:
        repo = _load_toml(explicit)
    elif repo_root is not None:
        for candidate in (repo_root / CONFIG_FILENAME, repo_root / ".gitscribe" / "config.toml"):
            if candidate.exists():
                repo = _load_toml(candidate)
                break

    merged = _merge(bundled, user, repo)
    return _to_config(merged)


def _bundled_default_path() -> Path:
    return Path(__file__).parent / "templates" / "default-config.toml"


def _user_config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "git-scribe" / "config.toml"


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def _merge(*layers: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for layer in layers:
        _deep_update(result, layer)
    return result


def _deep_update(dst: dict[str, Any], src: dict[str, Any]) -> None:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_update(dst[k], v)
        else:
            dst[k] = v


def _to_config(d: dict[str, Any]) -> Config:
    rules = d.get("rules") or {}
    llm = d.get("llm") or {}
    commit = d.get("commit") or {}
    push = d.get("push") or {}
    lang = d.get("language") or {}
    scope = d.get("scope") or {}
    typ = d.get("type") or {}

    mappings = [
        ScopeMapping(prefix=str(m["prefix"]), scope=str(m["scope"]))
        for m in (scope.get("mappings") or [])
        if isinstance(m, dict) and "prefix" in m and "scope" in m
    ]

    env_cmd = os.environ.get("GIT_SCRIBE_LLM_COMMAND")
    env_timeout = os.environ.get("GIT_SCRIBE_LLM_TIMEOUT_SEC")

    return Config(
        rules_search=list(rules.get("search") or []),
        llm_command=env_cmd or str(llm.get("command") or "claude"),
        llm_timeout_sec=int(env_timeout) if env_timeout else int(llm.get("timeout_sec") or 60),
        llm_required=bool(llm.get("required", False)),
        commit_trailer=str(commit.get("trailer") or ""),
        push_enabled=bool(push.get("enabled", True)),
        require_gh=bool(push.get("require_gh", False)),
        fallback_lang=str(lang.get("fallback_lang") or "ja"),
        scope_mappings=mappings,
        type_docs_globs=list(typ.get("docs_globs") or []),
        type_ci_globs=list(typ.get("ci_globs") or []),
        type_test_globs=list(typ.get("test_globs") or []),
        type_build_globs=list(typ.get("build_globs") or []),
        type_fallback=str(typ.get("fallback") or "chore"),
    )
