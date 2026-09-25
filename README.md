# Agentic Skills

A collection of agent skills (Claude Code / Hermes compatible) for AI-powered workflows.

All skill code and documentation are in **English** (Chinese appears only in
content examples, e.g. sample broadcast scripts, since the briefing itself is bilingual).

## Skills

### [ai-daily-briefing](skills/ai-daily-briefing/)

Daily bilingual (Chinese + English) AI trends briefing — combines top AI builders'
tweets (free central feed, no API keys) with RSS articles into:

- **Bilingual text summary** (Chinese + English)
- **Chinese voice broadcast** (spoken-word audio)
- **English voice broadcast** (spoken-word audio)

Delivered to Telegram. Zero API cost — tweets come from a central feed, RSS from
blogwatcher-cli, voice from edge-tts.

### [how-to-speak](skills/how-to-speak/)

Executable rules for giving a lecture, talk or voice-over script that lands — distilled
from Patrick Winston's *How to Speak* (MIT OpenCourseWare, 63:42):

- **Openings & closings** — lead with an empowerment promise, never end on "thank you"
- **Slides** — the nine slide crimes, with the fix for each (the final slide is *contributions*)
- **What to say** — vision + evidence of work within five minutes, situate, inspire, tell stories
- **Verbal craft** — cycle the core point three times, verbal punctuation, a question with a 7-second pause
- **Winston's star** — the five S's in his own words (`salient` means it sticks out, not that it's important)

Every rule carries a verbatim transcript quote with a timestamp, so each claim can be checked
against the source; `references/how_to_speak_winston.md` holds the full clause + quote evidence.

## Structure

```
agenticSkills/
└── skills/
    └── <skill-name>/
        ├── SKILL.md          # Skill definition (YAML frontmatter + instructions)
        ├── references/       # Optional reference docs
        └── scripts/          # Executable helpers
```
