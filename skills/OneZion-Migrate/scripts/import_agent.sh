#!/usr/bin/env bash
# OneZion-Migrate: Agent 环境导入脚本
# 从迁移 zip 包恢复 WorkBuddy 环境
set -euo pipefail

# --- 参数解析 ---
ZIP_PATH=""
DRY_RUN=false
SKIP_SECRETS=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run) DRY_RUN=true; shift ;;
    --skip-secrets) SKIP_SECRETS=true; shift ;;
    -*) echo "Unknown option: $1"; exit 1 ;;
    *)
      if [ -z "$ZIP_PATH" ]; then
        ZIP_PATH="$1"
      fi
      shift
      ;;
  esac
done

if [ -z "$ZIP_PATH" ]; then
  echo "用法: import_agent.sh <path-to-migrate.zip> [--dry-run] [--skip-secrets]"
  exit 1
fi

if [ ! -f "$ZIP_PATH" ]; then
  echo "❌ 文件不存在: $ZIP_PATH"
  exit 1
fi

WORKBUDDY_DIR="${HOME}/.workbuddy"
STAGING_DIR=$(mktemp -d)

echo "🔄 OneZion-Migrate Agent Import"
echo "   来源: ${ZIP_PATH}"
echo ""

# ========== 解压 ==========
echo "📦 解压迁移包..."
unzip -q "$ZIP_PATH" -d "$STAGING_DIR"
PACKAGE_DIR="${STAGING_DIR}/onezion-agent-migrate"

if [ ! -d "$PACKAGE_DIR" ]; then
  echo "❌ 无效的迁移包（缺少 onezion-agent-migrate 目录）"
  rm -rf "$STAGING_DIR"
  exit 1
fi

# ========== 读取元数据 ==========
if [ -f "${PACKAGE_DIR}/meta.json" ]; then
  echo "📋 迁移包信息:"
  python3 -c "
import json
with open('${PACKAGE_DIR}/meta.json') as f:
    m = json.load(f)
print(f'   来源平台: {m.get(\"source_platform\", \"unknown\")}')
print(f'   来源设备: {m.get(\"source_device\", \"unknown\")}')
print(f'   导出时间: {m.get(\"exported_at\", \"unknown\")}')
print(f'   Tier 1 Skills: {m.get(\"tier1_skills_count\", 0)}')
print(f'   Tier 2 Skills: {m.get(\"tier2_skills_count\", 0)}')
print(f'   包含密钥: {m.get(\"include_secrets\", False)}')
" 2>/dev/null || true
  echo ""
fi

# ========== 读取 README ==========
if [ -f "${PACKAGE_DIR}/README.md" ]; then
  echo "📖 请阅读 README.md 了解配置要求"
  echo "   (按 Enter 继续，Ctrl+C 取消)"
  if [ "$DRY_RUN" = false ]; then
    read -r
  fi
  echo ""
fi

# ========== Dry Run ==========
if [ "$DRY_RUN" = true ]; then
  echo "🔍 Dry Run 模式 — 仅预览，不执行任何操作"
  echo ""
  echo "将要导入的内容:"
  echo ""

  # Skills
  if [ -d "${PACKAGE_DIR}/skills/Tier1" ]; then
    echo "  Skills (Tier 1):"
    for d in "${PACKAGE_DIR}/skills/Tier1"/*/; do
      [ -d "$d" ] && echo "    + $(basename "$d")"
    done
  fi
  if [ -d "${PACKAGE_DIR}/skills/Tier2" ]; then
    echo "  Skills (Tier 2):"
    for d in "${PACKAGE_DIR}/skills/Tier2"/*/; do
      [ -d "$d" ] && echo "    + $(basename "$d")"
    done
  fi

  # MCP
  if [ -f "${PACKAGE_DIR}/mcp/mcp.json" ]; then
    echo "  MCP: mcp.json"
  fi

  # Memory
  if [ -f "${PACKAGE_DIR}/memory/MEMORY.md" ]; then
    echo "  Memory: MEMORY.md"
  fi
  DAILY_COUNT=$(ls "${PACKAGE_DIR}/memory/daily/"*.md 2>/dev/null | wc -l | tr -d ' ')
  if [ "$DAILY_COUNT" -gt 0 ]; then
    echo "  Memory daily: ${DAILY_COUNT} 个文件"
  fi

  # Secrets
  if [ -d "${PACKAGE_DIR}/secrets" ] && [ "$(ls -A "${PACKAGE_DIR}/secrets" 2>/dev/null)" ]; then
    echo "  Secrets: $(ls "${PACKAGE_DIR}/secrets/" | tr '\n' ', ')"
  fi

  echo ""
  echo "✅ Dry run 完成。去掉 --dry-run 以执行实际导入。"
  rm -rf "$STAGING_DIR"
  exit 0
fi

# ========== 开始导入 ==========
echo "🚀 开始导入..."

# --- Skills ---
echo ""
echo "📦 安装 Skills..."

IMPORTED=0
SKIPPED=0

for tier in Tier1 Tier2; do
  TIER_DIR="${PACKAGE_DIR}/skills/${tier}"
  [ -d "$TIER_DIR" ] || continue

  for skill_dir in "${TIER_DIR}"/*/; do
    [ -d "$skill_dir" ] || continue
    skill_name=$(basename "$skill_dir")
    target="${WORKBUDDY_DIR}/skills/${skill_name}"

    if [ -d "$target" ]; then
      echo "   ⏭️  ${skill_name} (已存在，跳过)"
      SKIPPED=$((SKIPPED + 1))
    else
      cp -r "$skill_dir" "$target"
      echo "   ✅ ${skill_name} (${tier})"
      IMPORTED=$((IMPORTED + 1))
    fi
  done
done

echo "   导入: ${IMPORTED}，跳过: ${SKIPPED}"

# --- MCP ---
echo ""
echo "⚙️  MCP 配置..."
if [ -f "${PACKAGE_DIR}/mcp/mcp.json" ]; then
  if [ -f "${WORKBUDDY_DIR}/mcp.json" ]; then
    echo "   ⚠️  已有 mcp.json，备份为 mcp.json.bak"
    cp "${WORKBUDDY_DIR}/mcp.json" "${WORKBUDDY_DIR}/mcp.json.bak"
  fi
  cp "${PACKAGE_DIR}/mcp/mcp.json" "${WORKBUDDY_DIR}/mcp.json"
  echo "   ✅ mcp.json 已导入"
  echo "   ⚠️  部分 MCP server 可能需要重新 OAuth 授权（Outlook、GitHub 等）"
else
  echo "   ⏭️  无 MCP 配置"
fi

# --- Memory ---
echo ""
echo "🧠 Memory..."
mkdir -p "${WORKBUDDY_DIR}/memory"

if [ -f "${PACKAGE_DIR}/memory/MEMORY.md" ]; then
  if [ -f "${WORKBUDDY_DIR}/memory/MEMORY.md" ]; then
    echo "   ⚠️  已有 MEMORY.md，备份为 MEMORY.md.bak"
    cp "${WORKBUDDY_DIR}/memory/MEMORY.md" "${WORKBUDDY_DIR}/memory/MEMORY.md.bak"
  fi
  cp "${PACKAGE_DIR}/memory/MEMORY.md" "${WORKBUDDY_DIR}/memory/MEMORY.md"
  echo "   ✅ MEMORY.md 已导入"
fi

DAILY_IMPORTED=0
for daily in "${PACKAGE_DIR}/memory/daily/"*.md; do
  [ -f "$daily" ] || continue
  fname=$(basename "$daily")
  target="${WORKBUDDY_DIR}/memory/${fname}"
  if [ -f "$target" ]; then
    # 合并而非覆盖
    echo "" >> "$target"
    echo "# --- 导入自迁移包 (${fname}) ---" >> "$target"
    cat "$daily" >> "$target"
    echo "   🔀 ${fname} (已合并)"
  else
    cp "$daily" "$target"
  fi
  DAILY_IMPORTED=$((DAILY_IMPORTED + 1))
done
[ "$DAILY_IMPORTED" -gt 0 ] && echo "   ✅ 每日记忆: ${DAILY_IMPORTED} 个文件"

# --- Chat History ---
echo ""
echo "💬 聊天记录..."
if [ -f "${PACKAGE_DIR}/chat_history/conversations.jsonl" ]; then
  HISTORY_DIR="${WORKBUDDY_DIR}/migration_history"
  mkdir -p "$HISTORY_DIR"
  cp "${PACKAGE_DIR}/chat_history/conversations.jsonl" "$HISTORY_DIR/"
  if [ -f "${PACKAGE_DIR}/chat_history/context_brief.md" ]; then
    cp "${PACKAGE_DIR}/chat_history/context_brief.md" "$HISTORY_DIR/"
  fi
  echo "   ✅ 已保存到 ${HISTORY_DIR}/（供新 Agent 参考）"
else
  echo "   ⏭️  无聊天记录"
fi

# --- Secrets ---
echo ""
echo "🔑 密钥..."
if [ "$SKIP_SECRETS" = true ]; then
  echo "   ⏭️  已跳过密钥导入"
elif [ -d "${PACKAGE_DIR}/secrets" ] && [ "$(ls -A "${PACKAGE_DIR}/secrets" 2>/dev/null)" ]; then
  echo "   ⚠️  检测到密钥文件。以下密钥需要手动添加到 Keychain:"
  for secret_file in "${PACKAGE_DIR}/secrets"/*; do
    [ -f "$secret_file" ] || continue
    echo "   - $(basename "$secret_file")"
  done
  echo ""
  echo "   使用以下命令导入（替换 YOUR_KEY）:"
  echo "   security add-generic-password -a \"notion\" -s \"notion-api-key\" -w \"YOUR_KEY\" -T \"\" -U"
else
  echo "   ⏭️  无密钥文件"
fi

# ========== 清理 ==========
rm -rf "$STAGING_DIR"

echo ""
echo "✅ 导入完成！"
echo ""
echo "📋 后续步骤:"
echo "   1. 确认 Skills 已正确安装: ~/.workbuddy/skills/"
echo "   2. 检查 MCP 配置: ~/.workbuddy/mcp.json"
echo "   3. 如有密钥，手动添加到 Keychain"
echo "   4. 填写 migration_history/context_brief.md"
echo "   5. 重启 WorkBuddy 使配置生效"
