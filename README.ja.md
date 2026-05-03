# git-scribe

AI を活用した Conventional Commits 用 CLI。Git の差分からコミットメッセージを生成し、`$EDITOR` でレビューしたあと、commit と push まで 1 コマンドで実行します。

> English: [README.md](README.md)

## このツールの目的

git-scribe は、Git を使う上で最も繰り返しが多い「整った形式のコミットメッセージを書く」作業を自動化します。作業ツリーの変更を読み取り、LLM（または失敗時のローカルヒューリスティック）に **プロジェクト固有の規約に従った** Conventional Commits メッセージを下書きさせ、`$EDITOR` で確認・編集できるようにし、形式を検証してから commit と push を実行します。

設計上の 2 つの柱:

- **プログラミング言語非依存** — Python / PHP / TypeScript / Go / Rust など、どの言語のプロジェクトでも使えます。プロジェクト固有の挙動（スコープのマッピング、type 推定の glob、コミット規約）はすべて `.gitscribe.toml` に書き、ツール本体のソースには持たせません。
- **LLM 非依存** — LLM は外部 CLI コマンドとして呼び出します。既定は `claude` ですが、`codex` / `llm` / `ollama` など、設定 1 行で差し替え可能です。

向いている用途: コミットタイトルを毎回手で書くのをやめたい / PR レビューで規約違反をいちいち指摘せずに Conventional Commits を統一したい / 自前のシェルラッパスクリプトを設定可能なツールに置き換えたい / 同じ作業を別の LLM バックエンド（ローカルモデル含む）で試したい、など。

## 動作の流れ

`git scribe` を実行すると、以下のステップを順に実行します:

1. **変更の収集** — staged / unstaged / 未追跡ファイル（`--prefer-staged` で staged のみに絞れる）
2. **プロンプトの組み立て** — コミット規約 + 変更ファイル一覧 + `diff --stat` + 完全な patch を結合
3. **LLM の呼び出し** — 設定した CLI（既定 `claude`）を実行。失敗時はローカルヒューリスティックにフォールバック（`[llm].required = true` の場合を除く）
4. **`$EDITOR` の起動** — 人間によるレビュー用（`GIT_EDITOR` → `VISUAL` → `EDITOR` → `vi` の順で選択）
5. **検証** — 1 行目が Conventional Commits 形式に合致するか確認
6. **commit と push** — `git commit -F` 実行後に `git push`

---

## 1. インストール

[uv](https://docs.astral.sh/uv/) がまだ無い場合は、以下のワンライナーで uv の自動取得から git-scribe のインストールまで一気にやれます。**clone も Python も不要**:

```bash
curl -LsSf https://raw.githubusercontent.com/ookuni-asset/git-scribe/main/install.sh | bash
```

uv が既にあるなら、公開リポジトリの URL から直接インストールできます:

```bash
uv tool install --from "git+https://github.com/ookuni-asset/git-scribe.git" git-scribe
```

リポジトリを clone して `./install.sh` を実行する形でも同じ結果になります。

> Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` で uv をインストールしたあと、上記の `uv tool install` コマンドを実行してください。

インストール後、`git-scribe` と `git scribe` の両方が使えます（git は `PATH` 上の `git-*` バイナリを自動検出します）。

環境確認:

```bash
git scribe doctor
```

### アップデート

```bash
uv tool upgrade git-scribe
```

uv が GitHub から最新コミットを再取得して、その場でビルドし直します。clone やスクリプト実行は不要です。

---

## 2. 使い方

`git scribe` は `git` 本体と同じく、**一度インストールすれば、あとはコミット対象のリポジトリに `cd` してから使う**ツールです。内部で `git rev-parse --show-toplevel` を呼び、現在のリポジトリを自動検出します。プロジェクト固有の設定（LLM・ルール・スコープマッピング等）はそのリポジトリの `.gitscribe.toml` に、全プロジェクト共通の個人デフォルトは `~/.config/git-scribe/config.toml` に書けます。

### クイックスタート

```bash
cd your-project
git scribe init           # .gitscribe.toml と COMMIT_GUIDELINES.md を作成
git add -A
git scribe                # 生成 → レビュー → commit → push
```

### コマンド一覧

`git scribe`（サブコマンド省略時）はメインフロー（commit）を実行します。

| コマンド / フラグ | 動作 |
|---|---|
| `git scribe` | メインフローを実行 |
| `git scribe -a` | 生成前に `git add -A` で全変更をステージ |
| `git scribe --prefer-staged` | staged 済みの変更がある場合、それだけを使って生成（unstaged / 未追跡は無視） |
| `git scribe --issue 123` | subject に `#123` を付与 |
| `git scribe --no-push` | commit のみ。push しない |
| `git scribe --no-llm` | LLM をスキップしてヒューリスティックのみで生成 |
| `git scribe --dry-run` | メッセージを表示するだけで commit しない |
| `git scribe --lang ja` | この実行だけ出力言語を上書き |
| `git scribe --llm-command "ollama run qwen2.5-coder:7b"` | この実行だけ LLM バックエンドを上書き |
| `git scribe print` | 生成して表示するだけ。commit しない |
| `git scribe init` | `.gitscribe.toml` と `COMMIT_GUIDELINES.md` を作成 |
| `git scribe init --cursor` | Cursor 用ルール / Skill ファイルも追加 |
| `git scribe config` | 解決後の設定を表示（デバッグ用） |
| `git scribe doctor` | git / LLM / 設定の準備状況をチェック |

---

## 3. 設定

プロジェクト固有の挙動はリポジトリ直下の `.gitscribe.toml` で制御します。`git scribe init` でコメント付きの雛形が生成されます。

### LLM の選択（`[llm]`）

git-scribe は外部 CLI を呼び出します。既定は `claude`:

```toml
[llm]
command     = "claude"        # 例: "codex exec {prompt}", "llm -m gpt-4o", "ollama run qwen2.5-coder:7b"
timeout_sec = 60
required    = false           # true の場合、LLM 失敗時にエラー終了（ヒューリスティックにフォールバックしない）
```

コマンド文字列に `{prompt}` が含まれていれば置換され、そうでなければプロンプトは stdin に渡されます。

実行時の上書きは環境変数で:

```bash
GIT_SCRIBE_LLM_COMMAND="ollama run qwen2.5-coder:7b" git scribe
GIT_SCRIBE_LLM_TIMEOUT_SEC=120                       git scribe
```

### コミット規約ファイルの指定（`[rules]`）

```toml
[rules]
# 最初に見つかったファイルが LLM プロンプトにそのまま注入されます。
search = [
  ".cursor/rules/git-commit.mdc",
  ".gitscribe/rules.md",
  "COMMIT_GUIDELINES.md",
]
```

候補のいずれもリポジトリに無い場合は、git-scribe 同梱の `default-rules.md` にフォールバックします。

### 出力言語（`[language]`）

```toml
[language]
output_lang = "en"   # "ja" や、その他 LLM が解釈できる任意のコード
```

実行時の上書きは `git scribe --lang ja`。

### ヒューリスティックフォールバックの調整（`[scope]` / `[type]`）

LLM が利用不可のとき、または `--no-llm` 指定時にのみ使われます:

```toml
[scope]
# ディレクトリ prefix → スコープ名。先勝ち。
mappings = [
  { prefix = "src/api/", scope = "api" },
  { prefix = "docs/",    scope = "docs" },
]

[type]
# glob ベースの type 推定（ヒューリスティック生成器用）。
docs_globs  = ["docs/**", "**/*.md"]
ci_globs    = [".github/**", ".gitlab-ci.yml"]
test_globs  = ["**/tests/**", "**/*.spec.*", "**/*.test.*"]
build_globs = [
  "package.json", "pnpm-lock.yaml",
  "composer.json", "composer.lock",
  "pyproject.toml", "uv.lock",
  "go.mod", "Cargo.toml", "Gemfile",
]
fallback = "chore"
```

### push の挙動（`[push]`）

```toml
[push]
enabled    = true     # false にすると `git scribe` は既定で commit のみになります
require_gh = false    # true なら push 前に `gh repo set-default / auth status / repo sync` を実行
```

### 設定の階層

git-scribe は設定を以下の順でマージします（後勝ち）:

1. **同梱デフォルト** — `templates/default-config.toml`（既定値の単一の真実の所在）
2. **ユーザ設定** — `~/.config/git-scribe/config.toml`（または `$XDG_CONFIG_HOME/git-scribe/config.toml`）
3. **プロジェクト設定** — リポジトリ直下の `.gitscribe.toml`（または `--config <path>`）
4. **環境変数** — `GIT_SCRIBE_LLM_COMMAND`, `GIT_SCRIBE_LLM_TIMEOUT_SEC`
5. **CLI フラグ** — `--llm-command`, `--llm-timeout-sec`, `--lang`, `--llm-required` 等

`git scribe config` で現在のリポジトリでの最終的な値を確認できます。

---

## ライセンス

MIT — 詳細は `LICENSE` を参照。
