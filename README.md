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

## Structure

```
agenticSkills/
└── skills/
    └── <skill-name>/
        ├── SKILL.md          # Skill definition (YAML frontmatter + instructions)
        ├── references/       # Optional reference docs
        └── scripts/          # Executable helpers
```
