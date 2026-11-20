# dev process kit

Software development process skills for AI coding agents; like a spec-driven-development.

AI コーディングエージェント向けの開発プロセス系スキルをまとめたプラグインです。Claude Code と Codex の両方に、このリポジトリをマーケットプレイスとして追加すれば導入できます。

## スキル

要望を Issue に記録し、設計文書で仕様を合意してから、Issue ごとに1つの PR で実装する、という流れを3つのスキルで進めます。

| スキル | 役割 |
| :--- | :--- |
| `issue` | 要望を GitHub Issue に起票する。リポジトリの Issue テンプレートがあれば従う |
| `design` | Issue を `requirements.md`・`specification.md`・`architecture.md` の3文書に設計し、設計 PR を作る |
| `implement` | マージ済みの設計文書をもとに、Issue 1つにつき1つの実装 PR で実装する |
| `hello` | 導入確認用。決まった1行を返す |

どの設計文書をどのレベルの検証で確かめるか（業務要件はシナリオテストと受け入れテスト、仕様はインテグレーションテスト、アーキテクチャは構造による強制とレビュー、詳細設計はユニットテスト）という対応は、このプラグインが決めます。PR の書式、実装の進め方、テストフレームワークやツール、品質ゲートの方法は決めません。リポジトリの規約と利用者の指示に従います。

## 対応ハーネス

| ハーネス | マーケットプレイス定義 | プラグインマニフェスト | スキル呼び出し |
| :--- | :--- | :--- | :--- |
| Claude Code | `.claude-plugin/marketplace.json` | `plugins/dev-process-kit/.claude-plugin/plugin.json` | `/dev-process-kit:<スキル名>` |
| Codex | `.agents/plugins/marketplace.json` | `plugins/dev-process-kit/.codex-plugin/plugin.json` | `$dev-process-kit:<スキル名>` |

スキル名には `dev-process-kit:` が付くので、同じ名前のスキルを別に入れていても取り違えません。

スキル本体（`plugins/dev-process-kit/skills/`）は両ハーネスで共通です。

## 導入方法

### Claude Code

```text
/plugin marketplace add neko3cs/dev-process-kit
/plugin install dev-process-kit@dev-process-kit
```

導入後に Claude Code を再起動し、次を実行します。

```text
/dev-process-kit:hello
```

### Codex

```sh
codex plugin marketplace add neko3cs/dev-process-kit
codex plugin add dev-process-kit@dev-process-kit
```

デスクトップアプリの場合は、マーケットプレイスを追加したあとに Plugins Directory から `dev-process-kit` を導入できます。導入後は新しいセッションで次を実行します。

```text
$dev-process-kit:hello
```

Codex ではスキルを `$` で呼び出します。Claude Code の `/dev-process-kit:hello` とは先頭の記号が違います。

### 期待される応答

```text
dev-process-kit is installed. (hello from dev-process-kit)
```

## 更新

```sh
# Claude Code
claude plugin marketplace update dev-process-kit
claude plugin update dev-process-kit@dev-process-kit

# Codex
codex plugin marketplace upgrade dev-process-kit
```

## ディレクトリ構成

```text
.
├── .agents/plugins/marketplace.json     # Codex 用マーケットプレイス定義
├── .claude-plugin/marketplace.json      # Claude Code 用マーケットプレイス定義
└── plugins/dev-process-kit/
    ├── .claude-plugin/plugin.json       # Claude Code 用マニフェスト
    ├── .codex-plugin/plugin.json        # Codex 用マニフェスト
    └── skills/                          # 両ハーネス共通のスキル
        ├── issue/
        ├── design/
        ├── implement/
        └── hello/
```

## ライセンス

[MIT](LICENSE)
