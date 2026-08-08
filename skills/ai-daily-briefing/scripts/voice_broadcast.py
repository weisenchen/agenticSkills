#!/usr/bin/env python3
"""
Voice broadcast generator - synthesizes Chinese/English speech from a
script FILE using edge-tts.

Guarantees the audio matches the broadcast script 100% (bypasses the
problem of an LLM passing its own shortened text to TTS).

Usage:
  python3 voice_broadcast.py --input /path/to/script.txt --output /tmp/broadcast.mp3 [--voice zh-CN-YunxiNeural]

Output:
  Prints the audio path on success (for the delivery script to use).
"""
import argparse
import asyncio
import os
import sys

DEFAULT_VOICE = "zh-CN-YunxiNeural"  # Yunxi: male, natural broadcast style


async def synthesize(text: str, voice: str, output_path: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate="+0%", pitch="+0Hz")
    await communicate.save(output_path)


def main():
    parser = argparse.ArgumentParser(description="Generate Chinese/English voice from a script file")
    parser.add_argument("--input", required=True, help="path to the broadcast script text file")
    parser.add_argument("--output", default="", help="output audio path (default /tmp/voice_broadcast.mp3)")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="edge-tts voice (default Yunxi male)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: script file not found: {args.input}")
        sys.exit(1)

    with open(args.input, encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("ERROR: script file is empty")
        sys.exit(1)

    char_count = len(text)
    output = args.output or "/tmp/voice_broadcast.mp3"

    try:
        asyncio.run(synthesize(text, args.voice, output))
    except Exception as e:
        print(f"ERROR: voice synthesis failed: {e}")
        sys.exit(1)

    size = os.path.getsize(output)
    print(f"OK: voice generated: {output} ({size//1024}KB, {char_count} chars)")
    print(output)


if __name__ == "__main__":
    main()
