"""
メタプラネット(3350) + ビットコイン 分析レポートをLINEに送信するスクリプト
朝(6:00 JST)と大引け後(15:30 JST)の2回、内容を変えて配信する。

必要な環境変数（GitHub Actions の Secrets に設定）:
  ANTHROPIC_API_KEY         Anthropic API キー
  LINE_CHANNEL_ACCESS_TOKEN LINE Messaging API のチャネルアクセストークン
  LINE_USER_ID              送信先のLINEユーザーID（push message の宛先）

コマンドライン引数:
  python daily_report.py morning   → 朝レポート（前夜〜早朝ニュースまとめ）
  python daily_report.py closing   → 大引け後レポート（その日の値動き振り返り）
"""

import os
import sys
from datetime import datetime, timezone, timedelta

import requests

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

JST = timezone(timedelta(hours=9))

PROMPT_MORNING = """あなたは日本株・暗号資産の投資分析アシスタントです。
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

PROMPT_CLOSING = """あなたは日本株・暗号資産の投資分析アシスタントです。
Web検索を使って、本日の取引についての最新ニュースを調べたうえで、
本日大引け後配信用の「値動き振り返りレポート」を作成してください。

対象は次の2つです。
1. メタプラネット（3350）の本日の株価の値動き（始値・終値・変動率・出来高の傾向）
   とその背景
2. ビットコイン（BTC）の本日（日本時間の日中〜夕方）の値動きとその背景

【出力形式】
- 見出しの前置きは不要。本文からそのまま始める
- 「■メタプラネット」「■ビットコイン」の2セクションに分ける
- 各セクション300字程度。今日1日の値動きの流れ（寄り付き→引けまで）と、
  それを動かした具体的な材料（政策、mNAV、大口売買、地合いなど）を含める
- 専門用語はできるだけ減らし、初心者にもわかる書き方にする
- 最後に1〜2行で、翌営業日以降の注目ポイントを添える
- LINEでそのまま読めるプレーンテキストで出力する
  （Markdown装飾は使わない）
- 株式市場が休場日（土日祝）の場合は、その旨を一言添えたうえで
  ビットコインの値動きを中心にまとめる
"""


def get_analysis(report_type: str) -> str:
    prompt = PROMPT_MORNING if report_type == "morning" else PROMPT_CLOSING
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
            "messages": [{"role": "user", "content": prompt}],
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


def send_line(message: str, report_type: str) -> None:
    today = datetime.now(JST).strftime("%Y/%m/%d")
    label = "朝の投資メモ" if report_type == "morning" else "大引け後の値動き振り返り"
    icon = "📊" if report_type == "morning" else "🔔"
    full_message = f"{icon} {today} {label}\n\n{message}"

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
    report_type = sys.argv[1] if len(sys.argv) > 1 else "morning"
    if report_type not in ("morning", "closing"):
        print(f"不明な引数: {report_type}（morning または closing を指定）", file=sys.stderr)
        sys.exit(1)

    try:
        analysis = get_analysis(report_type)
        send_line(analysis, report_type)
        print(f"送信完了（{report_type}）")
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
