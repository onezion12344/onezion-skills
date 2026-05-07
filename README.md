# OneZion Skills Collection

> Battle-tested AI agent skills for WorkBuddy. Built by a university student who got tired of doing things manually.

These are real skills I use daily — not demos, not tutorials. They solve actual problems I hit while building my personal AI agent system.

## Installation

```bash
# Clone into your WorkBuddy skills directory
git clone https://github.com/onezion12344/onezion-skills.git ~/.workbuddy/skills/onezion-skills

# Or copy individual skills
cp -r skills/onezion-<name> ~/.workbuddy/skills/
```

---

## The Skills

### 🖥️ onezion-macos-desktop-control

**Mac desktop automation via AppleScript + shortcuts CLI + computer-use MCP.**

Control any macOS app with natural language. Open windows, click buttons, fill forms — all from your AI agent. Uses a three-layer approach: CLI commands for simple ops, Shortcuts for workflows, and screen capture + AI vision for complex UIs.

```text
Triggers: "click the button", "open Safari", "fill this form", "screenshot and analyze"
```

---

### 💤 onezion-caffeinate

**Prevent your Mac from sleeping — on demand.**

Running a long task? Compiling? Rendering? Keep your Mac awake without touching System Preferences. Supports: prevent lid-close sleep, keep screen on, block idle timeout. One command, zero config.

```text
Triggers: "prevent sleep", "keep awake", "caffeinate", "don't sleep", "合盖不睡"
```

---

### 🧹 onezion-computer-cleanup

**Full Mac disk cleanup — find what's eating your storage.**

Scans caches, trash, browser data, dev tool artifacts, iOS backups, and more. Shows you exactly where your disk space went, with safe-to-delete recommendations. No mystery `rm -rf` — just clear reports before any action.

```text
Triggers: "clean up my Mac", "free up space", "disk full", "what's using my storage"
```

---

### 📊 onezion-daily-report

**Generate beautiful infographic posters from any data.**

Turn daily summaries, data analytics, social media stats, or project updates into shareable poster images. Uses a template-driven approach — your data in, a polished visual out. Great for team standups, social media, or personal dashboards.

```text
Triggers: "generate daily report", "make an infographic", "poster", "数据海报"
```

---

### 🎬 onezion-video-compress

**Compress videos to a target size — automatically calculates optimal parameters.**

Need to send a video that's too big? Give it a target size (e.g., "25MB for email") and it figures out the best bitrate, preset, and scaling. Supports 2-pass encoding for maximum quality and CRF mode for speed.

```text
Triggers: "compress this video", "make it smaller", "target 25MB", "video too large"
```

---

### 🧠 onezion-video-summarize

**Summarize any video — online or local — with AI.**

Works with YouTube, Bilibili, and 1000+ sites. Also handles local files (.mov, .mp4, .mkv). Get a structured summary, full transcript, key timestamps, and topic breakdown. Supports long videos — chunks intelligently to avoid context limits.

```text
Triggers: "summarize this video", "what's in this YouTube link", "transcribe", "视频总结"
```

---

### 📺 onezion-wechat-channels-live

**Record live streams from 50+ platforms + WeChat Channels download + AI summarization.**

Combines StreamCap/streamget for universal live recording with WeChat Channels video download. Records Twitch, Bilibili, Douyin, Kuaishou, and more. Auto-generates summaries when the stream ends. Perfect for catching streams you can't watch live.

```text
Triggers: "record this live stream", "直播录制", "下载视频号", "watch later"
```

---

### 🧽 onezion-workspace-cleanup

**Scan and clean bloated WorkBuddy workspaces.**

Uses `dust`/`dua` CLI for fast disk usage analysis. Identifies oversized workspaces, stale task directories, and forgotten artifacts. Gives you a clear report before deleting anything.

```text
Triggers: "clean up workspace", "WorkBuddy too big", "disk usage", "workspace cleanup"
```

---

### 🛒 onezion-e-commerce

**Full-stack e-commerce toolkit for Chinese platforms.**

Price comparison across Taobao, JD, Pinduoduo, Douyin, Kuaishou, 1688, Suning, VIP. Rebate link generator for Taobao/JD/PDD. Product search, price history, and deal alerts. All from your agent.

```text
Triggers: "比价", "search product", "find deals", "淘宝京东拼多多", "返利"
```

---

### 🎙️ onezion-mimo

**Multimodal processing via Xiaomi MiMo API.**

Video understanding (URL/Base64), audio transcription, image analysis, and V2.5 TTS voice synthesis. Feed it a video URL and get a structured analysis. Transcribe audio files. Generate speech with custom voice profiles.

```text
Triggers: "analyze this video", "transcribe audio", "TTS", "voice synthesis", "MiMo"
```

---

### 🐟 onezion-mimo-xianyu

**Smart Xianyu (闲鱼) seller assistant — browser automation for the Chinese second-hand market.**

Auto-list products, monitor messages, suggest intelligent replies, and manage your Xianyu shop. Classifies incoming messages (buyer inquiry / negotiation / after-sale) and drafts contextual responses. Browser-based — works with your existing login.

```text
Triggers: "sell on Xianyu", "闲鱼", "monitor messages", "auto-reply", "二手交易"
```

---

### 💬 onezion-chatlab

**Query local chat history from ChatLab (WhatsApp, WeChat, etc.).**

Search, filter, and analyze imported chat records via ChatLab's local REST API. Keyword search with SQL query support, conversation statistics, and message export. All data stays local — nothing sent to the cloud.

```text
Triggers: "search chats", "find message", "chat history", "聊天记录查询"
```

---

## What's NOT Included

Skills that are excluded because they contain personal config, HKU-specific integrations, or API keys:

- `onezion-superhuman-cli` — HKU email integration (requires institutional auth)
- `onezion-ricci-blacker-dining-hall` — HKU dormitory dining hall
- `onezion-hotel-flights` — Personal booking configs
- `onezion-trading-webull` — Financial trading (too risky for public)
- `onezion-wechat-article-to-notion` — Contains personal Notion page IDs
- `onezion-RAG-workbuddy-log` — Personal chat log vector DB

These live in the private repo: [onezion-agent-migrate](https://github.com/onezion12344/onezion-agent-migrate) (private).

## Design Philosophy

**Naming = Classification.** Skills prefixed with `onezion-` are Tier 1 (core, always migrate). No AI guesswork needed — the name is the contract.

**Skills are modular.** Each one does one thing well. No monolithic "do everything" skills.

**Real-world tested.** Every skill here has been used in production (my daily workflow). If it broke, I fixed it. If it was annoying, I rewrote it.

## Contributing

These are my personal skills shared as-is. Fork freely. PRs welcome if you fix bugs or add genuinely useful features.

## License

MIT — do whatever you want with them.
