#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_ecdict.py - 从 GitHub 下载 ECDICT 的 CSV 数据文件

使用说明:
    1. 确保已安装 Python 3.6+
    2. 运行脚本下载 ECDICT 数据：
        默认用法（下载到当前目录的 ecdict.csv）：
            python download_ecdict.py

        指定输出路径：
            python download_ecdict.py --output /path/to/ecdict.csv

    3. 下载完成后，运行 csv_to_sqlite.py 将 CSV 转换为 SQLite 数据库：
            python csv_to_sqlite.py --input ecdict.csv --output ecdict.db

依赖:
    - Python 3.6+
    - 标准库: urllib, sys, os, time

数据来源:
    - 项目地址: https://github.com/skywind3000/ECDICT
    - ECDICT 是一个开源的英汉词典数据项目，包含约 770 万词条
    - 数据格式为 CSV（UTF-8 编码），包含音标、释义、词频等信息
"""

import argparse
import os
import sys
import time

try:
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
except ImportError:
    print("[错误] 需要 Python 3 环境")
    sys.exit(1)


# ECDICT CSV 文件的下载地址（GitHub Release v1.0.28）
DEFAULT_DOWNLOAD_URL = (
    "https://github.com/skywind3000/ECDICT/"
    "releases/download/1.0.28/ecdict.csv"
)

# 默认输出文件名
DEFAULT_OUTPUT = "ecdict.csv"

# 下载缓冲区大小（字节）
BUFFER_SIZE = 8192

# 显示进度条的刷新间隔（秒）
PROGRESS_REFRESH_INTERVAL = 0.1


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="从 GitHub 下载 ECDICT CSV 数据文件"
    )
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT,
        help=f"输出文件路径（默认: {DEFAULT_OUTPUT}）"
    )
    parser.add_argument(
        "--url", "-u",
        default=DEFAULT_DOWNLOAD_URL,
        help="自定义下载 URL（默认: ECDICT v1.0.28 Release）"
    )
    return parser.parse_args()


def format_size(byte_count):
    """
    将字节数格式化为人类可读的字符串

    Args:
        byte_count: 字节数

    Returns:
        str: 格式化后的字符串，如 "123.45 MB"
    """
    if byte_count >= 1024 * 1024 * 1024:
        return f"{byte_count / (1024 * 1024 * 1024):.2f} GB"
    elif byte_count >= 1024 * 1024:
        return f"{byte_count / (1024 * 1024):.2f} MB"
    elif byte_count >= 1024:
        return f"{byte_count / 1024:.2f} KB"
    else:
        return f"{byte_count} B"


def format_time(seconds):
    """
    将秒数格式化为人类可读的时间字符串

    Args:
        seconds: 秒数

    Returns:
        str: 格式化后的字符串，如 "1m 23s"
    """
    if seconds >= 3600:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"
    elif seconds >= 60:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        return f"{seconds:.1f}s"


def download_file(url, output_path):
    """
    下载文件并显示进度条

    Args:
        url: 下载 URL
        output_path: 输出文件路径
    """
    print(f"[信息] 下载地址: {url}")
    print(f"[信息] 保存路径: {output_path}")
    print()

    # 创建请求，设置 User-Agent 避免被 GitHub 拒绝
    request = Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; ECDictDownloader/1.0)"
    })

    try:
        response = urlopen(request, timeout=30)
    except HTTPError as e:
        print(f"[错误] HTTP 请求失败: {e.code} {e.reason}")
        sys.exit(1)
    except URLError as e:
        print(f"[错误] 网络请求失败: {e.reason}")
        print("[提示] 请检查网络连接，或尝试使用代理")
        sys.exit(1)

    # 获取文件总大小（部分服务器可能不返回 Content-Length）
    total_size = int(response.headers.get("Content-Length", 0))
    if total_size > 0:
        print(f"[信息] 文件大小: {format_size(total_size)}")
    else:
        print("[信息] 文件大小: 未知")

    print()
    print("[下载中]")

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 如果文件已存在，先删除
    if os.path.exists(output_path):
        os.remove(output_path)

    downloaded = 0
    start_time = time.time()
    last_refresh_time = 0
    last_downloaded = 0

    try:
        with open(output_path, "wb") as f:
            while True:
                chunk = response.read(BUFFER_SIZE)
                if not chunk:
                    break

                f.write(chunk)
                downloaded += len(chunk)
                current_time = time.time()

                # 控制进度条刷新频率，避免输出过于频繁
                if current_time - last_refresh_time >= PROGRESS_REFRESH_INTERVAL:
                    last_refresh_time = current_time

                    # 计算下载速度
                    elapsed = current_time - start_time
                    if elapsed > 0:
                        speed = downloaded / elapsed
                    else:
                        speed = 0

                    # 计算增量速度（最近一段时间的速度）
                    delta_size = downloaded - last_downloaded
                    delta_time = current_time - (start_time if last_downloaded == 0 else last_refresh_time - PROGRESS_REFRESH_INTERVAL)
                    instant_speed = delta_size / PROGRESS_REFRESH_INTERVAL if PROGRESS_REFRESH_INTERVAL > 0 else 0
                    last_downloaded = downloaded

                    # 构建进度条
                    if total_size > 0:
                        progress = downloaded / total_size
                        bar_width = 40
                        filled = int(bar_width * progress)
                        bar = "[" + "=" * filled + ">" + " " * (bar_width - filled) + "]"
                        percent = progress * 100
                        sys.stdout.write(
                            f"\r  {bar} {percent:5.1f}%  "
                            f"{format_size(downloaded):>10s} / {format_size(total_size):<10s}  "
                            f"{format_size(speed):>10s}/s"
                        )
                    else:
                        sys.stdout.write(
                            f"\r  已下载: {format_size(downloaded):>10s}  "
                            f"{format_size(speed):>10s}/s"
                        )

                    sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n\n[警告] 下载被用户中断")
        # 删除不完整的文件
        if os.path.exists(output_path):
            os.remove(output_path)
            print("[信息] 已删除不完整的下载文件")
        sys.exit(1)

    # 下载完成，换行
    print()

    elapsed = time.time() - start_time
    actual_size = os.path.getsize(output_path)
    avg_speed = actual_size / elapsed if elapsed > 0 else 0

    print()
    print(f"[完成] 下载完成！")
    print(f"  文件大小: {format_size(actual_size)}")
    print(f"  耗时:     {format_time(elapsed)}")
    print(f"  平均速度: {format_size(avg_speed)}/s")
    print()
    print("[提示] 下一步，运行以下命令将 CSV 转换为 SQLite 数据库:")
    print(f"        python csv_to_sqlite.py --input {output_path} --output ecdict.db")


def main():
    """主函数"""
    args = parse_args()

    output_path = args.output
    url = args.url

    print("=" * 50)
    print("  ECDICT 数据下载工具")
    print("=" * 50)
    print()

    # 检查文件是否已存在
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"[警告] 文件已存在: {output_path} ({format_size(file_size)})")
        print("[提示] 将覆盖已有文件")
        print()

    # 开始下载
    download_file(url, output_path)


if __name__ == "__main__":
    main()
