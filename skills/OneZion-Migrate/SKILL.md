---
name: OneZion-Migrate
description: >
  Agent 迁移工具。将当前 WorkBuddy 环境打包为可移植 zip 包，包含 Skills、MCP 配置、Memory、聊天记录、API 密钥，
  以便一键迁移到任意 Agent 平台（OpenClaw、Codex、Manus、Claude Code 等）。
  也支持反向操作：从 zip 包恢复环境到新的 WorkBuddy 实例。
  触发词：迁移、migrate、打包、备份 Agent、export agent、import agent、上云、cloud deploy。
agent_created: true
allowed-tools:
  - Bash
  - Read
  - Write
  - AskUserQuestion
---

# OneZion-Migrate

Agent 便携化迁移工具。核心理念：**Agent 之间迁移应该是无感的**。把所有自定义配置打包成一个 zip，丢进任何 Agent 对话框，它自己配置好。

## 设计哲学

Agent 迁移 ≠ 软件迁移、硬件迁移、OS 迁移。只有 Agent 迁移能做到无缝：
- 从 0 到 1 最难（首次搭建）
- 从 1 到 100 极简（迁移 zip 丢进去就行）

这是滚雪球效应：有了迁移能力 → 可以批量试用新 Agent → 可以云端部署 → 可以只带手机工作。

## 五层迁移架构

迁移包包含 5 个抽象层：

```
onezion-agent-migrate/
├── README.md                    # 新 Agent 读取的第一个文件（含配置指引）
├── skills/                      # 层1: Skills（核心资产）
│   ├── Tier1/                   # onezion-* 命名 = 必带，最高优先级
│   └── Tier2/                   # 其他有用但非核心的 skills
├── mcp/                         # 层2: MCP 配置
│   ├── mcp.json                 # MCP server 配置
│   └── env_export.sh            # 导出的环境变量（Keychain → 文件）
├── memory/                      # 层3: Memory
│   ├── MEMORY.md                # 长期记忆
│   └── daily/                   # 每日记忆文件
├── chat_history/                # 层4: 聊天记录（双层策略）
│   ├── sessions_metadata.jsonl  # sessions 表元数据（标题、时间、模型）
│   ├── raw_messages/            # 原始 JSONL 消息文件（完整对话内容）
│   ├── LLMWiki_simplified.md    # LLMWiki 简化版（快速概览，导入后自动生成）
│   └── context_brief.md         # 当前工作状态一句话说明
├── secrets/                     # 密钥导出（⚠️ 敏感）
│   ├── keychain_export.txt      # macOS Keychain 导出
│   └── notion.env               # Notion API key 等
└── meta.json                    # 迁移包元数据（时间、版本、来源平台）
```

## Skills 分层规则

**Tier 1（硬编码，必带）**：以 `onezion-` 或 `OneZion-` 开头的所有 skills。
这是设计意图：命名就是筛选规则，不容忍 AI 概率性猜测。

**Tier 2（推荐）**：非 onezion 前缀但用户高频使用的 skills（如 `wacli`、`agent-browser`）。

**排除**：内置 skill（builtin/plugin）、临时或一次性 skill。

## 操作指南

### 导出（Export）

当用户要求打包/迁移/备份 Agent 环境时执行：

1. **确认目标**：询问用户迁移目的（换平台、上云、备份、分享给他人）
2. **运行导出脚本**：

```bash
bash /Users/onezion12344/.workbuddy/skills/OneZion-Migrate/scripts/export_agent.sh \
  --output ~/Desktop/onezion-agent-migrate.zip
```

3. **生成 README.md**：脚本自动生成，但需人工/AI review 确认指引准确
4. **确认密钥处理**：导出 Keychain 中的 API keys（notion-api-key 等），需用户授权

### 导入（Import）

当收到迁移 zip 包时执行：

1. **解压到临时目录**
2. **读取 README.md** 了解配置要求
3. **按 README 指引逐步配置**：
   - 安装 Tier 1 skills（复制到 `~/.workbuddy/skills/`）
   - 导入 MCP 配置（合并到 `~/.workbuddy/mcp.json`）
   - 恢复 Memory 文件
   - 导入 API keys（提示用户手动添加或使用 keychain 导入命令）
4. **验证**：运行关键 skill 确认可用

### 优化（Optimize）

打包前做一次清理：

- 合并功能重叠的 skills
- 删除已废弃或从未使用的 skills
- 压缩过大的 memory 文件（保留最近 30 天，更早的 distill 到 MEMORY.md）
- 聊天记录只保留摘要，不搬运完整历史

### 部署到云端（Cloud Deploy）

迁移包的终极用法：将 zip 包内容部署到云端 Agent：

1. 确认云端 Agent 支持的配置方式（API、文件上传、对话框粘贴）
2. 将 README.md + 关键配置转为一段长文本 prompt
3. 在云端 Agent 对话框中发送，让它自配置

## 密钥安全

- `secrets/` 目录包含敏感信息，zip 包需加密或仅本地传输
- macOS Keychain 导出命令：
  ```bash
  security find-generic-password -a "notion" -s "notion-api-key" -w
  ```
- ⚠️ 不要将含密钥的 zip 包上传到公开 GitHub 仓库

## meta.json 格式

```json
{
  "version": "1.0.0",
  "exported_at": "2026-05-07T10:35:00+08:00",
  "source_platform": "workbuddy",
  "source_device": "MacBook Air M4 (macOS)",
  "user": "onezion12344",
  "tier1_skills_count": 25,
  "tier2_skills_count": 8,
  "total_size_mb": 12.5,
  "notes": "考后迁移包，包含全部 onezion-* skills"
}
```

## 注意事项

- 聊天记录全部丢入可能爆 context window，所以只迁移摘要 + 关键对话
- 有些 MCP server 需要重新 OAuth 授权（如 Outlook、GitHub），README 中标注
- 本地 RAG（ChromaDB 向量库）体积较大，可选择性包含
- ScreenPipe 录制数据不包含在迁移包中（体积太大，且有隐私风险）
