# メタプラネット・ビットコイン 毎朝LINE配信システム

毎朝6:00(JST)に、メタプラネット(3350)とビットコインの最新ニュースを
Claude APIが検索・分析し、LINEに1通のメッセージとして自動配信します。

## 仕組み

1. GitHub Actions が毎朝6:00(JST)に `daily_report.py` を実行
2. Claude API（web検索ツール有効）が直近24時間のニュースを検索し、
   メタプラネット・ビットコインそれぞれの分析文を生成
3. LINE Messaging API（push message）で指定ユーザーに送信

競艇予想LINE通知システムと同じ構成なので、既存のLINE Botチャネルを
そのまま流用することもできます（別チャネルにして通知を分けるのもアリです）。

## セットアップ手順

### 1. リポジトリを作る
このフォルダの中身を新しいGitHubリポジトリにpushしてください。

```
git init
git add .
git commit -m "init"
git remote add origin <あなたのリポジトリURL>
git push -u origin main
```

### 2. Secretsを設定
リポジトリの `Settings > Secrets and variables > Actions` で
以下の3つを登録します。

| Secret名 | 内容 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic Consoleで発行したAPIキー |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Developersのチャネルアクセストークン（長期） |
| `LINE_USER_ID` | 送信先のLINEユーザーID |

※ 競艇システムで既にLINE Botを作っている場合、同じチャネルの
アクセストークン・ユーザーIDをそのまま使えます。別々に通知を分けたい
場合は、LINE Developersで新しいチャネルを追加してください。

### 3. 動作確認
リポジトリの `Actions` タブ →
「Daily Metaplanet & BTC Report」→「Run workflow」で手動実行できます。
LINEにメッセージが届けば成功です。

### 4. あとは放置でOK
毎朝6:00(JST)に自動配信されます。

## カスタマイズ

- **配信時刻を変える**: `.github/workflows/daily-report.yml` の
  `cron: '0 21 * * *'` を変更（UTC指定。JST = UTC+9）
- **文章のトーン・分量を変える**: `daily_report.py` の `PROMPT` を編集
- **対象銘柄を増やす**: `PROMPT` に銘柄名を追記するだけでOK
  （例: CRAVIA、東陽テクニカなども対象に含める）
