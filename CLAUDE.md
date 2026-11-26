# claude-devkit

どのリポジトリでも使う Claude Code の共通の道具（pstack の振り分け、使用記録、編集直後の検査、開発の考え方）を入れるプラグイン。中身と入れ方は `README.md`。

## 決まり

- ここには、どのリポジトリでも同じに使えるものだけを入れる。特定のリポジトリだけのもの（記事、ドメインのスキル、そのリポジトリの検査）は、そのリポジトリの `.claude/pstack-route.md` と `.claude/devkit.json` に置く。
- フックのスクリプト（`scripts/*.py`）は標準ライブラリだけで書き、Python 3.9 でも動く書き方にする。フックは Mac の system python3 で動くため。
- フックは失敗してもセッションを止めない。
- `install.sh` と `scripts/bootstrap.sh` は何度走らせても同じ結果にする。macOS の bash 3.2 で動く書き方にする。
- 秘密情報、個人情報、特定のリポジトリの運用データを入れない。このリポジトリは公開されている。

## 確認

```bash
uv sync --frozen
bash -n install.sh scripts/bootstrap.sh
uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest -q
```
