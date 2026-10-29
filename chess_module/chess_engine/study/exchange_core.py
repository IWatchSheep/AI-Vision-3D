"""Stage 3E: capture exchanges and move ordering.

Split across:
  exchange_gain.py    capture helpers and minimax value
  exchange_report.py  printed EXCHANGE report
  exchange_order.py   printed ORDER report
"""

from .exchange_gain import (
    captured_type,
    captures_on,
    capture_gain,
    exchange_value,
    first_capture_class,
    material_text,
    promotion_gain,
)
from .exchange_order import order_report
from .exchange_report import exchange_report

# Older private names kept for any direct callers.
_promotion_gain = promotion_gain
_capture_gain = capture_gain

__all__ = [
    "captured_type",
    "captures_on",
    "exchange_value",
    "first_capture_class",
    "material_text",
    "exchange_report",
    "order_report",
    "_promotion_gain",
    "_capture_gain",
]
