# onezion-skills

自创 WorkBuddy Skills 库 — 由 onezion 实际跑通、验证可用的 Skill 集合。

## 规范
- 所有 Skill 以 `onezion-` 前缀命名
- 每个 Skill 必须在真实场景中跑通过
- SKILL.md 中包含完整 Workflow 和踩坑记录
- 零依赖或仅依赖免费工具（不绑定付费 API Key）

## Skill 列表

| Skill | 功能 | 依赖 |
|-------|------|------|
| `onezion-video-summarize` | yt-dlp + Whisper 视频转录总结 | yt-dlp, python3.12, openai-whisper |
| `onezion-windows-gui-automation` | Windows 桌面 GUI 自动化（原生 UI + AI 视觉 + 鼠标控制） | windows-gui-automation-cn (含 6 子技能) |

## 快速使用

将此仓库中的 skill 目录复制到 \`~/.workbuddy/skills/\` 即可激活。

