"""Public entry for study reports (goals, calc, replies, routes, exchange).

Implementation lives under study/; cli_analysis_cmds and cli_goal_cmds call
these helpers. Importing here keeps one stable name for the rest of the engine.
"""
from .study import *  # noqa: F401
