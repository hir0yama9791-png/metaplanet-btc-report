"""
メタプラネット(3350) + ビットコイン 毎朝の分析レポートをLINEに送信するスクリプト

必要な環境変数（GitHub Actions の Secrets に設定）:
  ANTHROPIC_API_KEY         Anthropic API キー
  LINE_CHANNEL_ACCESS_TOKEN LINE Messaging API のチャネルアクセストークン
  LINE_USER_ID              送信先のLINEユーザーID（push message の宛先）
"""

import os
import sys
from datetime import datetime, timezone, timedelta

import requests

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

JST = timezone(timedelta(hours=9))

PROMPT = """あなたは日本株・暗号資産の投資分析アシスタントです。
Web検索を使って、直近24時間以内のニュースを調べたうえで、
今日の朝配信用の分析レポートを作成してください。

対象は次の2つです。
1. メタプラネット（3350）の直近の株価動向とその背景
2. ビットコイン（BTC）の直近の価格動向とその背景

【出力形式】
- 見出しの前置きは不要。本文からそのまま始める
- 「■メタプラネット」「■ビットコイン」の2セクションに分ける
- 各セクション300字程度。具体的な価格・変動率・材料
  （政策、mNAV、大口売買、需給など）を含める
- 専門用語はできるだけ減らし、初心者にもわかる書き方にする
- 最後に1〜2行で、今日以降の注目ポイントを添える
- LINEでそのまま読めるプレーンテキストで出力する
  （Markdown装飾は使わない）
"""


def get_analysis() -> str:
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 1500,
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
            "messages": [{"role": "user", "content": PROMPT}],
        },
        timeout=180,
    )
    resp.raise_for_status()
    data = resp.json()
    text_blocks = [b["text"] for b in data["content"] if b.get("type") == "text"]
    analysis = "\n".join(text_blocks).strip()
    if not analysis:
        raise RuntimeError(f"Claude APIから本文が取得できませんでした: {data}")
    return analysis


def send_line(message: str) -> None:
    today = datetime.now(JST).strftime("%Y/%m/%d")
    full_message = f"📊 {today} 朝の投資メモ\n\n{message}"

    # LINEのテキストメッセージは1通5000文字までなので安全のため切り詰め
    if len(full_message) > 4900:
        full_message = full_message[:4900] + "\n…(以下省略)"

    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "to": LINE_USER_ID,
            "messages": [{"type": "text", "text": full_message}],
        },
        timeout=30,
    )
    resp.raise_for_status()


def main() -> None:
    try:
        analysis = get_analysis()
        send_line(analysis)
        print("送信完了")
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
