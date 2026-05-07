#!/usr/bin/env python3
"""
onezion-wechat-channels-live — 录制+总结一体化脚本

用法:
  # 自动解析流 URL 并录制
  python3 record_and_summarize.py --url <直播间URL> [--duration 3600] [--summarize]

  # 直接用流 URL 录制（视频号等）
  python3 record_and_summarize.py --stream-url <流URL> [--duration 3600] [--summarize]

  # 仅检查依赖
  python3 record_and_summarize.py --check

功能:
  1. 通过 streamget 库解析直播流 URL（50+ 平台）
  2. 使用 FFmpeg 录制
  3. 录制完成后（可选）调用 onezion-video-summarize 总结
"""

import argparse
import asyncio
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# streamget 平台映射表
PLATFORM_MAP = {
    "bilibili": "BilibiliLiveStream",
    "douyin": "DouyinLiveStream",
    "douyu": "DouyuLiveStream",
    "huya": "HuyaLiveStream",
    "kuaishou": "KwaiLiveStream",
    "kwai": "KwaiLiveStream",
    "twitch": "TwitchLiveStream",
    "youtube": "YoutubeLiveStream",
    "tiktok": "TikTokLiveStream",
    "yy": "YYLiveStream",
    "inke": "InkeLiveStream",
    "acfun": "AcfunLiveStream",
    "rednote": "RedNoteLiveStream",
    "xiaohongshu": "RedNoteLiveStream",
    "taobao": "TaobaoLiveStream",
    "jd": "JDLiveStream",
    "shopee": "ShopeeLiveStream",
    "liveme": "LiveMeLiveStream",
    "soop": "SoopLiveStream",
    "twitcasting": "TwitCastingLiveStream",
    "chzzk": "ChzzkLiveStream",
    "bigo": "BigoLiveStream",
    "popkon": "PopkonTVLiveStream",
    "flex": "FlexTVLiveStream",
    "pandtv": "PandaLiveStream",
    "showroom": "ShowRoomLiveStream",
    "netease": "NeteaseLiveStream",
    "migu": "MiguLiveStream",
    "kugou": "KugouLiveStream",
    "weibo": "WeiboLiveStream",
    "zhihu": "ZhihuLiveStream",
    "blued": "BluedLiveStream",
    "huajiao": "HuajiaoLiveStream",
    "look": "LookLiveStream",
    "sixroom": "SixRoomLiveStream",
    "lang": "LangLiveStream",
    "laixiu": "LaixiuLiveStream",
    "huamao": "HuamaoLiveStream",
    "piaopaio": "PiaopaioLiveStream",
    "vvxq": "VVXQLiveStream",
    "yinbo": "YinboLiveStream",
    "yiqi": "YiqiLiveStream",
    "qiandurebo": "QiandureboLiveStream",
    "xindongrebo": "XindongreboLiveStream",
    "winktv": "WinkTVLiveStream",
    "lehai": "LehaiLiveStream",
    "lianJie": "LianJieLiveStream",
    "maoer": "MaoerLiveStream",
    "faceit": "FaceitLiveStream",
    "picarto": "PicartoLiveStream",
    "changliao": "ChangliaoLiveStream",
    "haixiu": "HaixiuLiveStream",
    "baidu": "BaiduLiveStream",
}


def check_dependencies():
    """检查必要的依赖"""
    errors = []

    # 检查 FFmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        ver_line = result.stdout.decode().split("\n")[0]
        print(f"  ✅ {ver_line}")
    except (FileNotFoundError, subprocess.CalledProcessError):
        errors.append("FFmpeg 未安装。请运行: brew install ffmpeg")

    # 检查 Python 版本
    if sys.version_info < (3, 10):
        errors.append(f"需要 Python 3.10+，当前: {sys.version}")
    else:
        print(f"  ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # 检查 streamget
    try:
        import streamget
        print(f"  ✅ streamget {streamget.__version__}")
    except ImportError:
        errors.append("streamget 未安装。请运行: pip install streamget")

    if errors:
        for e in errors:
            print(f"  ❌ {e}", file=sys.stderr)
        sys.exit(1)

    print("\n  ✅ 所有依赖已就绪")


def detect_platform(url: str) -> str:
    """根据 URL 自动检测平台"""
    url_lower = url.lower()

    patterns = {
        "bilibili": r"bilibili\.com",
        "douyin": r"douyin\.com|iesdouyin\.com",
        "douyu": r"douyu\.com",
        "huya": r"huya\.com",
        "kuaishou": r"kuaishou\.com|kslive\.com",
        "twitch": r"twitch\.tv",
        "youtube": r"youtube\.com|youtu\.be",
        "tiktok": r"tiktok\.com",
        "yy": r"yy\.com",
        "acfun": r"acfun\.cn",
        "rednote": r"xiaohongshu\.com|xhslink\.com",
        "taobao": r"taobao\.com|tb\.live",
        "jd": r"jd\.com",
        "shopee": r"shopee\.",
        "liveme": r"liveme\.com",
        "soop": r"soop\.com|afreecatv\.com",
        "twitcasting": r"twitcasting\.tv",
        "chzzk": r"chzzk\.naver\.com",
        "bigo": r"bigo\.tv",
        "netease": r"cc\.163\.com",
        "migu": r"migu\.cn",
        "kugou": r"kugou\.com",
        "weibo": r"weibo\.com",
        "zhihu": r"zhihu\.com",
    }

    for platform, pattern in patterns.items():
        if re.search(pattern, url_lower):
            return platform

    return "unknown"


async def resolve_stream_url(url: str, platform: str = "auto") -> dict:
    """
    使用 streamget 解析直播流 URL。

    返回: {"stream_url": "...", "anchor_name": "...", "title": "...", "live_status": ...}
    """
    import streamget

    if platform == "auto":
        platform = detect_platform(url)

    if platform == "unknown":
        raise ValueError(f"无法识别平台: {url}。请用 --platform 手动指定。")

    class_name = PLATFORM_MAP.get(platform)
    if not class_name:
        raise ValueError(f"不支持的平台: {platform}")

    # 获取平台类
    platform_class = getattr(streamget, class_name, None)
    if not platform_class:
        raise ValueError(f"streamget 中找不到 {class_name}")

    print(f"  📡 正在解析 {platform} 直播流...")
    instance = platform_class()

    try:
        result = await instance.fetch_web_stream_data(url)
        return result
    except Exception as e:
        raise RuntimeError(f"解析直播流失败: {e}")


def record_stream(stream_url: str, output_path: str, duration: int = None, use_2pass: bool = False):
    """
    使用 FFmpeg 录制直播流。

    Args:
        stream_url: 直播流 URL
        output_path: 输出文件路径
        duration: 录制时长（秒），None 则持续录制
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "10",
        "-i", stream_url,
        "-c", "copy",
    ]

    if duration:
        cmd.extend(["-t", str(duration)])

    cmd.append(output_path)

    print(f"\n  🎬 开始录制")
    print(f"     输出: {output_path}")
    if duration:
        mins = duration // 60
        print(f"     时长: {mins} 分钟")
    else:
        print(f"     模式: 持续录制（Ctrl+C 停止）")

    start_time = time.time()

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # 实时显示进度
        while process.poll() is None:
            elapsed = int(time.time() - start_time)
            mins, secs = divmod(elapsed, 60)
            hours, mins = divmod(mins, 60)
            print(f"\r     ⏱️  已录制: {hours:02d}:{mins:02d}:{secs:02d}", end="", flush=True)
            time.sleep(1)

        elapsed = int(time.time() - start_time)
        mins, secs = divmod(elapsed, 60)
        hours, mins = divmod(mins, 60)
        print(f"\r     ⏱️  录制完成: {hours:02d}:{mins:02d}:{secs:02d}")

    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        print("\n     ⏹️  录制已手动停止")

    # 检查输出文件
    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"     📁 文件大小: {size_mb:.1f} MB")
        return output_path
    else:
        print("     ❌ 录制文件未生成", file=sys.stderr)
        return None


def summarize_video(video_path: str, output_dir: str = None):
    """生成总结指令，提示用户调用 onezion-video-summarize skill"""
    print(f"\n  📝 视频总结")
    print(f"     文件: {video_path}")
    print(f"     请在 WorkBuddy 中执行:")
    print(f"     @skill:onezion-video-summarize {video_path}")

    # 生成总结指令文件
    summarize_cmd = {
        "video_path": video_path,
        "output_dir": output_dir or str(Path(video_path).parent),
        "timestamp": datetime.now().isoformat(),
        "instruction": f"@skill:onezion-video-summarize {video_path}"
    }

    cmd_file = Path(video_path).with_suffix(".summarize.json")
    with open(cmd_file, "w", encoding="utf-8") as f:
        json.dump(summarize_cmd, f, ensure_ascii=False, indent=2)

    print(f"     指令已保存: {cmd_file}")
    return str(cmd_file)


def main():
    parser = argparse.ArgumentParser(
        description="多平台直播录制 + 智能总结",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 录制 B站直播 1 小时
  python3 record_and_summarize.py --url https://live.bilibili.com/12345 --duration 3600

  # 录制并自动总结
  python3 record_and_summarize.py --url https://live.bilibili.com/12345 --duration 3600 --summarize

  # 直接用流 URL 录制（视频号等不支持自动解析的平台）
  python3 record_and_summarize.py --stream-url "https://pull-flv-xxx.flv" --output recording.flv

支持的平台: bilibili, douyin, douyu, huya, kuaishou, twitch, youtube, tiktok, yy,
acfun, rednote, taobao, jd, shopee, liveme, soop, twitcasting, chzzk, bigo 等 50+
        """
    )

    parser.add_argument("--url", help="直播间 URL（自动解析流地址）")
    parser.add_argument("--stream-url", help="直接提供直播流 URL（跳过自动解析）")
    parser.add_argument("--platform", default="auto", help="平台名称（默认自动识别）")
    parser.add_argument("--duration", type=int, help="录制时长（秒），不指定则持续录制")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--output-dir", default=os.path.expanduser("~/records/live"),
                        help="输出目录（默认 ~/records/live/）")
    parser.add_argument("--summarize", action="store_true", help="录制完成后自动总结")
    parser.add_argument("--check", action="store_true", help="仅检查依赖")

    args = parser.parse_args()

    print("\n  === onezion-wechat-channels-live ===\n")
    print("  [1] 检查依赖...")
    check_dependencies()

    if args.check:
        return

    # 确定输出路径
    if args.output:
        output_path = args.output
    else:
        os.makedirs(args.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform = args.platform if args.platform != "auto" else "live"
        output_path = os.path.join(args.output_dir, f"{platform}_{timestamp}.flv")

    # 获取直播流 URL
    if args.stream_url:
        stream_url = args.stream_url
        print(f"\n  [2] 使用直接提供的流 URL")
        print(f"     URL: {stream_url[:80]}...")
    elif args.url:
        print(f"\n  [2] 解析直播流 URL...")
        try:
            result = asyncio.run(resolve_stream_url(args.url, args.platform))
            if isinstance(result, dict):
                stream_url = result.get("stream_url") or result.get("url")
                anchor = result.get("anchor_name", "未知")
                title = result.get("title", "")
                status = result.get("live_status", "未知")
                print(f"     主播: {anchor}")
                if title:
                    print(f"     标题: {title}")
                print(f"     状态: {status}")
                print(f"     流URL: {stream_url[:80]}..." if stream_url else "     流URL: 未获取到")
            else:
                stream_url = str(result)
        except Exception as e:
            print(f"     ❌ {e}", file=sys.stderr)
            print(f"\n     提示: 你可以手动获取流 URL 后用 --stream-url 参数直接录制")
            sys.exit(1)
    else:
        print("  ❌ 请提供 --url 或 --stream-url 参数", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    if not stream_url:
        print("  ❌ 未能获取到直播流 URL", file=sys.stderr)
        sys.exit(1)

    # 开始录制
    print(f"\n  [3] 开始录制...")
    result = record_stream(stream_url, output_path, args.duration)

    # 总结
    if result and args.summarize:
        print(f"\n  [4] 生成总结指令...")
        summarize_video(result, args.output_dir)
    elif result:
        print(f"\n  [4] 录制完成（未启用自动总结，使用 --summarize 参数启用）")

    print("\n  ✅ 任务完成\n")


if __name__ == "__main__":
    main()
