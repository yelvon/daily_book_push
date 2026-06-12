"""配置加载：books.yaml + 环境变量。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT_DIR / "config" / "books.yaml"
DEFAULT_PROGRESS_PATH = ROOT_DIR / "state" / "progress.json"


@dataclass
class BookConfig:
    id: str
    file: str
    title: str
    author: str = ""
    enabled: bool = True
    daily_chars: int = 2000
    encoding: str = "utf-8"


@dataclass
class AppConfig:
    books: List[BookConfig] = field(default_factory=list)
    rotation_mode: str = "round_robin"
    schedule_timezone: str = "Asia/Shanghai"
    ai_enabled: bool = True
    ai_on_failure: str = "skip"
    config_path: Path = DEFAULT_CONFIG_PATH
    progress_path: Path = DEFAULT_PROGRESS_PATH
    root_dir: Path = ROOT_DIR
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini/gemini-2.5-flash"
    gemini_model_fallback: Optional[str] = None
    feishu_webhook_url: Optional[str] = None
    feishu_webhook_secret: Optional[str] = None
    feishu_webhook_keyword: Optional[str] = None
    wechat_webhook_url: Optional[str] = None
    wechat_msg_type: str = "markdown"
    webhook_verify_ssl: bool = True
    feishu_max_bytes: int = 20000
    wechat_max_bytes: int = 4000


def setup_env() -> None:
    env_file = os.getenv("ENV_FILE")
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv(ROOT_DIR / ".env")


def _parse_books(raw: Dict[str, Any]) -> List[BookConfig]:
    books: List[BookConfig] = []
    for item in raw.get("books", []) or []:
        books.append(
            BookConfig(
                id=str(item["id"]),
                file=str(item["file"]),
                title=str(item.get("title") or item["id"]),
                author=str(item.get("author") or ""),
                enabled=bool(item.get("enabled", True)),
                daily_chars=int(item.get("daily_chars", 2000)),
                encoding=str(item.get("encoding", "utf-8")),
            )
        )
    return books


def load_app_config(config_path: Optional[Path] = None) -> AppConfig:
    setup_env()
    path = config_path or DEFAULT_CONFIG_PATH
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    ai_cfg = raw.get("ai") or {}
    schedule_cfg = raw.get("schedule") or {}
    rotation_cfg = raw.get("rotation") or {}

    verify_ssl = os.getenv("WEBHOOK_VERIFY_SSL", "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }

    return AppConfig(
        books=_parse_books(raw),
        rotation_mode=str(rotation_cfg.get("mode", "round_robin")),
        schedule_timezone=str(schedule_cfg.get("timezone", "Asia/Shanghai")),
        ai_enabled=bool(ai_cfg.get("enabled", True)),
        ai_on_failure=str(ai_cfg.get("on_failure", "skip")),
        config_path=path,
        progress_path=DEFAULT_PROGRESS_PATH,
        root_dir=ROOT_DIR,
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini/gemini-2.5-flash"),
        gemini_model_fallback=os.getenv("GEMINI_MODEL_FALLBACK") or None,
        feishu_webhook_url=os.getenv("FEISHU_WEBHOOK_URL") or None,
        feishu_webhook_secret=os.getenv("FEISHU_WEBHOOK_SECRET") or None,
        feishu_webhook_keyword=os.getenv("FEISHU_WEBHOOK_KEYWORD") or None,
        wechat_webhook_url=os.getenv("WECHAT_WEBHOOK_URL") or None,
        wechat_msg_type=os.getenv("WECHAT_MSG_TYPE", "markdown"),
        webhook_verify_ssl=verify_ssl,
    )


def resolve_book_path(config: AppConfig, book: BookConfig) -> Path:
    path = Path(book.file)
    if not path.is_absolute():
        path = config.root_dir / path
    return path
