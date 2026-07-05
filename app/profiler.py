"""
app/profiler.py
---------------
VELNIX Pipeline Profiler — measurement-only, no optimisations.

Usage
-----
Attach to a request by calling ``PipelineProfiler(run_id)`` at the top of
the upload handler, then use the ``.stage()`` context manager at each step.
At the end call ``profiler.finish()`` to get a ``ProfileReport``.

Design constraints
------------------
- No changes to agent logic or business rules.
- No async dependencies (uses time.perf_counter throughout).
- All timing is wall-clock (includes I/O + API latency).
- Thread-safe per-request instances; no shared global state.
"""

from __future__ import annotations

import logging
import time
import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_log = logging.getLogger("velnix.profiler")


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class StageRecord:
    """One timed measurement for a named pipeline stage."""
    stage: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def finish(self, **meta):
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000.0
        self.metadata.update(meta)
        return self


@dataclass
class GeminiCallRecord:
    """Timing record for one Gemini API call."""
    caller: str
    prompt_chars: int
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    model: str = "unknown"
    call_type: str = "generate_content"

    def finish(self):
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000.0
        return self


@dataclass
class SqliteCallRecord:
    """Timing record for one SQLite query."""
    function_name: str
    query_type: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    hit: Optional[bool] = None

    def finish(self, hit: Optional[bool] = None):
        self.end_time = time.perf_counter()
        self.duration_ms = (self.end_time - self.start_time) * 1000.0
        self.hit = hit
        return self


# ---------------------------------------------------------------------------
# Main profiler
# ---------------------------------------------------------------------------

class PipelineProfiler:
    """Collects timing data for one complete invoice investigation run."""

    def __init__(self, run_id: str = ""):
        self.run_id = run_id or f"run-{int(time.time())}"
        self.pipeline_start: float = time.perf_counter()
        self.pipeline_end: float = 0.0
        self.stages: List[StageRecord] = []
        self.gemini_calls: List[GeminiCallRecord] = []
        self.sqlite_calls: List[SqliteCallRecord] = []
        self._active_stages: Dict[str, StageRecord] = {}

    @contextmanager
    def stage(self, name: str, **initial_meta):
        """Context manager that records start/end wall-clock time for a stage."""
        rec = StageRecord(stage=name, start_time=time.perf_counter(), metadata=dict(initial_meta))
        self._active_stages[name] = rec
        try:
            yield rec
        except Exception as exc:
            rec.error = str(exc)
            raise
        finally:
            rec.finish()
            self.stages.append(rec)
            self._active_stages.pop(name, None)
            _log.info(
                "[PROFILER] %-38s  %8.1f ms  %s",
                name,
                rec.duration_ms,
                json.dumps(rec.metadata, default=str) if rec.metadata else "",
            )

    def record_gemini_call(
        self,
        caller: str,
        prompt_chars: int,
        model: str = "gemini-2.5-flash",
        call_type: str = "generate_content",
    ) -> GeminiCallRecord:
        rec = GeminiCallRecord(
            caller=caller,
            prompt_chars=prompt_chars,
            start_time=time.perf_counter(),
            model=model,
            call_type=call_type,
        )
        self.gemini_calls.append(rec)
        return rec

    def record_sqlite(self, function_name: str, query_type: str) -> SqliteCallRecord:
        rec = SqliteCallRecord(
            function_name=function_name,
            query_type=query_type,
            start_time=time.perf_counter(),
        )
        self.sqlite_calls.append(rec)
        return rec

    def finish(self) -> "ProfileReport":
        self.pipeline_end = time.perf_counter()
        total_ms = (self.pipeline_end - self.pipeline_start) * 1000.0
        return ProfileReport(profiler=self, total_ms=total_ms)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class ProfileReport:
    """Computed, human-readable profiling report for one pipeline run."""

    def __init__(self, profiler: PipelineProfiler, total_ms: float):
        self.run_id = profiler.run_id
        self.total_ms = total_ms
        self.stages = list(profiler.stages)
        self.gemini_calls = list(profiler.gemini_calls)
        self.sqlite_calls = list(profiler.sqlite_calls)

    def stage_table(self) -> List[Dict]:
        rows = []
        for s in self.stages:
            rows.append({
                "stage": s.stage,
                "duration_ms": round(s.duration_ms, 1),
                "pct_of_total": round(s.duration_ms / self.total_ms * 100, 1) if self.total_ms else 0,
                "metadata": s.metadata,
                "error": s.error,
            })
        rows.sort(key=lambda r: r["duration_ms"], reverse=True)
        return rows

    def gemini_summary(self) -> Dict:
        if not self.gemini_calls:
            return {"count": 0, "total_ms": 0.0, "are_sequential": True, "calls": []}
        total = sum(c.duration_ms for c in self.gemini_calls)
        return {
            "count": len(self.gemini_calls),
            "total_ms": round(total, 1),
            # Root orchestrator calls sub-agents one by one in a loop → sequential
            "are_sequential": True,
            "calls": [
                {
                    "caller": c.caller,
                    "model": c.model,
                    "prompt_chars": c.prompt_chars,
                    "duration_ms": round(c.duration_ms, 1),
                }
                for c in self.gemini_calls
            ],
        }

    def sqlite_summary(self) -> Dict:
        if not self.sqlite_calls:
            return {"count": 0, "total_ms": 0.0, "calls": []}
        total = sum(c.duration_ms for c in self.sqlite_calls)
        return {
            "count": len(self.sqlite_calls),
            "total_ms": round(total, 1),
            "calls": [
                {
                    "function": c.function_name,
                    "query_type": c.query_type,
                    "duration_ms": round(c.duration_ms, 1),
                    "hit": c.hit,
                }
                for c in self.sqlite_calls
            ],
        }

    def top_bottlenecks(self, n: int = 5) -> List[Dict]:
        return self.stage_table()[:n]

    def to_dict(self) -> Dict:
        return {
            "run_id": self.run_id,
            "total_pipeline_ms": round(self.total_ms, 1),
            "stage_breakdown": self.stage_table(),
            "gemini_api": self.gemini_summary(),
            "sqlite_queries": self.sqlite_summary(),
            "top_bottlenecks": self.top_bottlenecks(),
        }

    def to_log_lines(self) -> str:
        """Human-readable multi-line string for server log output."""
        SEP = "=" * 72
        lines = [
            SEP,
            f"VELNIX PIPELINE PROFILE  run_id={self.run_id}",
            f"Total wall-clock time : {self.total_ms:,.1f} ms",
            SEP,
            f"{'Stage':<40} {'ms':>10}  {'%':>6}  Notes",
            "-" * 72,
        ]
        for row in self.stage_table():
            notes = ""
            m = row.get("metadata", {})
            if m:
                notes = "  ".join(f"{k}={v}" for k, v in m.items() if v is not None)
            if row.get("error"):
                notes = f"ERROR: {row['error']}"
            lines.append(
                f"{row['stage']:<40} {row['duration_ms']:>10,.1f}  "
                f"{row['pct_of_total']:>5.1f}%  {notes}"
            )

        g = self.gemini_summary()
        lines += [
            SEP,
            f"Gemini API calls      : {g['count']}  total={g['total_ms']:,.1f} ms  sequential={g['are_sequential']}",
            f"  NOTE: Each sub-agent makes its own separate Gemini call (no batching).",
            f"  NOTE: A 13-second rate-limit delay is enforced between calls (free-tier patch).",
        ]
        for c in g.get("calls", []):
            lines.append(
                f"  [{c['caller']:<30}]  {c['duration_ms']:>8,.1f} ms  "
                f"model={c['model']}  prompt_chars={c['prompt_chars']:,}"
            )

        sq = self.sqlite_summary()
        lines += [
            SEP,
            f"SQLite queries        : {sq['count']}  total={sq['total_ms']:,.1f} ms",
        ]
        for c in sq.get("calls", []):
            hit_str = f"hit={c['hit']}" if c["hit"] is not None else ""
            lines.append(
                f"  [{c['function']:<30}]  {c['duration_ms']:>8,.1f} ms  {c['query_type']}  {hit_str}"
            )

        lines += [
            SEP,
            "TOP BOTTLENECKS (by wall-clock duration)",
            "-" * 72,
        ]
        for i, row in enumerate(self.top_bottlenecks(), 1):
            lines.append(
                f"  {i}. {row['stage']:<38} {row['duration_ms']:>8,.1f} ms  ({row['pct_of_total']}%)"
            )
        lines.append(SEP)
        return "\n".join(lines)
