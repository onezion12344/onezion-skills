#!/usr/bin/env bash
# OneZion-Migrate: Agent 环境导出脚本
# 将当前 WorkBuddy 环境打包为可移植 zip 包
set -euo pipefail

# --- 参数解析 ---
OUTPUT_PATH="${HOME}/Desktop/onezion-agent-migrate.zip"
INCLUDE_SECRETS=false
INCLUDE_RAG=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --output) OUTPUT_PATH="$2"; shift 2 ;;
    --secrets) INCLUDE_SECRETS=true; shift ;;
    --rag) INCLUDE_RAG=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

WORKBUDDY_DIR="${HOME}/.workbuddy"
SKILLS_DIR="${WORKBUDDY_DIR}/skills"
MCP_CONFIG="${WORKBUDDY_DIR}/mcp.json"
MEMORY_DIR="${HOME}/WorkBuddy"
STAGING_DIR=$(mktemp -d)
PACKAGE_DIR="${STAGING_DIR}/onezion-agent-migrate"

echo "🚀 OneZion-Migrate Agent Export"
echo "   输出: ${OUTPUT_PATH}"
echo ""

mkdir -p "${PACKAGE_DIR}"/{skills/Tier1,skills/Tier2,mcp,memory/daily,chat_history,secrets}

# ========== 层1: Skills ==========
echo "📦 扫描 Skills..."
TIER1_COUNT=0
TIER2_COUNT=0

for skill_dir in "${SKILLS_DIR}"/*/; do
  [ -d "$skill_dir" ] || continue
  skill_name=$(basename "$skill_dir")

  # 跳过内置/plugin
  if [[ "$skill_name" == "find-skills" ]] || [[ "$skill_name" == "skill-creator" ]]; then
    continue
  fi

  # Strip trailing / for rsync (rsync src/ = copy contents, src = copy dir itself)
  skill_src="${skill_dir%/}"

  # Tier 1: onezion-* 或 OneZion-* 前缀
  if [[ "$skill_name" =~ ^[Oo]ne[Zz]ion ]]; then
    # Skip nested onezion-* copies inside container dirs
    if [ -f "${skill_dir}/SKILL.md" ]; then
      mkdir -p "${PACKAGE_DIR}/skills/Tier1/${skill_name}"
      rsync -a --exclude='.git' --exclude='__pycache__' --exclude='onezion-*' \
        "${skill_src}/" "${PACKAGE_DIR}/skills/Tier1/${skill_name}/"
      TIER1_COUNT=$((TIER1_COUNT + 1))
    fi
  else
    # Tier 2: 检查是否有 agent_created 标记
    if [ -f "${skill_dir}/SKILL.md" ]; then
      has_agent_created=$(grep -l "agent_created: true" "${skill_dir}/SKILL.md" 2>/dev/null || true)
      if [ -n "$has_agent_created" ]; then
        mkdir -p "${PACKAGE_DIR}/skills/Tier2/${skill_name}"
        rsync -a --exclude='.git' --exclude='__pycache__' --exclude='onezion-*' \
          "${skill_src}/" "${PACKAGE_DIR}/skills/Tier2/${skill_name}/"
        TIER2_COUNT=$((TIER2_COUNT + 1))
      fi
    fi
  fi
done

echo "   Tier 1 (onezion-*): ${TIER1_COUNT} 个"
echo "   Tier 2 (agent_created): ${TIER2_COUNT} 个"

# ========== 层2: MCP 配置 ==========
echo "⚙️  导出 MCP 配置..."
if [ -f "$MCP_CONFIG" ]; then
  cp "$MCP_CONFIG" "${PACKAGE_DIR}/mcp/mcp.json"
  echo "   mcp.json 已导出"
else
  echo "   ⚠️ 未找到 mcp.json"
fi

# ========== 层3: Memory ==========
echo "🧠 导出 Memory..."
MEMORY_FILE="${WORKBUDDY_DIR}/memory/MEMORY.md"
if [ -f "$MEMORY_FILE" ]; then
  cp "$MEMORY_FILE" "${PACKAGE_DIR}/memory/MEMORY.md"
  echo "   MEMORY.md 已导出"
fi

# 每日记忆（最近 30 天）
if [ -d "${WORKBUDDY_DIR}/memory" ]; then
  find "${WORKBUDDY_DIR}/memory" -name "*.md" -not -name "MEMORY.md" -mtime -30 \
    -exec cp {} "${PACKAGE_DIR}/memory/daily/" \; 2>/dev/null || true
  DAILY_COUNT=$(ls "${PACKAGE_DIR}/memory/daily/"*.md 2>/dev/null | wc -l | tr -d ' ')
  echo "   每日记忆: ${DAILY_COUNT} 个文件"
fi

# ========== 层4: 聊天记录（双层策略） ==========
echo "💬 导出聊天记录（双层策略）..."

CONV_DB="${WORKBUDDY_DIR}/workbuddy.db"

# 4a: Sessions 元数据（原始版）
if [ -f "$CONV_DB" ]; then
  # sessions table stores conversation metadata
  sqlite3 "$CONV_DB" \
    "SELECT json_object('id', id, 'title', title, 'cwd', cwd, 'created_at', datetime(created_at/1000, 'unixepoch', 'localtime'), 'updated_at', datetime(updated_at/1000, 'unixepoch', 'localtime'), 'model', model)
     FROM sessions
     WHERE deleted_at IS NULL
     ORDER BY updated_at DESC
     LIMIT 500;" > "${PACKAGE_DIR}/chat_history/sessions_metadata.jsonl" 2>/dev/null || true
  SESSION_COUNT=$(wc -l < "${PACKAGE_DIR}/chat_history/sessions_metadata.jsonl" | tr -d ' ')
  echo "   元数据: ${SESSION_COUNT} 条 session 记录"
fi

# 4b: 原始聊天内容（JSONL files from projects directory）
PROJECTS_DIR="${WORKBUDDY_DIR}/projects"
if [ -d "$PROJECTS_DIR" ]; then
  mkdir -p "${PACKAGE_DIR}/chat_history/raw_messages"
  # Copy all .jsonl conversation files
  find "$PROJECTS_DIR" -name "*.jsonl" -exec cp {} "${PACKAGE_DIR}/chat_history/raw_messages/" \; 2>/dev/null || true
  MSG_COUNT=$(ls "${PACKAGE_DIR}/chat_history/raw_messages/"*.jsonl 2>/dev/null | wc -l | tr -d ' ')
  MSG_SIZE=$(du -sh "${PACKAGE_DIR}/chat_history/raw_messages/" 2>/dev/null | cut -f1)
  echo "   原始消息: ${MSG_COUNT} 个 JSONL 文件 (${MSG_SIZE})"
fi

# 4c: LLMWiki 简化版骨架（导入后由新 Agent 用 LLMWiki 生成完整简化版）
cat > "${PACKAGE_DIR}/chat_history/LLMWiki_simplified.md" << 'EOF'
# 聊天记录简化版 (LLMWiki)

> 此文件为骨架模板。导入后使用 LLMWiki skill 从 sessions_metadata.jsonl + raw_messages/ 生成完整简化版。

## 简化版说明

- **用途**: 快速概览历史对话，按主题索引，日常参考
- **生成方式**: LLMWiki 自动从原始聊天记录提取关键信息
- **格式**: 每条对话一个摘要条目，按主题/项目分类
- **原始版**: raw_messages/ 目录包含完整 JSONL 消息记录，支持深度检索

## 主题索引

> 导入后由 LLMWiki 自动填充

### Skills 开发
- [待生成]

### 学术研究
- [待生成]

### Agent 工具链
- [待生成]

### 日常生活
- [待生成]
EOF
echo "   LLMWiki 简化版骨架已生成（导入后由 LLMWiki 自动生成）"

# 生成上下文简介
cat > "${PACKAGE_DIR}/chat_history/context_brief.md" << 'EOF'
# 当前工作状态

> 此文件需要在导入时由新 Agent 或用户手动更新。

## 正在进行的工作
- [待填写]

## 近期优先事项
- [待填写]

## 关键决策记录
- [待填写]
EOF
echo "   context_brief.md 模板已生成（需手动填写）"

# ========== 层5: 密钥（可选） ==========
if [ "$INCLUDE_SECRETS" = true ]; then
  echo "🔑 导出密钥..."
  # Notion API Key
  NOTION_KEY=$(security find-generic-password -a "notion" -s "notion-api-key" -w 2>/dev/null || echo "")
  if [ -n "$NOTION_KEY" ]; then
    echo "NOTION_API_KEY=${NOTION_KEY}" > "${PACKAGE_DIR}/secrets/notion.env"
    chmod 600 "${PACKAGE_DIR}/secrets/notion.env"
    echo "   notion.env 已导出"
  fi

  # OpenRouter Key
  OPENROUTER_KEY=$(security find-generic-password -a "openrouter" -s "openrouter-api-key" -w 2>/dev/null || echo "")
  if [ -n "$OPENROUTER_KEY" ]; then
    echo "OPENROUTER_API_KEY=${OPENROUTER_KEY}" >> "${PACKAGE_DIR}/secrets/notion.env"
    echo "   openrouter key 已导出"
  fi

  echo "   ⚠️  secrets/ 目录包含敏感信息，请勿上传到公开仓库"
else
  echo "⏭️  跳过密钥导出（使用 --secrets 启用）"
fi

# ========== RAG 向量库（可选） ==========
if [ "$INCLUDE_RAG" = true ]; then
  RAG_DIR="${HOME}/.workbuddy/rag"
  if [ -d "$RAG_DIR" ]; then
    echo "📚 导出 RAG 向量库..."
    cp -r "$RAG_DIR" "${PACKAGE_DIR}/rag/"
    echo "   RAG 已导出"
  fi
fi

# ========== 生成 README.md ==========
echo "📝 生成 README.md..."
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
cat > "${PACKAGE_DIR}/README.md" << EOF
# OneZion Agent Migration Package

> 自动生成于 ${NOW}

## 快速导入指南

### 1. 安装 Skills

\`\`\`bash
# Tier 1 (必装)
cp -r skills/Tier1/* ~/.workbuddy/skills/

# Tier 2 (推荐)
cp -r skills/Tier2/* ~/.workbuddy/skills/
\`\`\`

### 2. 配置 MCP

将 \`mcp/mcp.json\` 的内容合并到 \`~/.workbuddy/mcp.json\`。
部分 MCP server 需要重新 OAuth 授权（Outlook、GitHub 等）。

### 3. 恢复 Memory

\`\`\`bash
cp memory/MEMORY.md ~/.workbuddy/memory/MEMORY.md
cp memory/daily/*.md ~/.workbuddy/memory/
\`\`\`

### 4. 导入密钥

如果包含 \`secrets/\` 目录：
\`\`\`bash
# Notion
security add-generic-password -a "notion" -s "notion-api-key" -w "YOUR_KEY" -T "" -U

# 其他 key 按需添加
\`\`\`

或者手动添加到 macOS Keychain。

### 5. 填写上下文简介

编辑 \`chat_history/context_brief.md\`，填写当前工作状态。

## 分层说明

| 层 | 目录 | 说明 |
|----|------|------|
| Skills | skills/ | Tier1 = onezion-* 前缀（必带）；Tier2 = agent_created 的其他 skills |
| MCP | mcp/ | MCP server 配置 |
| Memory | memory/ | 长期 + 每日记忆 |
| 聊天记录 | chat_history/ | 元数据 + 原始 JSONL + LLMWiki 简化版 + 上下文简介 |
| 密钥 | secrets/ | API keys（可选导出） |

## 注意事项

- 部分 MCP server 需重新授权（Outlook、GitHub OAuth）
- ScreenPipe 录制数据不包含在内（体积太大 + 隐私风险）
- RAG 向量库需使用 --rag 参数单独导出
- ⚠️ 不要将含 secrets/ 的 zip 上传到公开仓库
EOF

# ========== 生成 meta.json ==========
TOTAL_SIZE=$(du -sm "${PACKAGE_DIR}" | cut -f1)
cat > "${PACKAGE_DIR}/meta.json" << EOF
{
  "version": "1.0.0",
  "exported_at": "${NOW}",
  "source_platform": "workbuddy",
  "source_device": "$(sw_vers -productName) $(sw_vers -productVersion) ($(uname -m))",
  "user": "$(whoami)",
  "tier1_skills_count": ${TIER1_COUNT},
  "tier2_skills_count": ${TIER2_COUNT},
  "total_size_mb": ${TOTAL_SIZE},
  "include_secrets": ${INCLUDE_SECRETS},
  "include_rag": ${INCLUDE_RAG}
}
EOF

# ========== 打包 ==========
echo ""
echo "📦 打包中..."
# 确保输出目录存在
mkdir -p "$(dirname "$OUTPUT_PATH")"

cd "$STAGING_DIR"
zip -r "$OUTPUT_PATH" "onezion-agent-migrate/" -x "*.DS_Store" >/dev/null 2>&1
FINAL_SIZE=$(du -sh "$OUTPUT_PATH" | cut -f1)

# 清理临时目录
rm -rf "$STAGING_DIR"

echo ""
echo "✅ 导出完成！"
echo "   文件: ${OUTPUT_PATH}"
echo "   大小: ${FINAL_SIZE}"
echo "   Tier 1 Skills: ${TIER1_COUNT}"
echo "   Tier 2 Skills: ${TIER2_COUNT}"
echo ""
echo "⚠️  如果包含密钥，请妥善保管此文件，不要上传到公开仓库。"
