---
name: onezion-workspace-cleanup
description: Scan and clean up bloated WorkBuddy workspaces. Uses dust/dua CLI for fast disk analysis. Identifies large files (videos, node_modules, .venv, build artifacts), generates a report, and optionally removes them with user confirmation. Trigger on: "清理工作区", "磁盘不够了", "workspace cleanup", "free up space", "工作区膨胀", "node_modules 太大".
allowed-tools: Bash, Read, Write, AskUserQuestion
agent_created: true
---

# Workspace Cleanup Skill

Scan WorkBuddy workspaces for bloated directories and large files, generate a report, and optionally clean them up.

## CLI Tools (pre-installed)

| Tool | Purpose | Install |
|------|---------|---------|
| `dust` | Tree map view of disk usage, top-N biggest items | `brew install dust` |
| `dua` | Fast parallel disk usage analyzer, supports batch delete | `brew install dua-cli` |
| `du` | macOS built-in, fallback | built-in |
| `df` | Filesystem-level space check | built-in |

## Step 1: Disk overview

```bash
# Overall disk status
df -h /

# WorkBuddy total + top 20 biggest workspaces
du -sh ~/WorkBuddy/ 2>/dev/null
du -sh ~/WorkBuddy/*/ 2>/dev/null | sort -rh | head -20
```

## Step 2: Visual scan with dust

```bash
# Top 20 biggest items in WorkBuddy (tree view)
dust -n 20 ~/WorkBuddy/

# Top 15 biggest items in a specific workspace
dust -n 15 ~/WorkBuddy/<workspace-id>/
```

## Step 3: Deep scan — find the usual suspects

```bash
# Find large files (>50MB) — videos, binaries, archives
find ~/WorkBuddy -type f -size +50M -exec ls -lh {} \; 2>/dev/null | sort -k5 -rh

# Find all node_modules directories with sizes
find ~/WorkBuddy -name "node_modules" -type d -exec du -sh {} \; 2>/dev/null | sort -rh

# Find Python venv directories
find ~/WorkBuddy -name ".venv" -type d -exec du -sh {} \; 2>/dev/null | sort -rh

# Find build artifacts
find ~/WorkBuddy \( -name ".next" -o -name "dist" -o -name "build" -o -name "__pycache__" -o -name ".pytest_cache" \) -type d -exec du -sh {} \; 2>/dev/null | sort -rh

# Find video files specifically (the #1 space killer)
find ~/WorkBuddy \( -name "*.mov" -o -name "*.mp4" -o -name "*.avi" -o -name "*.mkv" \) -exec ls -lh {} \; 2>/dev/null | sort -k5 -rh
```

## Step 4: Generate report

Present findings to the user in a clear table:
- File path (relative to ~/WorkBuddy)
- Size
- Type (video / node_modules / venv / build artifact / other)
- Recommended action (delete / move to external SSD / keep)

## Step 5: Confirm before any cleanup

**NEVER delete without user confirmation.** Use AskUserQuestion to let the user select which items to clean.

For each confirmed item:
- **Videos (.mov, .mp4):** Move to trash via `osascript -e 'tell application "Finder" to delete POSIX file "PATH"'`
- **node_modules:** `rm -rf` (can always be regenerated with `npm install` or `pnpm install`)
- **.venv:** `rm -rf` (can be regenerated with `python3 -m venv .venv`)
- **Build artifacts (.next, dist, build, __pycache__):** `rm -rf` (regenerated on next build)
- **Entire completed workspaces:** `tar czf` to external SSD first, then trash

## Step 6: Post-cleanup verification

```bash
# Verify space recovered
df -h /
du -sh ~/WorkBuddy/
dust -n 10 ~/WorkBuddy/
```

## Automation suggestion

If the user wants ongoing management, suggest creating an automation that runs this scan weekly:
- Schedule: weekly on Sunday
- Action: scan and report only (never auto-delete)

## Key rules

1. **Always scan first, act second.** Never skip the report.
2. **Always confirm before deletion.** List every file path.
3. **Prefer trash over rm.** Use `osascript` Finder delete for user files.
4. **node_modules and .venv are safe to delete** — they're reproducible.
5. **Videos are the #1 space killer.** Always check for .mov and .mp4 files first.
6. **Never touch project source code, configs, or .git directories** without explicit approval.
7. **Use `dust` for quick visual scans, `dua` for detailed per-directory analysis, `du` as fallback.**
