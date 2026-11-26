---
name: pstack-route
description: 作業の種類から pstack の入口（poteto-mode の playbook か単独のスキル）を選び、作業の後に続けて回す pstack のスキルを決める。スレッドやタスクの最初、作業の種類が変わったとき、Stop フックに pstack の連鎖が足りないと言われたときに使う。
---

# pstack の振り分けと連鎖

pstack は `~/.claude/plugins/cache/cursor-plugins/pstack/<最新の版>/` にある（以下 `<pstack>`）。
pstack のスキルは Skill ツールから呼べないものが多い。ファイルを **Read ツールで** 読んで従う。読んだ記録が Stop フック（`<devkit>/scripts/pstack_usage.py`、`<devkit>` は `~/.claude/skills/devkit`）に残り、何を選んだかの監視と、使い忘れの警告に使われる。
最初に `<pstack>/docs/harness/claude-code.md` を読む。

リポジトリに `.claude/pstack-route.md` があれば先に読む。そこにある行は、この表より優先する。

## 1. 入口を選ぶ

上から順に見て、最初に当てはまる行を選ぶ。playbook は `poteto-mode-auto` スキルを読み込んでから `<pstack>/skills/poteto-mode/playbooks/<名前>.md` を読む。

| 作業 | 入口 |
| --- | --- |
| 数分で終わる読み取りだけの確認（設定や状態を見る、質問に答える） | pstack を使わない |
| 前のスレッドやブランチの続き | poteto-mode → `session-pickup`。自分の最近の作業を集めるだけなら `recall` |
| 大きい・複数の部分にまたがる・オーナーが離れている間に進める作業 | `figure-it-out` と `show-me-your-work` |
| 計画だけを書く（実装しない） | poteto-mode → `multi-phase-plan` |
| 不具合を直す | poteto-mode → `bug-fix`。安いテストが書けるなら `tdd` も |
| 新しい機能・仕組みを足す | poteto-mode → `feature` |
| 振る舞いを変えずに作り替える | poteto-mode → `refactoring` |
| Skill・`CLAUDE.md`・手順書を作る・直す | poteto-mode → `authoring-a-skill` |
| 案が複数あり、作って比べないと決まらない | poteto-mode → `prototype`。型と構成だけなら `architect` |
| 原因や現状を調べる | poteto-mode → `investigation` |
| コードの仕組み・置き場所の質問 | `how`。理由の質問は `why`。かみ砕いた説明は `teach` |
| PR を見守る | poteto-mode → `babysit`。緑の PR の束を入れるなら `shipping` |
| オーナーに同じ指摘を2回された | `correct` |

選んだ入口は、チェックリストの見出しに「入口: poteto-mode / feature」のように書く。

## 2. 作業の後に続けて回す

入口の作業が終わったら、当てはまる行を上から順に回す。★はフックが確かめる。抜けていると、ターンの終わりに読むファイルを示して止められる。

| いつ | 回すもの |
| --- | --- |
| 原因や現状を調べて、結論を出す前 | 反対の向きで一度だけ調べる。結論を決めると、それに合う資料ばかり集めがちだから。「この結論が間違っているとしたら、どんな資料やデータがあるはずか」を1文で書き、それを探す（`source-reader` に任せてよい）。見つかったことと見つからなかったことを、結論と一緒に書く |
| Web ページ、API、データファイルなど、外のデータを読むツールを変えたとき | 実際のデータで動かし、見つけるべきものを本当に見つけるかを確かめてから完了と言う。「何も見つからなかった」は、壊れて何も読めていないときにも同じ結果になるから（鳴らない火災報知器が、火事がないのか電池切れなのか分からないのと同じ）。例：古いリンクを探すツールなら、わざと切れたリンクを1つ混ぜて一覧に出ることを見る。処理が分かれる場合（下書きと公開済みなど）は、どちらの側も1件以上通して確かめる |
| コードや Skill を変えて、レビューに出す前 | ★`no-comments`。変更が小さくても検査の仕組みやフックに触ったなら `blast-radius` |
| 設計に争点がある、または変更が大きい | `interrogate` |
| 文書や文章を書いた | ★`unslop`（文書と PR の文章） |
| PR を出す | ★poteto-mode → `opening-a-pr`（中で `technical-writing`） |
| PR を出した後 | ★poteto-mode → `babysit`。CI が緑でマージしてよいかは、リポジトリの決まりに従う |
| PR をマージした後 | ★`reflect`。学んだことを、このリポジトリの Skill への変更案にする |

★の判定は `<devkit>/scripts/pstack_usage.py` の `RULES` にある。行を足すときは、この表と `RULES` を一緒に直す。

## 3. 監視

各セッションの記録は、クラウドでは `/mnt/project-files/pstack-usage/`、Mac では `~/.claude/pstack-usage/` に1セッション1ファイルで残る。一覧は次で出す。

```bash
python3 ~/.claude/skills/devkit/scripts/pstack_usage.py report
```
