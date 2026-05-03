"""Configuration loading and merging.

`templates/default-config.toml` is the single source of truth for
user-facing defaults. The dataclass field defaults below are minimal
placeholders so `Config()` is constructible — they are not authoritative.
"""
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
    llm_command: str = ""
    llm_timeout_sec: int = 0
    llm_required: bool = False
    commit_trailer: str = ""
    push_enabled: bool = True
    require_gh: bool = False
    fallback_lang: str = ""
    scope_mappings: list[ScopeMapping] = field(default_factory=list)
    type_docs_globs: list[str] = field(default_factory=list)
    type_ci_globs: list[str] = field(default_factory=list)
    type_test_globs: list[str] = field(default_factory=list)
    type_build_globs: list[str] = field(default_factory=list)
    type_fallback: str = ""


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
    cfg = Config()

    rules = d.get("rules") or {}
    llm = d.get("llm") or {}
    commit = d.get("commit") or {}
    push = d.get("push") or {}
    lang = d.get("language") or {}
    scope = d.get("scope") or {}
    typ = d.get("type") or {}

    if "search" in rules:
        cfg.rules_search = list(rules["search"])
    if "command" in llm:
        cfg.llm_command = str(llm["command"])
    if "timeout_sec" in llm:
        cfg.llm_timeout_sec = int(llm["timeout_sec"])
    if "required" in llm:
        cfg.llm_required = bool(llm["required"])
    if "trailer" in commit:
        cfg.commit_trailer = str(commit["trailer"])
    if "enabled" in push:
        cfg.push_enabled = bool(push["enabled"])
    if "require_gh" in push:
        cfg.require_gh = bool(push["require_gh"])
    if "fallback_lang" in lang:
        cfg.fallback_lang = str(lang["fallback_lang"])
    if "mappings" in scope:
        cfg.scope_mappings = [
            ScopeMapping(prefix=str(m["prefix"]), scope=str(m["scope"]))
            for m in scope["mappings"]
            if isinstance(m, dict) and "prefix" in m and "scope" in m
        ]
    if "docs_globs" in typ:
        cfg.type_docs_globs = list(typ["docs_globs"])
    if "ci_globs" in typ:
        cfg.type_ci_globs = list(typ["ci_globs"])
    if "test_globs" in typ:
        cfg.type_test_globs = list(typ["test_globs"])
    if "build_globs" in typ:
        cfg.type_build_globs = list(typ["build_globs"])
    if "fallback" in typ:
        cfg.type_fallback = str(typ["fallback"])

    env_cmd = os.environ.get("GIT_SCRIBE_LLM_COMMAND")
    if env_cmd:
        cfg.llm_command = env_cmd
    env_timeout = os.environ.get("GIT_SCRIBE_LLM_TIMEOUT_SEC")
    if env_timeout:
        cfg.llm_timeout_sec = int(env_timeout)

    return cfg
