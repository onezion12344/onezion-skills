#!/bin/bash
# onezion-wechat-channels-live — 安装脚本
# 安装 StreamCap + 检查 FFmpeg

set -eo pipefail

STREAMCAP_DIR="$HOME/Tools/StreamCap"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== onezion-wechat-channels-live 安装 ===${NC}"

# 1. 检查 Python 版本
echo -e "\n${YELLOW}[1/5] 检查 Python 版本...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | sed 's/Python \([0-9]*\.[0-9]*\).*/\1/')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}需要 Python 3.10+，当前版本: $PYTHON_VERSION${NC}"
    echo "请先升级 Python: brew install python@3.12"
    exit 1
fi
echo -e "  Python $PYTHON_VERSION ✓"

# 2. 检查 FFmpeg
echo -e "\n${YELLOW}[2/5] 检查 FFmpeg...${NC}"
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -1)
    echo -e "  $FFMPEG_VERSION ✓"
else
    echo -e "${RED}FFmpeg 未安装${NC}"
    if command -v brew &> /dev/null; then
        echo "正在通过 Homebrew 安装 FFmpeg..."
        brew install ffmpeg
    else
        echo "请手动安装 FFmpeg: https://ffmpeg.org/download.html"
        exit 1
    fi
fi

# 3. 安装 streamget（核心流获取库）
echo -e "\n${YELLOW}[3/5] 安装 streamget...${NC}"
pip3 install streamget --upgrade 2>/dev/null || pip3 install streamget
echo -e "  streamget 安装完成 ✓"

# 4. 克隆 StreamCap 仓库
echo -e "\n${YELLOW}[4/5] 克隆 StreamCap 仓库...${NC}"
if [ -d "$STREAMCAP_DIR" ]; then
    echo -e "  目录已存在: $STREAMCAP_DIR，更新中..."
    cd "$STREAMCAP_DIR" && git pull
else
    git clone https://github.com/ihmily/StreamCap.git "$STREAMCAP_DIR"
    cd "$STREAMCAP_DIR"
fi
echo -e "  StreamCap 仓库就绪 ✓"

# 5. 安装 StreamCap 依赖
echo -e "\n${YELLOW}[5/5] 安装 StreamCap Python 依赖...${NC}"
pip3 install -r "$STREAMCAP_DIR/requirements.txt" 2>/dev/null || {
    echo -e "${YELLOW}  requirements.txt 安装失败，尝试单独安装核心包...${NC}"
    pip3 install streamget pyinstaller
}

# 创建 .env 配置文件（如果不存在）
if [ ! -f "$STREAMCAP_DIR/.env" ] && [ -f "$STREAMCAP_DIR/.env.example" ]; then
    cp "$STREAMCAP_DIR/.env.example" "$STREAMCAP_DIR/.env"
    echo -e "  创建默认 .env 配置文件 ✓"
fi

# 创建录制输出目录
mkdir -p "$STREAMCAP_DIR/records"

echo -e "\n${GREEN}=== 安装完成 ===${NC}"
echo ""
echo "使用方式："
echo "  桌面模式: cd ~/Tools/StreamCap && python3 main.py"
echo "  Web 模式: cd ~/Tools/StreamCap && python3 main.py --web"
echo "  录制目录: ~/Tools/StreamCap/records/"
echo ""
echo "视频号直播录制（macOS）："
echo "  1. 使用抓包工具（Charles/Proxyman）捕获直播流 URL"
echo "  2. ffmpeg -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -i \"流URL\" -c copy output.flv"
echo ""
echo "视频号直播录制（Windows）："
echo "  下载 wechatVideoDownload: https://pan.quark.cn/s/02054d6f9664"
