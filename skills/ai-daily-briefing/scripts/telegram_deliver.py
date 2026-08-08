#!/usr/bin/env python3
"""
Telegram direct delivery script - sends text + voice messages via the
Telegram Bot API directly.

Bypasses Hermes cron MEDIA delivery (which may silently drop audio) to
guarantee reliable text + voice delivery for daily AI trend briefings.

Usage:
  python3 telegram_deliver.py --text "summary text" [--audio /path/to/audio.mp3 ...] [--chat 8365377574]
"""
import argparse
import os
import sys
import urllib.request
import urllib.parse
import json
import time

CONFIG_PATH = os.path.expanduser("~/.hermes/config.yaml")
ENV_PATH = os.path.expanduser("~/.hermes/.env")
DEFAULT_CHAT = "8365377574"


def get_token():
    """Read the Telegram bot token: prefer .env TELEGRAM_BOT_TOKEN, then config.yaml."""
    # 1. .env file (real token lives here)
    try:
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line.startswith("TELEGRAM_BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if token and "***" not in token:
                        return token
    except Exception:
        pass
    # 2. Environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if token and "***" not in token:
        return token
    # 3. config.yaml (may be masked; fallback only)
    try:
        import yaml
        with open(CONFIG_PATH) as f:
            cfg = yaml.safe_load(f) or {}
        token = (cfg.get("telegram") or {}).get("token", "")
        if token and "***" not in token:
            return token
    except Exception:
        pass
    return ""


def api_call(token, method, data=None, files=None):
    """Call the Telegram Bot API. files: {field: (filename, fileobj)}"""
    url = f"https://api.telegram.org/bot{token}/{method}"
    if files:
        boundary = "----WebKitFormBoundary" + str(time.time()).replace(".", "")
        body = b""
        for field, value in (data or {}).items():
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"\r\n\r\n{value}\r\n".encode()
        for field, (filename, fobj) in files.items():
            content = fobj.read()
            body += (
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{filename}\"\r\n"
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode() + content + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    else:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data or {}).encode())
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"ok": False, "error": str(e)}


def send_text(token, chat_id, text):
    """Send a text message (chunked to fit Telegram's 4096 limit)."""
    max_len = 4000
    for i in range(0, len(text), max_len):
        chunk = text[i:i + max_len]
        result = api_call(token, "sendMessage", {
            "chat_id": chat_id,
            "text": chunk,
        })
        if not result.get("ok"):
            print(f"ERROR: text send failed: {result.get('error', result)}")
            return False
        time.sleep(0.3)
    return True


def send_voice(token, chat_id, audio_path):
    """Send a voice message. Falls back to sendAudio if sendVoice fails."""
    if not os.path.exists(audio_path):
        print(f"ERROR: audio file not found: {audio_path}")
        return False
    with open(audio_path, "rb") as f:
        result = api_call(token, "sendVoice", {"chat_id": chat_id}, files={"voice": (os.path.basename(audio_path), f)})
    if not result.get("ok"):
        print(f"WARNING: sendVoice failed ({result.get('error')}), trying sendAudio...")
        with open(audio_path, "rb") as f:
            result = api_call(token, "sendAudio", {"chat_id": chat_id}, files={"audio": (os.path.basename(audio_path), f)})
    if result.get("ok"):
        print(f"OK: voice sent: {audio_path}")
        return True
    print(f"ERROR: voice send failed: {result.get('error', result)}")
    return False


def main():
    parser = argparse.ArgumentParser(description="Telegram text + voice delivery (multiple voices supported)")
    parser.add_argument("--text", default="", help="text content to send (may be empty if only sending voice)")
    parser.add_argument("--audio", action="append", default=[], help="audio file path (repeatable, sends multiple)")
    parser.add_argument("--chat", default=DEFAULT_CHAT, help="chat_id")
    args = parser.parse_args()

    token = get_token()
    if not token:
        print("ERROR: cannot get Telegram bot token (.env TELEGRAM_BOT_TOKEN or config.yaml)")
        sys.exit(1)
    if not args.text and not args.audio:
        print("ERROR: at least one of --text / --audio is required")
        sys.exit(1)

    ok_text = True
    if args.text:
        ok_text = send_text(token, args.chat, args.text)

    ok_voice = True
    for audio in args.audio:
        if not send_voice(token, args.chat, audio):
            ok_voice = False

    if ok_text and ok_voice:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
