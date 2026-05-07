#!/usr/bin/env python3
"""
onezion-video-compress: 自动视频压缩工具
用法: python3 compress.py <input> [options]

选项:
  -o, --output PATH    输出路径 (默认: 原文件名_compressed.mp4)
  -t, --target SIZE    目标大小，支持单位 (如 900MB, 1GB, 500MB)
  -p, --preset PRESET  ffmpeg preset (ultrafast/superfast/veryfast/faster/fast/medium/slow)
                        默认自动选择
  -m, --mode MODE      压缩模式: 2pass(默认) 或 crf
  --crf VAL            CRF 模式时的质量值 (默认28)
  -s, --scale H        .他缩放到高度 (如 720, 1080)，默认自动
  -r, --fps FPS        帧率 (默认保持原帧率)
  --audio-bitrate RATE 音频码率 (默认128k)

示例:
  python3 compress.py recording.mov -t 900MB -o output.mp4
  python3 compress.py input.mp4 -t 1GB --crf 26 -p fast
"""

import argparse
import subprocess
import json
import sys
import os
import re


def run_cmd(cmd, capture=False):
    """运行命令，返回 (returncode, stdout, stderr)"""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=capture,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def get_video_info(path):
    """用 ffprobe 获取视频信息"""
    cmd = (
        f'ffprobe -v quiet -print_format json -show_format -show_streams "{path}"'
    )
    code, stdout, stderr = run_cmd(cmd, capture=True)
    if code != 0:
        print(f"[ERROR] ffprobe 失败: {stderr}")
        sys.exit(1)

    data = json.loads(stdout)

    # 找到视频流
    video_stream = None
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            video_stream = s
            break

    if not video_stream:
        print("[ERROR] 未找到视频流")
        sys.exit(1)

    duration = float(data["format"].get("duration", 0))
    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    fps_str = video_stream.get("r_frame_rate", "30/1")
    # 解析帧率分数
    if "/" in fps_str:
        num, den = fps_str.split("/")
        fps = float(num) / float(den) if float(den) != 0 else 30.0
    else:
        fps = float(fps_str)

    has_audio = any(
        s.get("codec_type") == "audio" for s in data.get("streams", [])
    )

    return {
        "duration": duration,
        "width": width,
        "height": height,
        "fps": fps,
        "has_audio": has_audio,
        "format": data["format"].get("format_name", ""),
    }


def parse_size(size_str):
    """解析大小字符串，返回 MB"""
    size_str = size_str.strip().upper()
    match = re.match(r"([\d.]+)\s*(GB|MB|KB)?", size_str)
    if not match:
        raise ValueError(f"无法解析大小: {size_str}")
    val = float(match.group(1))
    unit = (match.group(2) or "MB").upper()
    if unit == "GB":
        return val * 1024
    elif unit == "MB":
        return val
    elif unit == "KB":
        return val / 1024
    return val


def auto_preset(duration_sec, height):
    """根据视频时长和分辨率自动选择 preset"""
    # 长视频或高分辨率 → 更快的 preset
    if duration_sec > 7200 or height >= 2160:  # >2小时 或 4K
        return "fast"
    elif duration_sec > 3600 or height >= 1080:  # >1小时 或 1080p
        return "medium"
    else:
        return "slow"


def auto_scale(height, target_mb, duration_sec):
    """根据目标大小和时长自动决定是否缩放"""
    # 如果目标码率很低，建议缩放
    # 目标视频码率 (kbps)
    target_bitrate_k = (target_mb * 8192) / duration_sec
    if height > 720 and target_bitrate_k < 1500:
        return 720
    elif height > 1080 and target_bitrate_k < 3000:
        return 1080
    return None  # 不缩放


def build_ffmpeg_cmd(
    input_path, output_path, video_bitrate_k, audio_bitrate="128k",
    preset="medium", scale=None, fps=None, has_audio=True,
    pass_num=1, pass_log="/tmp/ffmpeg2pass", mode="2pass"
):
    """构建 ffmpeg 命令"""
    cmd = ["ffmpeg", "-y", "-i", input_path]

    # 视频滤镜
    vf_parts = []
    if scale:
        vf_parts.append(f"scale=-2:{scale}")
    if fps:
        vf_parts.append(f"fps={fps}")
    if vf_parts:
        cmd += ["-vf", ",".join(vf_parts)]

    # 视频编码参数
    cmd += ["-c:v", "libx264", "-preset", preset]

    if mode == "2pass":
        if pass_num == 1:
            cmd += ["-b:v", f"{video_bitrate_k}k", "-pass", "1",
                    "-passlogfile", pass_log, "-an", "-f", "null", "/dev/null"]
            return " ".join(f'"{x}"' if " " in str(x) or x.startswith("/") else x for x in cmd)
        else:
            cmd += ["-b:v", f"{video_bitrate_k}k", "-pass", "2",
                    "-passlogfile", pass_log]
    else:  # CRF mode
        cmd += [f"-crf", str(video_bitrate_k)]  # CRF value

    # 音频
    if has_audio:
        cmd += ["-c:a", "aac", "-b:a", audio_bitrate]
    else:
        cmd += ["-an"]

    cmd += ["-movflags", "+faststart", output_path]
    return " ".join(f'"{x}"' if (" " in str(x) or (isinstance(x, str) and x.startswith("/"))) and not x.startswith("-") else x for x in cmd)


def compress_2pass(input_path, output_path, target_mb, info, args):
    """2-pass 压缩"""
    duration = info["duration"]
    # 视频目标码率 = (总目标比特 - 音频比特) / 时长
    # 音频约占用 128kbps = 每秒 16KB = 每分钟 ~1MB
    audio_mb = (128 * 1024 / 8) * duration / 1024 / 1024
    video_target_mb = target_mb - audio_mb * 1.1  # 留10%余量
    video_bitrate_k = int((video_target_mb * 8192) / duration)  # kbps

    # 码率下限保护
    video_bitrate_k = max(video_bitrate_k, 300)
    # 码率上限保护（不压缩到比原片码率还高）
    max_br = int((target_mb * 8192) / duration)
    video_bitrate_k = min(video_bitrate_k, max_br)

    preset = args.preset or auto_preset(duration, info["height"])
    scale = args.scale or auto_scale(info["height"], target_mb, duration)
    fps = args.fps

    print(f"[INFO] 模式: 2-pass")
    print(f"[INFO] 视频时长: {duration:.0f}s ({duration/3600:.1f}h)")
    print(f"[INFO] 分辨率: {info['width']}x{info['height']}")
    print(f"[INFO] 目标视频码率: {video_bitrate_k}kbps")
    print(f"[INFO] Preset: {preset}")
    if scale:
        print(f"[INFO] 缩放到: -2:{scale}")

    pass_log = "/tmp/ffmpeg2pass"

    vf_parts = []
    if scale:
        vf_parts.append(f"scale=-2:{scale}")
    if fps:
        vf_parts.append(f"fps={fps}")

    # Pass 1
    print("\n[PASS 1/2] 分析中...")
    cmd1 = f'ffmpeg -y -i "{input_path}"'
    if vf_parts:
        cmd1 += f' -vf "{",".join(vf_parts)}"'
    cmd1 += (
        f' -c:v libx264 -preset {preset}'
        f' -b:v {video_bitrate_k}k'
        f' -pass 1 -passlogfile "{pass_log}"'
        f' -an -f null /dev/null'
    )
    print(f"[CMD] {cmd1}")
    code1, _, err1 = run_cmd(cmd1, capture=True)
    if code1 != 0:
        print(f"[ERROR] Pass 1 失败:\n{err1[-2000:]}")
        sys.exit(1)

    # Pass 2
    print("\n[PASS 2/2] 编码中...")
    cmd2 = f'ffmpeg -y -i "{input_path}"'
    if vf_parts:
        cmd2 += f' -vf "{",".join(vf_parts)}"'
    cmd2 += (
        f' -c:v libx264 -preset {preset}'
        f' -b:v {video_bitrate_k}k'
        f' -pass 2 -passlogfile "{pass_log}"'
    )
    if info["has_audio"]:
        cmd2 += f' -c:a aac -b:a {args.audio_bitrate or "128k"}'
    else:
        cmd2 += ' -an'
    cmd2 += f' -movflags +faststart "{output_path}"'

    print(f"[CMD] {cmd2}")
    code2, _, err2 = run_cmd(cmd2, capture=True)
    if code2 != 0:
        print(f"[ERROR] Pass 2 失败:\n{err2[-2000:]}")
        sys.exit(1)

    return video_bitrate_k


def compress_crf(input_path, output_path, info, args):
    """CRF 模式压缩"""
    preset = args.preset or auto_preset(info["duration"], info["height"])
    scale = args.scale
    fps = args.fps
    crf = args.crf or 28

    print(f"[INFO] 模式: CRF {crf}")
    print(f"[INFO] Preset: {preset}")
    if scale:
        print(f"[INFO] 缩放到: -2:{scale}")

    cmd = f'ffmpeg -y -i "{input_path}"'
    vf_parts = []
    if scale:
        vf_parts.append(f"scale=-2:{scale}")
    if fps:
        vf_parts.append(f"fps={fps}")
    if vf_parts:
        cmd += f' -vf "{",".join(vf_parts)}"'
    cmd += (
        f' -c:v libx264 -preset {preset}'
        f' -crf {crf}'
    )
    if info["has_audio"]:
        cmd += f' -c:a aac -b:a {args.audio_bitrate or "128k"}'
    else:
        cmd += ' -an'
    cmd += f' -movflags +faststart "{output_path}"'

    print(f"[CMD] {cmd}")
    code, _, err = run_cmd(cmd, capture=True)
    if code != 0:
        print(f"[ERROR] 编码失败:\n{err[-2000:]}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="onezion-video-compress: 自动视频压缩工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("input", help="输入视频路径")
    parser.add_argument("-o", "--output", help="输出路径 (默认: 原文件名_compressed.mp4)")
    parser.add_argument("-t", "--target", help="目标大小 (如 900MB, 1GB)")
    parser.add_argument("-p", "--preset", help="ffmpeg preset (ultrafast~slow)")
    parser.add_argument("-m", "--mode", choices=["2pass", "crf"], default="2pass",
                        help="压缩模式 (默认: 2pass)")
    parser.add_argument("--crf", type=int, default=28,
                        help="CRF 质量值 (默认28，仅CRF模式)")
    parser.add_argument("-s", "--scale", type=int,
                        help="缩放到指定高度 (如 720, 1080)")
    parser.add_argument("-r", "--fps", type=int, help="输出帧率")
    parser.add_argument("--audio-bitrate", default="128k", help="音频码率 (默认128k)")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERROR] 输入文件不存在: {args.input}")
        sys.exit(1)

    # 获取视频信息
    print(f"[INFO] 分析视频: {args.input}")
    info = get_video_info(args.input)
    print(f"[INFO] 时长: {info['duration']:.1f}s, 分辨率: {info['width']}x{info['height']}, FPS: {info['fps']:.1f}")

    # 输出路径
    if not args.output:
        base, ext = os.path.splitext(args.input)
        args.output = f"{base}_compressed.mp4"

    # 目标大小
    if not args.target:
        # 默认压缩到原大小的 1/10 或 900MB，取较小值
        orig_size_mb = os.path.getsize(args.input) / 1024 / 1024
        args.target = min(900, orig_size_mb / 10)
        args.target = max(args.target, 100)  # 至少 100MB
        print(f"[INFO] 未指定目标大小，自动设为: {args.target:.0f}MB")
        args.target_str = f"{args.target:.0f}MB"
    else:
        args.target_str = args.target

    target_mb = parse_size(args.target_str)

    print(f"[INFO] 目标大小: {target_mb:.0f}MB")
    print(f"[INFO] 输出路径: {args.output}")
    print()

    if args.mode == "2pass":
        compress_2pass(args.input, args.output, target_mb, info, args)
    else:
        compress_crf(args.input, args.output, info, args)

    # 验证输出
    if os.path.exists(args.output):
        out_size_mb = os.path.getsize(args.output) / 1024 / 1024
        print(f"\n[SUCCESS] 压缩完成!")
        print(f"[INFO] 输出文件: {args.output}")
        print(f"[INFO] 文件大小: {out_size_mb:.1f}MB (目标: {target_mb:.0f}MB)")
        if out_size_mb > target_mb * 1.1:
            print(f"[WARN] 文件大小超出目标 10%，建议降低分辨率或 CRF 值")
    else:
        print(f"\n[ERROR] 输出文件未生成: {args.output}")
        sys.exit(1)


if __name__ == "__main__":
    main()
