# dev process kit

Software development process skills for AI coding agents; like a spec-driven-development.

AI コーディングエージェント向けの開発プロセス系スキルをまとめたプラグインです。現在は導入確認用の `hello` スキルだけが入っています。Claude Code と Codex の両方に、このリポジトリをマーケットプレイスとして追加すれば導入できます。

## 対応ハーネス

| ハーネス | マーケットプレイス定義 | プラグインマニフェスト | スキル呼び出し |
| :--- | :--- | :--- | :--- |
| Claude Code | `.claude-plugin/marketplace.json` | `plugins/dev-process-kit/.claude-plugin/plugin.json` | `/dev-process-kit:hello` |
| Codex | `.agents/plugins/marketplace.json` | `plugins/dev-process-kit/.codex-plugin/plugin.json` | `$dev-process-kit:hello` |

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
    └── skills/hello/SKILL.md            # 両ハーネス共通のスキル
```

## ライセンス

[MIT](LICENSE)
