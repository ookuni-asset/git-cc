# git-cc

AI を活用した Conventional Commits 用 CLI。Git の差分からコミットメッセージを生成し、`$EDITOR` でレビューしたあと、commit と push まで 1 コマンドで実行します。

> English: [README.md](README.md)

## このツールの目的

git-cc は、Git を使う上で最も繰り返しが多い「整った形式のコミットメッセージを書く」作業を自動化します。作業ツリーの変更を読み取り、LLM（または失敗時のローカルヒューリスティック）に **プロジェクト固有の規約に従った** Conventional Commits メッセージを下書きさせ、`$EDITOR` で確認・編集できるようにし、形式を検証してから commit と push を実行します。

設計上の 2 つの柱:

- **プログラミング言語非依存** — Python / PHP / TypeScript / Go / Rust など、どの言語のプロジェクトでも使えます。プロジェクト固有の挙動（スコープのマッピング、type 推定の glob、コミット規約）はすべて `.gitcc.toml` に書き、ツール本体のソースには持たせません。
- **LLM 非依存** — LLM は外部 CLI コマンドとして呼び出します。既定は `claude` ですが、`cursor` / `codex` / `llm` / `ollama` など、設定 1 行で差し替え可能です。

## 動作の流れ

`git cc` を実行すると、以下のステップを順に実行します:

1. **変更の収集** — staged / unstaged / 未追跡ファイル（`--prefer-staged` で staged のみに絞れる）
2. **プロンプトの組み立て** — コミット規約 + 変更ファイル一覧 + `diff --stat` + 完全な patch を結合
3. **LLM の呼び出し** — 設定した CLI（既定 `claude`）を実行。失敗時はローカルヒューリスティックにフォールバック（`[llm].required = true` の場合を除く）
4. **`$EDITOR` の起動** — 人間によるレビュー用（`GIT_EDITOR` → `VISUAL` → `EDITOR` → `vi` の順で選択）
5. **検証** — 1 行目が Conventional Commits 形式に合致するか確認
6. **commit と push** — `git commit -F` 実行後に `git push`

---

## 1. インストール

[uv](https://docs.astral.sh/uv/) がまだ無い場合は先にインストールします:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

その後、配布された `.whl` ファイルから git-cc をインストールします:

```bash
uv tool install git_cc-0.1.0-py3-none-any.whl
```

インストール後、`git-cc` と `git cc` の両方が使えます（git は `PATH` 上の `git-*` バイナリを自動検出します）。

環境確認:

```bash
git cc doctor
```

### アップデート

新しい `.whl` ファイルで再インストールします:

```bash
uv tool install --reinstall git_cc-<version>-py3-none-any.whl
```

---

## 2. 使い方

`git cc` は `git` 本体と同じく、**一度インストールすれば、あとはコミット対象のリポジトリに `cd` してから使う**ツールです。プロジェクト固有の設定はそのリポジトリの `.gitcc.toml` に、全プロジェクト共通の個人デフォルトは `~/.config/git-cc/config.toml` に書けます。

### クイックスタート

```bash
cd your-project
git cc init           # .gitcc.toml と COMMIT_GUIDELINES.md を作成
git add -A
git cc                # 生成 → レビュー → commit → push
```

### コマンド一覧

| コマンド / フラグ | 動作 |
|---|---|
| `git cc` | 生成 → レビュー → commit → push（staged が必要） |
| `git cc -a` | `git add -A` で全変更をステージしてからメインフローを実行 |
| `git cc --issue 123` | subject に `#123` を付与 |
| `git cc --no-push` | commit のみ。push しない |
| `git cc --no-llm` | LLM をスキップしてヒューリスティックのみで生成 |
| `git cc --dry-run` | メッセージを表示するだけで commit しない |
| `git cc --lang ja` | この実行だけ出力言語を上書き |
| `git cc --llm-command "cursor agent --print {prompt}"` | この実行だけ LLM バックエンドを上書き |
| `git cc print` | 生成して表示するだけ。commit しない |
| `git cc init` | `.gitcc.toml` と `COMMIT_GUIDELINES.md` を作成 |
| `git cc init --cursor` | Cursor 用ルール / Skill ファイルも追加 |
| `git cc config` | 解決後の設定を表示（デバッグ用） |
| `git cc doctor` | git / LLM / 設定の準備状況をチェック |

---

## 3. 設定

プロジェクト固有の挙動はリポジトリ直下の `.gitcc.toml` で制御します。`git cc init` でコメント付きの雛形が生成されます。

### LLM の選択（`[llm]`）

git-cc は外部 CLI を呼び出します。既定は `claude`:

```toml
[llm]
command     = "claude"        # Claude（既定）
timeout_sec = 60
required    = false
```

**Cursor に切り替える場合:**

```toml
[llm]
command = "cursor agent --print {prompt}"
```

コマンド文字列に `{prompt}` が含まれていれば置換され、そうでなければプロンプトは stdin に渡されます。

実行時の上書きは環境変数で:

```bash
GIT_CC_LLM_COMMAND="cursor agent --print {prompt}" git cc
GIT_CC_LLM_TIMEOUT_SEC=120                         git cc
```

### コミット規約ファイルの指定（`[rules]`）

```toml
[rules]
# 最初に見つかったファイルが LLM プロンプトにそのまま注入されます。
search = [
  ".cursor/rules/git-commit.mdc",
  ".gitcc/rules.md",
  "COMMIT_GUIDELINES.md",
]
```

候補のいずれもリポジトリに無い場合は、git-cc 同梱の `default-rules.md` にフォールバックします。

### 出力言語（`[language]`）

```toml
[language]
output_lang = "en"   # "ja" や、その他 LLM が解釈できる任意のコード
```

実行時の上書きは `git cc --lang ja`。

### ヒューリスティックフォールバックの調整（`[scope]` / `[type]`）

LLM が利用不可のとき、または `--no-llm` 指定時にのみ使われます:

```toml
[scope]
mappings = [
  { prefix = "src/api/", scope = "api" },
  { prefix = "docs/",    scope = "docs" },
]

[type]
docs_globs  = ["docs/**", "**/*.md"]
ci_globs    = [".github/**", ".gitlab-ci.yml"]
test_globs  = ["**/tests/**", "**/*.spec.*", "**/*.test.*"]
build_globs = ["package.json", "pyproject.toml", "go.mod", "Cargo.toml"]
fallback = "chore"
```

### push の挙動（`[push]`）

```toml
[push]
enabled    = true
require_gh = false
```

### 設定の階層

git-cc は設定を以下の順でマージします（後勝ち）:

1. **同梱デフォルト** — `templates/default-config.toml`
2. **ユーザ設定** — `~/.config/git-cc/config.toml`（または `$XDG_CONFIG_HOME/git-cc/config.toml`）
3. **プロジェクト設定** — リポジトリ直下の `.gitcc.toml`（または `--config <path>`）
4. **環境変数** — `GIT_CC_LLM_COMMAND`, `GIT_CC_LLM_TIMEOUT_SEC`
5. **CLI フラグ** — `--llm-command`, `--llm-timeout-sec`, `--lang`, `--llm-required` 等

`git cc config` で現在のリポジトリでの最終的な値を確認できます。

---

## ライセンス

MIT — 詳細は `LICENSE` を参照。
