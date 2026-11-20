# Getting Started

[English](getting-started.md) | 日本語

dev-process-kit を導入し、1つの要望を Issue から実装 PR のマージまで通す流れを説明します。工程の考え方は [dev-process-kit の思想](philosophy.ja.md)、各スキルの詳細は [スキルリファレンス](skills.ja.md) を参照してください。

## 前提

- 対象のプロジェクトが GitHub リポジトリであること
- [GitHub CLI（`gh`）](https://cli.github.com/) がインストールされ、`gh auth login` で認証済みであること
- 対応ハーネス（Claude Code、Codex、GitHub Copilot CLI、Antigravity）のいずれかが使えること

## 全体の流れ

導入の後、工程は上から順に進みます。「—」の工程は人が行います。工程名から、このページの対応する手順に飛べます。

| No. | 工程 | スキル | 内容 |
| :--- | :--- | :--- | :--- |
| 1 | [起票](#2-要望を-issue-に起票する) | `issue` | 要望を Issue に残す。何を作るかの合意や受け入れ基準はここでは決めない |
| 2 | [設計](#3-設計-pr-を作る) | `design` | Issue を3つの設計文書に落とし込み、設計 PR を作る。文書は完成品として書き、未決だった箇所で選んだ案は PR コメントで質問する |
| 3 | [設計の合意](#4-設計-pr-をレビューしてマージする人の作業) | — | 人が設計 PR をレビューしてマージする。マージで仕様が合意され、凍結される |
| 4 | [実装](#5-実装-pr-を作る) | `implement` | 合意済みの設計文書だけを実装し、Issue 1つにつき1つの実装 PR を作る。判断待ちがあるあいだは Draft のままにする |
| 5 | [受け入れテスト](#6-受け入れテストをして実装-pr-をマージする人の作業) | — | 人が `requirements.md` の受け入れ基準に照らして受け入れテストをし、GO / NO-GO を判断する。NO-GO なら実装に戻る |
| 6 | [実装の合意](#6-受け入れテストをして実装-pr-をマージする人の作業) | — | 人が実装 PR をレビューしてマージする。マージで Issue が完了する |

## 1. 導入する

ハーネスに合わせて、マーケットプレイスを追加してからプラグインを導入します。

```sh
# Claude Code
claude plugin marketplace add neko3cs/dev-process-kit
claude plugin install dev-process-kit@dev-process-kit

# Codex
codex plugin marketplace add neko3cs/dev-process-kit
codex plugin add dev-process-kit@dev-process-kit

# GitHub Copilot CLI
copilot plugin marketplace add neko3cs/dev-process-kit
copilot plugin install dev-process-kit@dev-process-kit

# Antigravity（AGY CLI 1.3.3 以上）
agy plugin install https://github.com/neko3cs/dev-process-kit/plugins/dev-process-kit
```

スキルの呼び出し方はハーネスによって違います。

| ハーネス | 呼び出し例 |
| :--- | :--- |
| Claude Code、GitHub Copilot CLI | `/dev-process-kit:issue` |
| Codex | `$dev-process-kit:issue` |

以降の例は Claude Code の書き方で示します。名前で呼び出すほか、「Issue を作って」「#12 を設計して」のような依頼からスキルが選ばれることもあります。

## 2. 要望を Issue に起票する

作りたいものを、そのまま伝えます。

```text
/dev-process-kit:issue タスクの期限が過ぎたら、一覧で分かるようにしたい
```

`dev-process-kit:issue` は、リポジトリの Issue テンプレートに従って Issue を作ります。テンプレートが無ければ、説明・動機と背景・受け入れ条件の見出しで書きます。決まっていない部分は `仮定:` として理由と一緒に書き、確認のために止まりません。

作られた Issue の番号（ここでは #12 とします）を次の工程で使います。

## 3. 設計 PR を作る

```text
/dev-process-kit:design 12
```

`dev-process-kit:design` は Issue を読み、`requirements.md`・`specification.md`・`architecture.md` を作成または更新して、設計文書だけの設計 PR を作ります。設計文書が無いリポジトリでは、テンプレートから3つの文書を新しく作ります。

設計文書は完成品として書かれます。決まっていない箇所は最も妥当な案が選ばれ、仮定や未承認の印を付けずに仕様として書かれます。その案でよいかは、設計 PR のコメントで質問されます。回答は該当箇所の書き換えで反映されるため、設計 PR をマージすれば、書かれた内容がすべて合意されたことになります。

## 4. 設計 PR をレビューしてマージする（人の作業）

設計 PR を読み、質問コメントに答えます。直してほしい点があれば、レビューコメントを付けて `dev-process-kit:design` にもう一度頼みます。

```text
設計PRのレビューを反映して
```

内容に納得したら、設計 PR をマージします。**このマージで仕様が合意され、凍結されます。**

## 5. 実装 PR を作る

```text
/dev-process-kit:implement 12
```

`dev-process-kit:implement` は、マージ済みの設計文書をもとに、ユニットテストを先に書いて部品を作るテスト駆動開発（TDD）で実装し、インテグレーションテストとシナリオテストで仕様と業務要件を確かめて、Issue 1つにつき1つの実装 PR を作ります。PR 本文には `Closes #12` と、受け入れ基準ごとに対応するテストが書かれます。

実装の途中で設計の不足や誤りが見つかると、`dev-process-kit:implement` は実装を止めます。実装 PR を Draft にし、別の設計 PR で設計を直します。その設計 PR をレビューしてマージしてから、もう一度 `/dev-process-kit:implement 12` を実行すると、実装が再開されます。

## 6. 受け入れテストをして、実装 PR をマージする（人の作業）

`requirements.md` の受け入れ基準に照らして受け入れテストをし、GO / NO-GO を判断します。

- **NO-GO**: 実装 PR にレビューコメントを付け、`dev-process-kit:implement` に対応を頼みます（「PR #13 のレビューに対応して」など）。
- **GO**: 実装 PR をレビューしてマージします。マージで Issue #12 が完了します。

## バグを直すとき

正しい動作がすでに設計文書に書かれているバグは、設計を経ずに Issue を起票してから `dev-process-kit:implement` で直せます。設計文書と食い違うコードは、コードの不具合として扱われます。

## 次に読む

- [dev-process-kit の思想](philosophy.ja.md) — なぜこの工程で進めるのか
- [スキルリファレンス](skills.ja.md) — 各スキルが何を読み、何を作り、何をしないか
