# pstack と Codex

pstack の並列の局面（arena、interrogate、swarm）では、席のうち1つ（`inherit-parent` の席）を Codex に回す。

- Codex へは `codex:codex-rescue` サブエージェントを通して頼む。poteto-mode から Codex を直接呼ばない。
- Codex が使えないとき（呼び出しが失敗する、認証が切れている）は、その席を Claude に戻して続ける。
- このルールは `codex` コマンドがある環境（ローカルの Mac）だけで効く。ない環境では置かない。
