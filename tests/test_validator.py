from git_cc.validator import validate


def test_accepts_simple():
    ok, _ = validate("feat: add thing\n")
    assert ok


def test_accepts_with_scope():
    ok, _ = validate("feat(api): add health endpoint\n")
    assert ok


def test_accepts_with_issue():
    ok, _ = validate("fix(web): correct typo #42\n")
    assert ok


def test_accepts_breaking_marker():
    ok, _ = validate("feat(api)!: remove deprecated route\n")
    assert ok


def test_rejects_empty():
    ok, _ = validate("")
    assert not ok


def test_rejects_unknown_type():
    ok, _ = validate("foo: bar\n")
    assert not ok


def test_rejects_trailing_period():
    ok, _ = validate("feat: do something.\n")
    assert not ok


def test_rejects_japanese_period():
    ok, _ = validate("feat: 何かする。\n")
    assert not ok


def test_validates_only_first_line():
    msg = "feat(api): add health endpoint\n\n- some body line.\n"
    ok, _ = validate(msg)
    assert ok
