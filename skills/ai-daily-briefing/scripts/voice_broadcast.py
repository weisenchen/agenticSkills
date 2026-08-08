#!/usr/bin/env python3
"""
語音播報生成腳本 — 從文本文件生成中文語音（edge-tts）。
確保語音內容與播報稿文件 100% 一致（繞過 agent 自行決定 TTS 文本的問題）。

用法:
  python3 voice_broadcast.py --input /path/to/script.txt --output /tmp/broadcast.mp3 [--voice zh-CN-YunxiNeural]

輸出:
  生成成功後打印音頻路徑（供投遞腳本使用）
"""
import argparse
import asyncio
import os
import sys

DEFAULT_VOICE = "zh-CN-YunxiNeural"  # 雲希：男聲，自然播報風格


async def synthesize(text: str, voice: str, output_path: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate="+0%", pitch="+0Hz")
    await communicate.save(output_path)


def main():
    parser = argparse.ArgumentParser(description="從播報稿文件生成中文語音")
    parser.add_argument("--input", required=True, help="播報稿文本文件路徑")
    parser.add_argument("--output", default="", help="輸出音頻路徑（默認 /tmp/voice_broadcast.mp3）")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="edge-tts 語音（默認雲希男聲）")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ 播報稿文件不存在: {args.input}")
        sys.exit(1)

    with open(args.input, encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("❌ 播報稿為空")
        sys.exit(1)

    char_count = len(text)
    output = args.output or "/tmp/voice_broadcast.mp3"

    try:
        asyncio.run(synthesize(text, args.voice, output))
    except Exception as e:
        print(f"❌ 語音生成失敗: {e}")
        sys.exit(1)

    size = os.path.getsize(output)
    print(f"✅ 語音生成成功: {output} ({size//1024}KB, {char_count}字)")
    print(output)


if __name__ == "__main__":
    main()
