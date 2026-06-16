from datetime import date
from unittest.mock import patch

from src.config import RecommendConfig


def test_alternate_even_day_read():
    cfg = RecommendConfig(alternate_even_day="read")
    from main import _resolve_alternate_mode

    with patch("main.date") as mock_date:
        mock_date.today.return_value.toordinal.return_value = 100  # even
        assert _resolve_alternate_mode(cfg) == "read"
        mock_date.today.return_value.toordinal.return_value = 101  # odd
        assert _resolve_alternate_mode(cfg) == "recommend"
