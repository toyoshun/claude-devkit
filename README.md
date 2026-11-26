# devkit

どのリポジトリでも使える、pstack まわりの共通の道具をまとめた Claude Code のプラグイン。

## 中身

| 場所 | 役目 |
| --- | --- |
| `skills/pstack-route/` | 作業の種類から pstack の入口と、作業後に続けて回すスキルを選ぶ |
| `scripts/pstack_usage.py` | Stop フック。使った pstack のスキルを記録し、抜けていれば知らせる。`report` で一覧 |
| `scripts/edit_check.py` | PostToolUse フック。編集した1ファイルを検査する。`*.py` は ruff。リポジトリごとの検査は `.claude/devkit.json` |
| `scripts/bootstrap.sh` | SessionStart フック。`poteto-mode-auto` の写しと、`~/.claude/rules/` のルールをそろえる。考え方のルールは毎回 devkit の版で置き直し、モデル設定と Codex のルールは既存を上書きしない |
| `rules/` | どの作業にも効く開発の考え方（`pstack-principles.md`、pstack の原則を短くしたもの）、pstack のモデル設定、Codex を使うルール（`codex` があるときだけ置く） |
| `templates/project-instructions.md` | 新しい Claude プロジェクトの指示に貼る文面 |
| `install.sh` | 新しい環境に入れる |

## 入れ方

Mac では、チェックアウトして実行する。

```bash
git clone https://github.com/toyoshun/claude-devkit ~/dev/claude-devkit
bash ~/dev/claude-devkit/install.sh
```

`~/.claude/skills/devkit` にリンクが張られ、プラグインとして読み込まれる。`--copy` を付けるとコピーで入れる。pstack が未導入で `claude` コマンドがあれば、pstack も入れる。

クラウド環境では、環境のセットアップスクリプトに1行足す。

```bash
git clone --depth 1 https://github.com/toyoshun/claude-devkit /opt/claude-devkit && bash /opt/claude-devkit/install.sh
```

何度走らせても同じ結果になる。Mac ではリンクなので、`git pull` すれば次のセッションから新しい版になる。

新しい Claude プロジェクトを作ったら、`templates/project-instructions.md` の文面をプロジェクトの指示に貼る。

## リポジトリごとの足し方

- `.claude/pstack-route.md`: そのリポジトリだけの振り分けの行と、作業後に回すスキルの行。`pstack-route` スキルが先に読み、表より優先する。
- `.claude/devkit.json`: 編集後の検査を足す。一致したファイルの相対パスを末尾に付けて、リポジトリの根から実行する。`python3` と書くと、`.venv/bin/python` があればそちらを使う。

```json
{
  "edit_checks": [
    {"glob": "docs/*.md", "run": ["python3", "tools/lint.py"]}
  ]
}
```

検査は出力があれば exit 2 で Claude に知らせる。作業は止めない。

## リポジトリに残すもの

記事・文章の検査・ドメインのスキルなど、そのリポジトリだけのものは、リポジトリに置く。devkit に入れるのは、どのリポジトリでも同じに使えるものだけ。

## 記録

クラウドでは `/mnt/project-files/pstack-usage/`、Mac では `~/.claude/pstack-usage/` に、1セッション1ファイルで残る。`PSTACK_USAGE_DIR` で置き場を変えられる。

```bash
python3 ~/.claude/skills/devkit/scripts/pstack_usage.py report
```
