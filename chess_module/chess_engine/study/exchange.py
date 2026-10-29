"""Stage 3E and 3F: capture exchanges, move ordering, and move comparison.

Re-exports exchange_core (EXCHANGE, ORDER) and exchange_compare (COMPARE).
Import from here to match older study package paths.
"""

from .common import piece_value
from .search import loop_report
from .exchange_core import (
    captured_type,
    captures_on,
    exchange_value,
    first_capture_class,
    material_text,
    exchange_report,
    order_report,
)
from .exchange_compare import compare_report

__all__ = [
    "piece_value",
    "captured_type",
    "captures_on",
    "exchange_value",
    "first_capture_class",
    "material_text",
    "exchange_report",
    "order_report",
    "compare_report",
]
