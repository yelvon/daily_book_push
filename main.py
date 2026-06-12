#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日读书推送 - CLI 入口。"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.config import load_app_config, resolve_book_path
from src.message import build_all_finished_message, build_message
from src.notifier import send_message
from src.progress import (
    get_or_init_book_progress,
    load_progress,
    record_push,
    reset_book_progress,
    save_progress,
)
from src.rotation import next_rotation_index, peek_next_book_title, pick_book
from src.splitter import split_text
from src.summarizer import summarize_segment

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "daily_book_push.log", encoding="utf-8"),
        ],
    )


def run(args: argparse.Namespace) -> int:
    config = load_app_config()
    state = load_progress(config.progress_path)

    if args.reset:
        reset_book_progress(state, args.reset)
        save_progress(config.progress_path, state)
        logger.info("已重置书籍进度: %s", args.reset)
        return 0

    if args.notify_test:
        test_msg = "## 每日读书测试\n\n这是一条测试消息。"
        if args.dry_run:
            print(test_msg)
            return 0
        ok = send_message(config, test_msg)
        return 0 if ok else 1

    pick = pick_book(config.books, state, force_book_id=args.book)
    if pick is None:
        msg = build_all_finished_message()
        logger.info("所有书籍已读完")
        if args.dry_run:
            print(msg)
            return 0
        send_message(config, msg)
        return 0

    book = pick.book
    book_path = resolve_book_path(config, book)
    if not book_path.exists():
        logger.error("书籍文件不存在: %s", book_path)
        return 1

    text = book_path.read_text(encoding=book.encoding)
    prog = get_or_init_book_progress(state, book.id, len(text))
    split = split_text(text, prog.offset, book.daily_chars)

    if not split.segment.strip() and split.is_finished:
        prog.finished = True
        save_progress(config.progress_path, state)
        logger.info("书籍 %s 已无新内容", book.id)
        return 0

    ai_summary = None
    if config.ai_enabled and not args.skip_ai:
        ai_summary = summarize_segment(config, book, split.segment)

    next_idx = next_rotation_index(pick.index, len(pick.active_books))
    next_title = peek_next_book_title(pick.active_books, next_idx)
    message = build_message(
        book=book,
        day_count=prog.day_count,
        progress_pct=split.progress_pct,
        segment=split.segment,
        ai_summary=ai_summary,
        next_book_title=next_title,
        is_finished=split.is_finished,
    )

    logger.info("选中书籍: %s (%s), offset=%s -> %s", book.id, book.title, prog.offset, split.new_offset)

    if args.dry_run:
        print(message)
        return 0

    if not send_message(config, message):
        logger.error("推送失败")
        return 1

    record_push(
        state=state,
        book_id=book.id,
        new_offset=split.new_offset,
        is_finished=split.is_finished,
        rotation_index=next_idx,
    )
    save_progress(config.progress_path, state)
    logger.info("推送完成，进度已保存")
    return 0


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="每日读书推送")
    parser.add_argument("--dry-run", action="store_true", help="预览消息，不推送、不写进度")
    parser.add_argument("--book", help="强制指定书籍 id")
    parser.add_argument("--reset", metavar="BOOK_ID", help="重置指定书籍进度")
    parser.add_argument("--notify-test", action="store_true", help="发送测试通知")
    parser.add_argument("--skip-ai", action="store_true", help="跳过 AI 摘要")
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
