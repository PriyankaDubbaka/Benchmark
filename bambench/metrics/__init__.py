"""Scoring. Pure Python, no model calls, no LLM judge."""

# Raised whenever a change to the metrics can move a score. Every summary records the version it
# was scored with, and the leaderboard marks rows from an older one. `bambench rescore` brings
# them up to date from the saved outputs. docs/CHANGELOG.md says what each version changed.
SCORER_VERSION = 2
