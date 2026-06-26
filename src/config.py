"""配置加载：books.yaml + 环境变量。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT_DIR / "config" / "books.yaml"
DEFAULT_RECOMMEND_CONFIG_PATH = ROOT_DIR / "config" / "recommend.yaml"
DEFAULT_ECONOMICS_CONFIG_PATH = ROOT_DIR / "config" / "economics.yaml"
DEFAULT_LAW_CONFIG_PATH = ROOT_DIR / "config" / "law.yaml"
DEFAULT_BUSINESS_CONFIG_PATH = ROOT_DIR / "config" / "business.yaml"
DEFAULT_PROGRESS_PATH = ROOT_DIR / "state" / "progress.json"
DEFAULT_RECOMMEND_HISTORY_PATH = ROOT_DIR / "state" / "recommend_history.json"
DEFAULT_ECONOMICS_PROGRESS_PATH = ROOT_DIR / "state" / "economics_progress.json"
DEFAULT_LAW_PROGRESS_PATH = ROOT_DIR / "state" / "law_progress.json"
DEFAULT_BUSINESS_PROGRESS_PATH = ROOT_DIR / "state" / "business_progress.json"


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
class RecommendConfig:
    mode: str = "recommend"
    alternate_even_day: str = "read"
    language: str = "zh"
    use_google_search: bool = True
    history_days: int = 90
    max_history_in_prompt: int = 30
    categories: List[str] = field(default_factory=list)
    rotate_categories: bool = True
    avoid_repeat: bool = True
    recommend_history_path: Path = DEFAULT_RECOMMEND_HISTORY_PATH


@dataclass
class EconomicsConfig:
    language: str = "zh"
    use_google_search: bool = True
    history_days: int = 180
    level_start: str = "beginner"
    level_progression: str = "gradual"
    weekday_style: str = "concept"
    weekend_style: str = "case_review"
    syllabus: List[str] = field(default_factory=list)
    progress_path: Path = DEFAULT_ECONOMICS_PROGRESS_PATH


@dataclass
class LawConfig:
    language: str = "zh"
    use_google_search: bool = True
    history_days: int = 180
    jurisdiction: str = "cn_primary"
    level_start: str = "beginner"
    level_progression: str = "gradual"
    weekday_style: str = "concept"
    weekend_style: str = "case_review"
    syllabus: List[str] = field(default_factory=list)
    progress_path: Path = DEFAULT_LAW_PROGRESS_PATH


@dataclass
class BusinessConfig:
    language: str = "zh"
    use_google_search: bool = True
    history_days: int = 180
    level_start: str = "beginner"
    level_progression: str = "gradual"
    weekday_style: str = "case"
    weekend_style: str = "case_review"
    audience: str = "early_stage_founder"
    company_scope: str = "global_and_china"
    avoid_news_summary: bool = True
    syllabus: List[str] = field(default_factory=list)
    progress_path: Path = DEFAULT_BUSINESS_PROGRESS_PATH


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
    cursor_api_key: Optional[str] = None
    cursor_model: str = "composer-2.5"
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini/gemini-2.5-flash"
    gemini_model_fallback: Optional[str] = None
    feishu_webhook_url: Optional[str] = None
    feishu_webhook_secret: Optional[str] = None
    feishu_webhook_keyword: Optional[str] = None
    wechat_webhook_url: Optional[str] = None
    wechat_msg_type: str = "text"
    wechat_personal_compat: bool = True
    economics_feishu_webhook_url: Optional[str] = None
    economics_feishu_webhook_secret: Optional[str] = None
    economics_feishu_webhook_keyword: Optional[str] = None
    economics_wechat_webhook_url: Optional[str] = None
    economics_wechat_msg_type: str = "text"
    law_feishu_webhook_url: Optional[str] = None
    law_feishu_webhook_secret: Optional[str] = None
    law_feishu_webhook_keyword: Optional[str] = None
    law_wechat_webhook_url: Optional[str] = None
    law_wechat_msg_type: str = "text"
    business_feishu_webhook_url: Optional[str] = None
    business_feishu_webhook_secret: Optional[str] = None
    business_feishu_webhook_keyword: Optional[str] = None
    business_wechat_webhook_url: Optional[str] = None
    business_wechat_msg_type: str = "text"
    webhook_verify_ssl: bool = True
    feishu_max_bytes: int = 20000
    wechat_max_bytes: int = 4000
    notification_title: str = "每日读书"


def setup_env() -> None:
    env_file = os.getenv("ENV_FILE")
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv(ROOT_DIR / ".env")


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


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


def load_recommend_config(path: Optional[Path] = None) -> RecommendConfig:
    setup_env()
    cfg_path = path or DEFAULT_RECOMMEND_CONFIG_PATH
    if not cfg_path.exists():
        return RecommendConfig()

    with cfg_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    rec = raw.get("recommend") or {}
    strategy = raw.get("schedule_strategy") or {}
    use_search = rec.get("use_google_search", True)
    env_search = os.getenv("GEMINI_USE_SEARCH")
    if env_search is not None:
        use_search = env_search.strip().lower() not in {"0", "false", "no", "off"}

    env_mode = os.getenv("RUN_MODE")
    mode = str(env_mode or raw.get("mode", "recommend"))

    return RecommendConfig(
        mode=mode,
        alternate_even_day=str(strategy.get("alternate_even_day", "read")),
        language=str(rec.get("language", "zh")),
        use_google_search=bool(use_search),
        history_days=int(rec.get("history_days", 90)),
        max_history_in_prompt=int(rec.get("max_history_in_prompt", 30)),
        categories=[str(c) for c in rec.get("categories") or []],
        rotate_categories=bool(rec.get("rotate_categories", True)),
        avoid_repeat=bool(rec.get("avoid_repeat", True)),
        recommend_history_path=DEFAULT_RECOMMEND_HISTORY_PATH,
    )


def load_economics_config(path: Optional[Path] = None) -> EconomicsConfig:
    setup_env()
    cfg_path = path or DEFAULT_ECONOMICS_CONFIG_PATH
    if not cfg_path.exists():
        return EconomicsConfig(
            syllabus=[
                "基础概念",
                "消费者选择",
                "供给与需求",
                "市场与价格",
                "企业与成本",
                "竞争与垄断",
                "宏观经济",
                "货币与通胀",
                "金融市场",
                "全球化与制度",
            ]
        )

    with cfg_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    econ = raw.get("economics") or {}
    level = econ.get("level") or {}
    schedule = econ.get("schedule") or {}
    use_search = econ.get("use_google_search", True)
    env_search = os.getenv("ECONOMICS_USE_SEARCH")
    if env_search is not None:
        use_search = env_search.strip().lower() not in {"0", "false", "no", "off"}

    return EconomicsConfig(
        language=str(econ.get("language", "zh")),
        use_google_search=bool(use_search),
        history_days=int(econ.get("history_days", 180)),
        level_start=str(level.get("start", "beginner")),
        level_progression=str(level.get("progression", "gradual")),
        weekday_style=str(schedule.get("weekday_style", "concept")),
        weekend_style=str(schedule.get("weekend_style", "case_review")),
        syllabus=[str(item) for item in econ.get("syllabus") or []],
        progress_path=DEFAULT_ECONOMICS_PROGRESS_PATH,
    )


def load_law_config(path: Optional[Path] = None) -> LawConfig:
    setup_env()
    cfg_path = path or DEFAULT_LAW_CONFIG_PATH
    if not cfg_path.exists():
        return LawConfig(
            syllabus=[
                "创业法律常识",
                "公司设立与主体选择",
                "股权结构与股东权利",
                "股东协议与控制权",
                "劳动合同与用工合规",
                "合同管理与风险条款",
                "融资与尽调要点",
                "知识产权与商业秘密",
                "广告合规与消费者权益",
                "数据合规与隐私",
                "争议解决与维权",
            ]
        )

    with cfg_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    law = raw.get("law") or {}
    level = law.get("level") or {}
    schedule = law.get("schedule") or {}
    use_search = law.get("use_google_search", True)
    env_search = os.getenv("LAW_USE_SEARCH")
    if env_search is not None:
        use_search = env_search.strip().lower() not in {"0", "false", "no", "off"}

    return LawConfig(
        language=str(law.get("language", "zh")),
        use_google_search=bool(use_search),
        history_days=int(law.get("history_days", 180)),
        jurisdiction=str(law.get("jurisdiction", "cn_primary")),
        level_start=str(level.get("start", "beginner")),
        level_progression=str(level.get("progression", "gradual")),
        weekday_style=str(schedule.get("weekday_style", "concept")),
        weekend_style=str(schedule.get("weekend_style", "case_review")),
        syllabus=[str(item) for item in law.get("syllabus") or []],
        progress_path=DEFAULT_LAW_PROGRESS_PATH,
    )


def load_business_config(path: Optional[Path] = None) -> BusinessConfig:
    setup_env()
    cfg_path = path or DEFAULT_BUSINESS_CONFIG_PATH
    if not cfg_path.exists():
        return BusinessConfig(
            syllabus=[
                "商业模式基础",
                "用户需求与价值主张",
                "定价与收入模型",
                "获客与增长",
                "留存与复购",
                "渠道与分发",
                "成本结构与效率",
                "平台、网络效应与生态",
                "品牌、信任与社区",
                "竞争策略与护城河",
                "组织能力与执行",
                "失败案例与反模式",
            ]
        )

    with cfg_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    business = raw.get("business") or {}
    level = business.get("level") or {}
    schedule = business.get("schedule") or {}
    preferences = business.get("preferences") or {}
    use_search = business.get("use_google_search", True)
    env_search = os.getenv("BUSINESS_USE_SEARCH")
    if env_search is not None:
        use_search = env_search.strip().lower() not in {"0", "false", "no", "off"}

    return BusinessConfig(
        language=str(business.get("language", "zh")),
        use_google_search=bool(use_search),
        history_days=int(business.get("history_days", 180)),
        level_start=str(level.get("start", "beginner")),
        level_progression=str(level.get("progression", "gradual")),
        weekday_style=str(schedule.get("weekday_style", "case")),
        weekend_style=str(schedule.get("weekend_style", "case_review")),
        audience=str(preferences.get("audience", "early_stage_founder")),
        company_scope=str(preferences.get("company_scope", "global_and_china")),
        avoid_news_summary=bool(preferences.get("avoid_news_summary", True)),
        syllabus=[str(item) for item in business.get("syllabus") or []],
        progress_path=DEFAULT_BUSINESS_PROGRESS_PATH,
    )


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
        cursor_api_key=os.getenv("CURSOR_API_KEY") or None,
        cursor_model=os.getenv("CURSOR_MODEL", "composer-2.5"),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini/gemini-2.5-flash"),
        gemini_model_fallback=os.getenv("GEMINI_MODEL_FALLBACK", "gemini/gemini-2.0-flash") or None,
        feishu_webhook_url=os.getenv("FEISHU_WEBHOOK_URL") or None,
        feishu_webhook_secret=os.getenv("FEISHU_WEBHOOK_SECRET") or None,
        feishu_webhook_keyword=os.getenv("FEISHU_WEBHOOK_KEYWORD") or None,
        wechat_webhook_url=os.getenv("WECHAT_WEBHOOK_URL") or None,
        wechat_msg_type=os.getenv("WECHAT_MSG_TYPE", "text"),
        wechat_personal_compat=_env_bool("WECHAT_PERSONAL_COMPAT", default=True),
        economics_feishu_webhook_url=os.getenv("ECONOMICS_FEISHU_WEBHOOK_URL") or None,
        economics_feishu_webhook_secret=os.getenv("ECONOMICS_FEISHU_WEBHOOK_SECRET") or None,
        economics_feishu_webhook_keyword=os.getenv("ECONOMICS_FEISHU_WEBHOOK_KEYWORD") or None,
        economics_wechat_webhook_url=os.getenv("ECONOMICS_WECHAT_WEBHOOK_URL") or None,
        economics_wechat_msg_type=os.getenv("ECONOMICS_WECHAT_MSG_TYPE", "text"),
        law_feishu_webhook_url=os.getenv("LAW_FEISHU_WEBHOOK_URL") or None,
        law_feishu_webhook_secret=os.getenv("LAW_FEISHU_WEBHOOK_SECRET") or None,
        law_feishu_webhook_keyword=os.getenv("LAW_FEISHU_WEBHOOK_KEYWORD") or None,
        law_wechat_webhook_url=os.getenv("LAW_WECHAT_WEBHOOK_URL") or None,
        law_wechat_msg_type=os.getenv("LAW_WECHAT_MSG_TYPE", "text"),
        business_feishu_webhook_url=os.getenv("BUSINESS_FEISHU_WEBHOOK_URL") or None,
        business_feishu_webhook_secret=os.getenv("BUSINESS_FEISHU_WEBHOOK_SECRET") or None,
        business_feishu_webhook_keyword=os.getenv("BUSINESS_FEISHU_WEBHOOK_KEYWORD") or None,
        business_wechat_webhook_url=os.getenv("BUSINESS_WECHAT_WEBHOOK_URL") or None,
        business_wechat_msg_type=os.getenv("BUSINESS_WECHAT_MSG_TYPE", "text"),
        webhook_verify_ssl=verify_ssl,
    )


def resolve_book_path(config: AppConfig, book: BookConfig) -> Path:
    path = Path(book.file)
    if not path.is_absolute():
        path = config.root_dir / path
    return path


def select_channel_notifier_config(config: AppConfig, channel: str) -> AppConfig:
    if channel == "economics":
        return replace(
            config,
            feishu_webhook_url=config.economics_feishu_webhook_url,
            feishu_webhook_secret=config.economics_feishu_webhook_secret,
            feishu_webhook_keyword=config.economics_feishu_webhook_keyword,
            wechat_webhook_url=config.economics_wechat_webhook_url,
            wechat_msg_type=config.economics_wechat_msg_type,
            wechat_personal_compat=config.wechat_personal_compat,
            notification_title="每日经济学",
        )
    if channel == "law":
        return replace(
            config,
            feishu_webhook_url=config.law_feishu_webhook_url,
            feishu_webhook_secret=config.law_feishu_webhook_secret,
            feishu_webhook_keyword=config.law_feishu_webhook_keyword,
            wechat_webhook_url=config.law_wechat_webhook_url,
            wechat_msg_type=config.law_wechat_msg_type,
            wechat_personal_compat=config.wechat_personal_compat,
            notification_title="每日法学",
        )
    if channel == "business":
        return replace(
            config,
            feishu_webhook_url=config.business_feishu_webhook_url,
            feishu_webhook_secret=config.business_feishu_webhook_secret,
            feishu_webhook_keyword=config.business_feishu_webhook_keyword,
            wechat_webhook_url=config.business_wechat_webhook_url,
            wechat_msg_type=config.business_wechat_msg_type,
            wechat_personal_compat=config.wechat_personal_compat,
            notification_title="每日商业案例",
        )
    return config
