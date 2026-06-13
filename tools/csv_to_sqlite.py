#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
csv_to_sqlite.py - 将 ECDICT 的 CSV 文件转换为 Android Room 可用的 SQLite 数据库

使用说明:
    1. 确保已安装 Python 3.6+
    2. 确保已有 ecdict.csv 文件（可通过 download_ecdict.py 下载）
    3. 运行脚本：
        默认用法（读取当前目录的 ecdict.csv，输出到当前目录的 ecdict.db）：
            python csv_to_sqlite.py

        指定输入 CSV 路径：
            python csv_to_sqlite.py --input /path/to/ecdict.csv

        指定输出 DB 路径：
            python csv_to_sqlite.py --output /path/to/ecdict.db

        同时指定输入和输出：
            python csv_to_sqlite.py --input /path/to/ecdict.csv --output /path/to/ecdict.db

    4. 生成的 ecdict.db 文件可直接放入 Android 项目的 assets 目录供 Room 使用

依赖:
    - Python 3.6+
    - sqlite3（Python 标准库内置）
    - csv（Python 标准库内置）

ECDICT CSV 文件列说明:
    - word: 单词
    - phonetic: 音标
    - definition: 英文释义
    - translation: 中文释义
    - pos: 词性
    - collins: 柯林斯星级（1-5）
    - oxford: 是否为牛津3000核心词汇（1=是, 0=否）
    - tag: 标签
    - bnc: BNC词频排名
    - frq: 当代语料库词频排名
    - exchange: 词形变化（过去式、过去分词、现在分词、第三人称单数、复数等）
    - detail: 详尽释义（JSON格式）
    - audio: 朗读音频地址
"""

import argparse
import csv
import os
import sqlite3
import sys
import time


# CSV 文件中的列名（与 ECDICT CSV 文件的列顺序一致）
CSV_COLUMNS = [
    "word", "phonetic", "definition", "translation", "pos",
    "collins", "oxford", "tag", "bnc", "frq",
    "exchange", "detail", "audio"
]

# 批量插入的批次大小
BATCH_SIZE = 10000

# 数据库表创建 SQL
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS dictionary (
    word TEXT PRIMARY KEY,
    phonetic TEXT DEFAULT '',
    definition TEXT DEFAULT '',
    translation TEXT DEFAULT '',
    pos TEXT DEFAULT '',
    collins INTEGER DEFAULT 0,
    oxford INTEGER DEFAULT 0,
    tag TEXT DEFAULT '',
    bnc INTEGER DEFAULT 0,
    frq INTEGER DEFAULT 0,
    exchange TEXT DEFAULT '',
    detail TEXT DEFAULT '',
    audio TEXT DEFAULT ''
);
"""

# 索引创建 SQL
CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_word ON dictionary(word);
"""

# FTS5 全文搜索虚拟表创建 SQL
CREATE_FTS_TABLE_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS dictionary_fts USING fts5(
    word,
    translation,
    content='dictionary',
    content_rowid='rowid',
    tokenize='unicode61',
    prefix='2 3'
);
"""

# FTS 同步触发器 SQL
# 当向 dictionary 表插入新记录时，同步插入到 FTS 表
CREATE_FTS_INSERT_TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS dictionary_fts_insert AFTER INSERT ON dictionary BEGIN
    INSERT INTO dictionary_fts(rowid, word, translation)
    VALUES (new.rowid, new.word, new.translation);
END;
"""

# 当更新 dictionary 表记录时，同步更新 FTS 表
CREATE_FTS_UPDATE_TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS dictionary_fts_update AFTER UPDATE ON dictionary BEGIN
    INSERT INTO dictionary_fts(dictionary_fts, rowid, word, translation)
    VALUES ('delete', old.rowid, old.word, old.translation);
    INSERT INTO dictionary_fts(rowid, word, translation)
    VALUES (new.rowid, new.word, new.translation);
END;
"""

# 当从 dictionary 表删除记录时，同步删除 FTS 表中的记录
CREATE_FTS_DELETE_TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS dictionary_fts_delete AFTER DELETE ON dictionary BEGIN
    INSERT INTO dictionary_fts(dictionary_fts, rowid, word, translation)
    VALUES ('delete', old.rowid, old.word, old.translation);
END;
"""

# 插入数据的 SQL 语句
INSERT_SQL = """
INSERT OR REPLACE INTO dictionary
    (word, phonetic, definition, translation, pos,
     collins, oxford, tag, bnc, frq, exchange, detail, audio)
VALUES
    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
"""


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="将 ECDICT CSV 文件转换为 SQLite 数据库（适用于 Android Room）"
    )
    parser.add_argument(
        "--input", "-i",
        default="ecdict.csv",
        help="输入 CSV 文件路径（默认: ecdict.csv）"
    )
    parser.add_argument(
        "--output", "-o",
        default="ecdict.db",
        help="输出 SQLite 数据库文件路径（默认: ecdict.db）"
    )
    return parser.parse_args()


def setup_database(db_path):
    """
    创建并配置 SQLite 数据库

    设置性能优化 PRAGMA，创建表、索引、FTS 虚拟表和同步触发器。

    Args:
        db_path: 数据库文件路径

    Returns:
        sqlite3.Connection: 数据库连接对象
    """
    # 如果数据库文件已存在，先删除以避免旧数据干扰
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"[信息] 已删除旧的数据库文件: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 设置性能优化 PRAGMA
    # 注意：page_size 必须在创建任何表之前设置才能生效
    print("[信息] 设置数据库性能优化参数...")
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute("PRAGMA page_size = 4096;")
    cursor.execute("PRAGMA cache_size = -20000;")
    cursor.execute("PRAGMA temp_store = MEMORY;")

    # 验证 PRAGMA 设置
    journal_mode = cursor.execute("PRAGMA journal_mode;").fetchone()[0]
    page_size = cursor.execute("PRAGMA page_size;").fetchone()[0]
    print(f"  journal_mode = {journal_mode}")
    print(f"  page_size    = {page_size}")

    # 创建主表
    print("[信息] 创建 dictionary 表...")
    cursor.execute(CREATE_TABLE_SQL)

    # 创建索引
    print("[信息] 创建索引 idx_word...")
    cursor.execute(CREATE_INDEX_SQL)

    # 创建 FTS5 全文搜索虚拟表
    print("[信息] 创建 FTS5 全文搜索虚拟表 dictionary_fts...")
    cursor.execute(CREATE_FTS_TABLE_SQL)

    # 创建 FTS 同步触发器
    print("[信息] 创建 FTS 同步触发器...")
    cursor.execute(CREATE_FTS_INSERT_TRIGGER_SQL)
    cursor.execute(CREATE_FTS_UPDATE_TRIGGER_SQL)
    cursor.execute(CREATE_FTS_DELETE_TRIGGER_SQL)

    conn.commit()
    return conn


def convert_csv_to_row(csv_row):
    """
    将 CSV 行数据转换为数据库插入参数

    对数值字段进行类型转换，处理空值。

    Args:
        csv_row: CSV 读取的一行数据（字典格式）

    Returns:
        tuple: 可用于 SQL INSERT 的参数元组
    """
    values = []
    for col in CSV_COLUMNS:
        val = csv_row.get(col, "")

        # 数值类型转换
        if col in ("collins", "oxford", "bnc", "frq"):
            if val == "" or val is None:
                val = 0
            else:
                try:
                    val = int(val)
                except (ValueError, TypeError):
                    val = 0
        else:
            # 文本字段，确保空值转为空字符串
            if val is None:
                val = ""

        values.append(val)

    return tuple(values)


def import_csv(conn, csv_path):
    """
    从 CSV 文件批量导入数据到 SQLite 数据库

    使用批量插入方式，每 BATCH_SIZE 条记录提交一次事务。

    Args:
        conn: 数据库连接对象
        csv_path: CSV 文件路径

    Returns:
        int: 成功导入的总记录数
    """
    cursor = conn.cursor()
    total_count = 0
    batch_count = 0
    start_time = time.time()

    print(f"[信息] 开始导入 CSV 数据: {csv_path}")
    print(f"  批量插入大小: {BATCH_SIZE} 条/批")

    try:
        with open(csv_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            # 验证 CSV 列名
            if reader.fieldnames is None:
                print("[错误] CSV 文件为空或格式不正确")
                sys.exit(1)

            # 开始事务
            conn.execute("BEGIN TRANSACTION;")

            for row in reader:
                params = convert_csv_to_row(row)
                cursor.execute(INSERT_SQL, params)
                total_count += 1
                batch_count += 1

                # 每达到批次大小时提交一次
                if batch_count >= BATCH_SIZE:
                    conn.commit()
                    elapsed = time.time() - start_time
                    rate = total_count / elapsed if elapsed > 0 else 0
                    print(f"  已导入 {total_count:>8,} 条记录 "
                          f"({rate:>8,.0f} 条/秒)")
                    conn.execute("BEGIN TRANSACTION;")
                    batch_count = 0

            # 提交最后一批数据
            if batch_count > 0:
                conn.commit()

    except FileNotFoundError:
        print(f"[错误] 找不到 CSV 文件: {csv_path}")
        print("[提示] 请先运行 download_ecdict.py 下载 ECDICT 数据文件")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[警告] 用户中断导入，正在回滚未提交的数据...")
        conn.rollback()
        print(f"[信息] 已导入 {total_count} 条记录后中断")
        sys.exit(1)

    elapsed = time.time() - start_time
    return total_count, elapsed


def print_statistics(db_path, total_count, elapsed_time):
    """
    输出数据库统计信息

    Args:
        db_path: 数据库文件路径
        total_count: 导入的总记录数
        elapsed_time: 导入耗时（秒）
    """
    file_size = os.path.getsize(db_path)

    # 格式化文件大小
    if file_size >= 1024 * 1024 * 1024:
        size_str = f"{file_size / (1024 * 1024 * 1024):.2f} GB"
    elif file_size >= 1024 * 1024:
        size_str = f"{file_size / (1024 * 1024):.2f} MB"
    elif file_size >= 1024:
        size_str = f"{file_size / 1024:.2f} KB"
    else:
        size_str = f"{file_size} B"

    rate = total_count / elapsed_time if elapsed_time > 0 else 0

    print("\n" + "=" * 50)
    print("  数据库统计信息")
    print("=" * 50)
    print(f"  总词条数:       {total_count:>12,} 条")
    print(f"  导入耗时:       {elapsed_time:>12.2f} 秒")
    print(f"  导入速度:       {rate:>12,.0f} 条/秒")
    print(f"  数据库文件:     {db_path}")
    print(f"  数据库大小:     {size_str:>12s}")
    print("=" * 50)

    # 连接数据库查询额外统计
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 统计有音标的词条数
    phonetic_count = cursor.execute(
        "SELECT COUNT(*) FROM dictionary WHERE phonetic != ''"
    ).fetchone()[0]

    # 统计有中文翻译的词条数
    translation_count = cursor.execute(
        "SELECT COUNT(*) FROM dictionary WHERE translation != ''"
    ).fetchone()[0]

    # 统计牛津核心词汇数
    oxford_count = cursor.execute(
        "SELECT COUNT(*) FROM dictionary WHERE oxford = 1"
    ).fetchone()[0]

    # 统计柯林斯星级词条数
    collins_count = cursor.execute(
        "SELECT COUNT(*) FROM dictionary WHERE collins > 0"
    ).fetchone()[0]

    print(f"  有音标词条:     {phonetic_count:>12,} 条")
    print(f"  有中文翻译词条: {translation_count:>12,} 条")
    print(f"  牛津核心词汇:   {oxford_count:>12,} 条")
    print(f"  柯林斯星级词条: {collins_count:>12,} 条")
    print("=" * 50)

    conn.close()


def main():
    """主函数"""
    args = parse_args()

    csv_path = args.input
    db_path = args.output

    print("=" * 50)
    print("  ECDICT CSV to SQLite 转换工具")
    print("=" * 50)
    print(f"  输入文件: {csv_path}")
    print(f"  输出文件: {db_path}")
    print("=" * 50 + "\n")

    # 检查 CSV 文件是否存在
    if not os.path.exists(csv_path):
        print(f"[错误] 找不到 CSV 文件: {csv_path}")
        print("[提示] 请先运行以下命令下载 ECDICT 数据文件:")
        print("        python download_ecdict.py")
        sys.exit(1)

    # 创建并配置数据库
    conn = setup_database(db_path)

    try:
        # 导入 CSV 数据
        total_count, elapsed_time = import_csv(conn, csv_path)

        # 输出统计信息
        print_statistics(db_path, total_count, elapsed_time)

        print("\n[完成] 数据库转换成功！")
        print(f"[提示] 可将 {db_path} 放入 Android 项目的 assets 目录供 Room 使用")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
