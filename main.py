#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日读书 / 荐书推送 - CLI 入口。"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

from src.config import (
    load_app_config,
    load_economics_config,
    load_recommend_config,
    resolve_book_path,
    select_channel_notifier_config,
)
from src.economics import generate_daily_economics
from src.economics_progress import (
    append_record as append_economics_record,
    load_economics_progress,
    prune_history as prune_economics_history,
    save_economics_progress,
)
from src.message import build_all_finished_message, build_message
from src.notifier import send_message
from src.progress import (
    get_or_init_book_progress,
    load_progress,
    record_push,
    reset_book_progress,
    save_progress,
)
from src.recommend_history import (
    append_record,
    load_recommend_history,
    prune_history,
    recent_titles,
    save_recommend_history,
)
from src.recommender import generate_daily_recommendation
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


def run_recommend(args: argparse.Namespace) -> int:
    config = load_app_config()
    recommend = load_recommend_config()

    history_state = load_recommend_history(recommend.recommend_history_path)
    history_state = prune_history(history_state, recommend.history_days)
    recent = recent_titles(history_state, recommend.max_history_in_prompt)

    result = generate_daily_recommendation(config, recommend, recent)
    if not result:
        fallback = "## 每日荐书\n\n今日荐书生成失败，请检查 CURSOR_API_KEY / GEMINI_API_KEY 或稍后重试。"
        if args.dry_run:
            print(fallback)
            return 1
        send_message(config, fallback)
        return 1

    logger.info("今日荐书: %s / %s", result.record.title, result.record.author)

    if args.dry_run:
        print(result.message)
        return 0

    if not send_message(config, result.message):
        logger.error("推送失败")
        return 1

    append_record(history_state, result.record)
    save_recommend_history(recommend.recommend_history_path, history_state)
    logger.info("荐书推送完成，历史已更新")
    return 0


def run_economics(args: argparse.Namespace) -> int:
    config = load_app_config()
    economics = load_economics_config()

    state = load_economics_progress(economics.progress_path)
    state = prune_economics_history(state, economics.history_days)

    result = generate_daily_economics(config, economics, state)
    if not result:
        fallback = "## 今日经济学\n\n今日经济学内容生成失败，请检查 CURSOR_API_KEY / GEMINI_API_KEY 或稍后重试。"
        if args.dry_run:
            print(fallback)
            return 1
        channel_config = select_channel_notifier_config(config, "economics")
        send_message(channel_config, fallback)
        return 1

    logger.info("今日经济学: %s / %s", result.record.topic, result.record.module)

    if args.dry_run:
        print(result.message)
        return 0

    channel_config = select_channel_notifier_config(config, "economics")
    if not send_message(channel_config, result.message):
        logger.error("经济学频道推送失败")
        return 1

    append_economics_record(state, result.record)
    save_economics_progress(economics.progress_path, state)
    logger.info("经济学推送完成，进度已更新")
    return 0


def _resolve_mode(explicit_mode: str | None) -> str:
    if explicit_mode:
        return explicit_mode
    return load_recommend_config().mode


def _resolve_alternate_mode(recommend_cfg) -> str:
    even = date.today().toordinal() % 2 == 0
    even_mode = recommend_cfg.alternate_even_day
    odd_mode = "recommend" if even_mode == "read" else "read"
    return even_mode if even else odd_mode


def run_both(args: argparse.Namespace) -> int:
    read_args = argparse.Namespace(**{**vars(args), "mode": "read"})
    recommend_args = argparse.Namespace(**{**vars(args), "mode": "recommend"})

    read_code = run_read(read_args)
    recommend_code = run_recommend(recommend_args)

    if args.dry_run:
        return 0 if read_code == 0 or recommend_code == 0 else 1
    return 0 if read_code == 0 and recommend_code == 0 else 1


def run_read(args: argparse.Namespace) -> int:
    config = load_app_config()
    state = load_progress(config.progress_path)

    if args.reset:
        reset_book_progress(state, args.reset)
        save_progress(config.progress_path, state)
        logger.info("已重置书籍进度: %s", args.reset)
        return 0

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


def run(args: argparse.Namespace) -> int:
    if args.notify_test:
        test_msg = "## 每日荐书测试\n\n这是一条测试消息。"
        if args.dry_run:
            print(test_msg)
            return 0
        config = load_app_config()
        ok = send_message(config, test_msg)
        return 0 if ok else 1

    mode = _resolve_mode(args.mode)
    recommend_cfg = load_recommend_config()

    if mode == "alternate":
        mode = _resolve_alternate_mode(recommend_cfg)
        logger.info("alternate 模式，今日执行: %s", mode)

    if mode == "both":
        return run_both(args)
    if mode == "recommend":
        return run_recommend(args)
    if mode == "economics":
        return run_economics(args)
    if mode == "read":
        return run_read(args)
    logger.error("未知模式: %s（可选: recommend / read / both / alternate / economics）", mode)
    return 1


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="每日读书 / AI 荐书推送")
    parser.add_argument(
        "--mode",
        choices=["recommend", "read", "both", "alternate", "economics"],
        default=None,
        help="recommend=AI荐书; read=本地读书; both=两条都推; alternate=按日轮换; economics=每日经济学",
    )
    parser.add_argument("--dry-run", action="store_true", help="预览消息，不推送、不写状态")
    parser.add_argument("--book", help="[read 模式] 强制指定书籍 id")
    parser.add_argument("--reset", metavar="BOOK_ID", help="[read 模式] 重置指定书籍进度")
    parser.add_argument("--notify-test", action="store_true", help="发送测试通知")
    parser.add_argument("--skip-ai", action="store_true", help="[read 模式] 跳过 AI 摘要")
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
