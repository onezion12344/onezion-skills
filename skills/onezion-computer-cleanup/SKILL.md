---
name: onezion-computer-cleanup
description: Full Mac disk cleanup — scans caches, trash, browser data, dev tools, iOS backups, npm/pip/conda stores, Docker images, and Application Support. Goes beyond WorkBuddy workspaces to reclaim disk space across the entire system. Trigger on: "清理电脑", "电脑空间不够了", "mac cleanup", "clean my mac", "磁盘满了", "硬盘不够", "computer cleanup", "free up disk space".
allowed-tools: Bash, Read, Write, AskUserQuestion
agent_created: true
---

# Computer Cleanup Skill

Full macOS disk cleanup. Scans the entire system for space hogs and guides the user through safe cleanup.

**IMPORTANT**: This skill scans personal directories (Library, Trash, Downloads, etc.). Follow the personal_files_safety rules:
- Scan = read-only, report only
- Always confirm before any deletion
- Use trash mechanisms, never `rm -rf` on personal dirs
- Max 10 files per batch
- Warn before destructive actions

## Step 1: Overall disk status

```bash
df -h /
du -sh ~/
```

## Step 2: Scan top-level space consumers

```bash
# Top-level directories by size
du -sh ~/Library/Caches/ ~/Library/Application\ Support/ ~/Library/Logs/ ~/Downloads/ ~/.Trash/ ~/Library/Developer/ ~/.npm/ ~/Library/pnpm/ ~/.miniforge3/ ~/Library/Containers/com.docker.docker/ 2>/dev/null | sort -rh
```

## Step 3: Deep scan — cache breakdown

```bash
# Cache breakdown (top 15)
du -sh ~/Library/Caches/*/ 2>/dev/null | sort -rh | head -15

# npm cache
du -sh ~/.npm/ 2>/dev/null

# pip cache
du -sh ~/Library/Caches/pip/ 2>/dev/null; du -sh ~/.cache/pip/ 2>/dev/null

# Homebrew cache
du -sh ~/Library/Caches/Homebrew/ 2>/dev/null

# Playwright browsers
du -sh ~/Library/Caches/ms-playwright/ 2>/dev/null
```

## Step 4: Deep scan — Application Support

```bash
# Top 15 Application Support folders
du -sh ~/Library/Application\ Support/*/ 2>/dev/null | sort -rh | head -15
```

Known space hogs to look for:
- `CloudDocs` — iCloud document cache (safe to clear, will re-sync)
- `MobileSync` — iPhone/iPad backups (can be large, check if old backups exist)
- `Microsoft Edge` / `Google` — Browser profiles (profiles, extensions, cached data)
- `anythingllm-desktop` — Local LLM data
- `com.bradenwong.whispering` — Whisper model files
- `Superhuman` — Email client cache
- `Notion` — Offline cache
- `WorkBuddy` — App data (1-2GB, contains chat history)

## Step 5: Deep scan — Trash

```bash
du -sh ~/.Trash/
ls -lh ~/.Trash/ | head -20
```

Trash is often the easiest win. Use `osascript` to empty:
```bash
osascript -e 'tell application "Finder" to empty trash'
```

## Step 6: Deep scan — iOS Backups

```bash
# List iOS backups
ls -lh ~/Library/Application\ Support/MobileSync/Backup/ 2>/dev/null
du -sh ~/Library/Application\ Support/MobileSync/Backup/*/ 2>/dev/null | sort -rh
```

Old device backups can be 5-15GB each. If user has a new phone and the old backup is for a device they no longer own, it can be deleted.

## Step 7: Deep scan — Dev tools

```bash
# Conda environments
conda env list 2>/dev/null
du -sh ~/miniforge3/envs/*/ 2>/dev/null | sort -rh

# Docker images/containers
docker system df 2>/dev/null
docker images --format "table {{.Repository}}\t{{.Size}}" 2>/dev/null | head -10

# Xcode derived data
du -sh ~/Library/Developer/Xcode/DerivedData/ 2>/dev/null

# Xcode device support (old iOS versions)
du -sh ~/Library/Developer/Xcode/iOS\ DeviceSupport/ 2>/dev/null

# VS Code extensions
du -sh ~/.vscode/extensions/ 2>/dev/null; du -sh ~/.cursor/extensions/ 2>/dev/null
```

## Step 8: Generate report

Present a comprehensive table sorted by size:

| # | Location | Size | Type | Safe? | Action |
|---|----------|------|------|-------|--------|
| 1 | ~/.Trash | 15GB | Trash | Safe | Empty trash |
| 2 | Library/Caches/Homebrew | 6.3GB | Cache | Safe | `brew cleanup` |
| 3 | MobileSync/Backup/xxx | 16GB | iOS backup | Check | Delete old backups |
| ... | ... | ... | ... | ... | ... |

Safety levels:
- **Safe**: Trash, caches, npm/pip stores, Homebrew cache, browser cache
- **Check**: iOS backups, Docker images, Conda envs, browser profiles
- **Caution**: Application data, WorkBuddy data, iCloud cache

## Step 9: Execute cleanup (with confirmation)

Use AskUserQuestion to let the user select items. For each confirmed item:

**Safe cleanups (automatable):**
```bash
# Empty trash
osascript -e 'tell application "Finder" to empty trash'

# Homebrew cache
brew cleanup --prune=all

# npm cache
npm cache clean --force

# pip cache
pip cache purge 2>/dev/null

# Conda cache
conda clean --all -y 2>/dev/null

# Docker prune (unused images/containers)
docker system prune -a 2>/dev/null

# Xcode derived data
rm -rf ~/Library/Developer/Xcode/DerivedData/*
```

**Check-required cleanups:**
```bash
# iOS backup deletion (list first, confirm specific ones)
# Browser profile cleanup (warn about losing saved passwords if not synced)
# Application Support cleanup (app-specific, varies)
```

**For large Application Support folders:**
- Open the specific app and use its built-in "clear cache" option
- Or delete the app's cache subfolder (not the whole app support folder)

## Step 10: Post-cleanup verification

```bash
df -h /
du -sh ~/Library/Caches/ ~/Library/Application\ Support/ ~/.Trash/ ~/.npm/ 2>/dev/null
```

## Periodic automation

Suggest creating a weekly automation:
- Scan and report only (never auto-delete)
- Compare with previous scan to detect growth
- Alert if any single item grows by >1GB in a week

## Key rules

1. **NEVER `rm -rf` on Library, Downloads, Documents, or Home.** Use osascript/trash.
2. **Always list files before asking for confirmation.**
3. **iOS backups**: verify which device before deleting.
4. **Browser data**: warn about synced passwords before clearing profiles.
5. **CloudDocs/iCloud**: clearing cache is safe, data re-syncs. But warn user.
6. **Batch size**: max 10 items per cleanup action.
7. **Prioritize by impact**: Trash > Caches > Old backups > Dev tools.
