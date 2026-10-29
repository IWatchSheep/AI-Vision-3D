"""Stage 3C: game tree search (LOOP and TRACE reports).

Split across:
  mate_search.py   forced-mate helpers
  loop_report.py   LOOP tree walk
  trace_report.py  TRACE with CALC per ply
"""

from .loop_report import loop_report, zero_move_pieces
from .mate_search import first_move_forces, mate_forced
from .trace_report import trace_report

__all__ = [
    "zero_move_pieces",
    "mate_forced",
    "first_move_forces",
    "loop_report",
    "trace_report",
]
