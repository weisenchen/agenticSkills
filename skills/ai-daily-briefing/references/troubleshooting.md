# Troubleshooting & Debugging Notes (from real incidents)

Session-specific pitfalls discovered while building this pipeline. Read this
before debugging a "voice doesn't match" or "nothing delivered" report.

## 1. Voice doesn't read the broadcast script (ROOT CAUSE — most common bug)

**Symptom:** The script (written by the LLM) looks correct, but the audio only
covers a fraction of it (e.g. 30s of audio for a claimed 694-char script), or
reads content that differs from the script.

**Root cause:** The LLM passed its OWN shortened/summarized text to the TTS
tool instead of the full script — even when the prompt said "pass the full
script". The model truncates or rewrites at call time. The TTS tool itself
does NOT truncate (edge limit is 5000 chars; a 400-800 char script is fine).

**Fix (mandatory pattern):** never let the LLM pass text to TTS directly.
Always:
1. LLM writes the full script to a file (`/tmp/voice_zh.txt`) via write_file/heredoc
2. `voice_broadcast.py --input <file>` reads the file and synthesizes
3. Audio content is then mechanically identical to the file — cannot drift

This is the general **deterministic-handoff pattern**: when an LLM-produced
artifact must be passed to an external tool/API exactly, write it to a file
and let a script read the file. Do not trust the LLM to pass it inline.

## 2. Telegram delivery: Hermes cron MEDIA: tags may not deliver audio

**Symptom:** Cron job runs OK, text arrives, but the audio attachment never
arrives. The cron output file shows `MEDIA:/path/to/audio.mp3` in the
Response, delivery logs say "delivered to telegram:<chat>", yet no voice.

**Investigation trail (if you need to re-derive):**
- `cron/scheduler.py` extracts `MEDIA:` tags via
  `BasePlatformAdapter.extract_media()` and passes `media_files` to
  `_send_to_platform()` (standalone path) — in theory it should work.
- `gateway/platforms/base.py` `extract_media()` works fine on the exact
  format the agent emits (verified by unit test — the extraction logic is OK).
- In practice the cron delivery path (gateway.run / live adapter route) can
  drop the media silently. Don't spend hours here — switch to the direct
  approach below.

**Reliable fix:** `telegram_deliver.py` calls the Telegram Bot API directly
(`sendMessage` + `sendVoice`/`sendAudio`), bypassing Hermes MEDIA handling
entirely. Use it from the cron prompt as a mandatory step.

## 3. Telegram bot token location

- `~/.hermes/config.yaml` → `telegram.token` is **masked** (stored as
  `8056378201:***`). Useless for direct API calls.
- Real token lives in `~/.hermes/.env` → `TELEGRAM_BOT_TOKEN=...`.
- A standalone python process calling `load_gateway_config()` gets an empty
  token (`"You must pass the token from BotFather"` error) — the token is not
  in the config load path for out-of-process code.
- `telegram_deliver.py` handles this: reads `.env` first, skips any value
  containing `***`.

## 4. Cron agents skip "mandatory" steps

**Symptom:** First cron runs produced text-only output despite "you MUST call
text_to_speech". The agent decided there was nothing new and skipped TTS.

**Fix:** Make the cron prompt a mechanical checklist with file handoffs and
verification gates ("confirm output says voice generated OK"), and make the final
response `[SILENT]` so Hermes doesn't double-deliver the text.

## 5. Verifying audio content objectively

Use local whisper to transcribe the generated audio and compare with the
script file:

```python
from tools.transcription_tools import transcribe_audio
r = transcribe_audio('/tmp/voice_zh.mp3', model='base')
print(r['transcript'])   # note: key is 'transcript', not 'text'
```

`model='base'` mangles Chinese/English mixes into keyword soup, but you can
still confirm every headline/name is present. Duration check: `ffprobe -v
error -show_entries format=duration -of csv=p=0 file.mp3`.

## 6. Expected audio lengths (edge-tts, zh-CN-YunxiNeural)

- 400-800 Chinese chars → ~2 minutes (120-130s), ~180KB mp3
- 17-30s audio = script was truncated/shortened by the LLM → see #1
- English (en-US-AriaNeural) runs slightly longer per char (~170s for 500 words)

## 7. gh CLI device-code auth pitfall

`gh auth login --web` generates a NEW one-time code on every process start.
If the process times out and you restart, the previously-shown code is
already invalid — always show the LATEST code from the running process.
Run it in background (`terminal background=true` + `tee` to a log) so it
doesn't time out, poll for the code, then wait for completion.
