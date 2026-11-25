---
name: issue
description: Creates a GitHub Issue with the gh CLI that records the user's request, following the target repository's Issue templates when it has them, filling every required field from the user's request and composing the body in GitHub's rendered heading format. Also records context on an existing Issue as a comment — background, investigation results, or the course of a discussion. Run only when the user explicitly invokes this skill by name ("/dev-process-kit:issue ...", "$dev-process-kit:issue ..."); do not select it for general requests such as "create an issue" or "Issueを作って".
disable-model-invocation: true
---

# issue Skill

GitHub Issue を `gh` コマンドで作成し、必要に応じて調査結果や経緯をコメントとして残します。

## 責務と原則

- **責務の境界**: 要望の記録と経緯の補足だけを行う（設計・実装・PR 作成は始めない）。何を作るかの合意や受け入れ基準の作り込みは設計文書で行うため。対応する PR ができた後の未決質問は Issue ではなくその PR に投稿する。
- **公開・通知される前提で書く**: Issue はリポジトリ閲覧者全員に届き、後から消しても取り消せない。書いてよいのは一般化した要望とリポジトリに関する事実（コードの挙動、外部仕様、調査結果、選ばなかった案と技術的理由）だけとし、利用者固有の事情や機密情報（取引先・社名・社内予定・個人情報など）は明示的な依頼が無い限り書かない（例: 「A社の案件で来月までに CSV 出力が必要」→「集計結果を CSV で受け渡したい」）。判断できないものは書かない。
- **完成品として書く**: 本文はそのまま読める完成した要望として書き、確認できない事実（再現結果・環境・実測値など）だけは創作せず確認できていないと書く。未決の要望は最も妥当な案を本文に書き、確認は起票後のコメントで行う（例: `TBD`・`仮定` などの未決印や確認待ちの注記を本文に残さない）。
- **安全なコメント更新**: 同じ話題の記録（調査結果や論点の結論）が変わったら、古い内容で読者が迷わないよう既存コメントを書き換える。ただし書き換えでは通知が飛ばず他人の文章も変えてしまうため、対象はエージェント自身が書いたと確信できる記録コメントに限る。他人のコメント・利用者が書いたコメント・判断を問う質問は新規コメントにする。

## 1つの Issue に1つの要件

Issue は要件の単位で起票します。1つの Issue が1つの要件だけを持てば、設計PRと実装PRも Issue ごとに1つで済むためです。親子の Issue（`--parent`）には分けません（子だけを読んでも何の要件か分からなくなるため）。

- 単独で利用者に価値を届けられる要件が複数あるかで判断する（作業量や PR の大きさでは判断しない）。
- 要件が1つなら確認せず1つの Issue を起票する。
- 要件が複数なら起票前に分け方（Issue ごとのタイトルと要件）を示して確認する。了承されたら Issue ごとに手順1〜5を行い、各 Issue にもう一方の番号と分けた理由をコメントする。1つにまとめるよう言われたら1つの Issue で起票する。

## 起票前に確認する場合

原則として確認なしで起票します。起票前に止まって確認するのは次の場合だけで、複数あっても1回の質問にまとめます。

| 場合 | 確認すること |
| :--- | :--- |
| 依頼に要件が複数ある | 要件ごとの分け方（「1つの Issue に1つの要件」） |
| 本人の同意・確認を表すチェック項目がある | その項目に同意・確認するか（[テンプレートと `gh` 操作の詳細](references/templates-and-gh.md#3-各フィールドの埋め方と本文の組み立て)） |
| 複数テンプレートから選び難い | どのテンプレートを使うか |

## Issue に残すもの

後で設計や実装をする人が会話を持たずに困るものだけを残します。作業の実況やコードを読めば分かることは書きません。

| 残す先 | 残すもの |
| :--- | :--- |
| Issue 本文 | 合意の対象となる要望。テンプレートのフィールドに書く |
| Issue コメント | 要望を聞く途中で生じた考え・暗黙知・調査結果のうち、本文に入れると長すぎるものや経緯 |

## 実行手順

テンプレートの読み取り、`type: checkboxes` / `dropdown`、言語決定、ラベル事前照合、`gh` コマンドの詳細は [テンプレートと `gh` 操作の詳細](references/templates-and-gh.md) に従います。

1. **テンプレートを探す**: 作成のたびに `.github/ISSUE_TEMPLATE/`（無ければ所有者の `.github` リポジトリ）から `config.yml` / `config.yaml` を除く最新のテンプレートを読む。1つでもあれば必ず従う。
2. **各フィールドの内容を埋める**: 言語決定順に従って書く。必須項目をすべて埋め、任意項目は内容が無ければ省略する。`type: checkboxes` のうち本人の同意・確認項目は代理チェックせず起票前に確認する。
3. **本文を組み立てる**: Issue Forms は `### {label}` 形式で組み立てる（`type: markdown` は飛ばす）。テンプレートも指示も無ければデフォルト見出し（説明／動機・背景／受け入れ条件）で書く。
4. **`gh issue create` を実行する**: 事前に `gh label list` でラベルを照合して無いラベルは外し、一時ファイル経由（`--body-file`）で確認なしに起票する。作成後に Issue URL（と付けられなかったラベル・属性があればその旨）を提示する。
5. **補足と質問をコメントに書く**: 本文に入れなかった調査結果・経緯や、要件分割時の他 Issue 番号と理由があれば `gh issue comment` で書く。手順2で未決の要望から選んだ内容があれば、対象のフィールド・書いた内容・選んだ理由・代替案と違いを示し、「この内容でよいか、別案ならどれか」を答えられる新規コメントで質問する（調査結果コメントとは分ける）。

## 起票後に分かったことを残す

起票後の議論で考え・暗黙知・調査結果が生じたら、その Issue にコメントとして書きます。

- 議論の結果、要望が変わる場合は本文も更新する（`gh issue edit <番号> --body-file <一時ファイル>`、テンプレートの見出し形式を保つ）。
- 本文を更新したら、何をなぜ変えたかをコメントにも残す。同じ論点の記録コメントが既にあれば、[既存コメントの安全な書き換え](references/templates-and-gh.md#5-既存コメントの安全な書き換え) に従って書き換える。

## 参考資料

- [テンプレートと `gh` 操作の詳細](references/templates-and-gh.md)
- GitHub Docs: [Configuring issue templates for your repository](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository)
