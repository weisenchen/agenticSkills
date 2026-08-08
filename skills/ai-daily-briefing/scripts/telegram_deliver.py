#!/usr/bin/env python3
"""
Telegram 直投腳本 — 直接調用 Telegram Bot API 發送文字 + 語音。
繞過 Hermes cron MEDIA 投遞機制，用於每日 AI 趨勢摘要的文字+語音推送。

用法:
  python3 telegram_deliver.py --text "摘要文字" [--audio /path/to/audio.mp3] [--chat 8365377574]
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
    """讀取 Telegram bot token：優先 .env 的 TELEGRAM_BOT_TOKEN，其次 config.yaml。"""
    # 1. .env 文件（真實 token 存這裡）
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
    # 2. 環境變量
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if token and "***" not in token:
        return token
    # 3. config.yaml（可能被遮蔽，僅作 fallback）
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
    """調用 Telegram Bot API。files: {field: (filename, fileobj)}"""
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
    """發送文字訊息。"""
    # 分段（Telegram 限制 4096）
    max_len = 4000
    for i in range(0, len(text), max_len):
        chunk = text[i:i + max_len]
        result = api_call(token, "sendMessage", {
            "chat_id": chat_id,
            "text": chunk,
        })
        if not result.get("ok"):
            print(f"❌ 文字發送失敗: {result.get('error', result)}")
            return False
        time.sleep(0.3)
    return True


def send_voice(token, chat_id, audio_path):
    """發送語音訊息。"""
    if not os.path.exists(audio_path):
        print(f"❌ 音頻文件不存在: {audio_path}")
        return False
    ext = os.path.splitext(audio_path)[1].lower()
    with open(audio_path, "rb") as f:
        result = api_call(token, "sendVoice", {"chat_id": chat_id}, files={"voice": (os.path.basename(audio_path), f)})
    if not result.get("ok"):
        # 若 sendVoice 失敗（如格式不支持），退回 sendAudio
        print(f"⚠️ sendVoice 失敗: {result.get('error')}，嘗試 sendAudio...")
        with open(audio_path, "rb") as f:
            result = api_call(token, "sendAudio", {"chat_id": chat_id}, files={"audio": (os.path.basename(audio_path), f)})
    if result.get("ok"):
        print(f"✅ 語音發送成功: {audio_path}")
        return True
    print(f"❌ 語音發送失敗: {result.get('error', result)}")
    return False


def main():
    parser = argparse.ArgumentParser(description="Telegram 文字+語音直投（支持多條語音）")
    parser.add_argument("--text", default="", help="要發送的文字內容（可空，只發語音時留空）")
    parser.add_argument("--audio", action="append", default=[], help="音頻文件路徑（可多次，發送多條）")
    parser.add_argument("--chat", default=DEFAULT_CHAT, help="chat_id")
    args = parser.parse_args()

    token = get_token()
    if not token:
        print("❌ 無法獲取 Telegram bot token（config.yaml 或 TELEGRAM_BOT_TOKEN）")
        sys.exit(1)
    if not args.text and not args.audio:
        print("❌ --text 和 --audio 至少需要一個")
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
