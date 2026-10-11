"""Observation-only comparison of the peak hold floor with the refill reserve.

Nothing here feeds back into control, mode, parameters or the decision id.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from math import isfinite
from typing import Any

MAX_INTERVAL = 90
VERDICTS = ("both_hold", "both_release", "peak_only", "refill_only")
_VERDICT_COUNTERS = (
    "both_hold_seconds",
    "both_release_seconds",
    "peak_only_seconds",
    "refill_only_seconds",
)
# Which strategy value served as the peak floor; both are counted separately so
# mixed totals stay visible (hold threshold only exists while actively holding).
PEAK_SOURCES = ("hold_threshold", "planned_reserve")
_SOURCE_COUNTERS = tuple(f"{source}_seconds" for source in PEAK_SOURCES)
_COUNTERS = ("ready_seconds", *_VERDICT_COUNTERS, *_SOURCE_COUNTERS)
_SIGNED = ("difference_soc_seconds",)
NOTE = (
    "The refill reserve covers the whole demand until PV cover, the peak reserve "
    "only expensive slots. This compares hold floors only, not strategy "
    "decisions, and does not show which floor is right."
)


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if isfinite(result) else None


def refill_reserve_check(demand: Any, plan: Any, states: Any) -> dict[str, Any]:
    """Compare the active peak hold floor with the refill reserve of the demand forecast."""
    base: dict[str, Any] = {
        "compares": "hold_floor_only",
        "informational_only": True,
        "controls_battery": False,
        "note": NOTE,
    }
    demand = demand if isinstance(demand, Mapping) else {}
    plan = plan if isinstance(plan, Mapping) else {}
    states = states if isinstance(states, Mapping) else {}
    planned = _number(plan.get("planned_reserve_soc"))
    hold = _number(plan.get("hold_threshold_soc"))
    peak = hold if hold is not None else planned
    source = "hold_threshold" if hold is not None else "planned_reserve"
    if states.get("binary_sensor.opti_peak_reserve_aktiv") != "on" or peak is None:
        return {**base, "status": "not_applicable"}
    refill = _number(demand.get("suggested_reserve_soc"))
    if demand.get("status") != "ready" or refill is None:
        return {**base, "status": "forecast_unavailable"}
    if demand.get("refill_profile_ready") is not True:
        return {**base, "status": "profile_not_ready"}
    soc = _number(states.get("sensor.opti_soc"))
    if soc is None:
        return {**base, "status": "soc_missing"}
    capacity = _number(states.get("sensor.opti_battery_capacity_kwh"))
    difference = peak - refill
    peak_holds = soc <= peak
    refill_holds = soc <= refill
    verdict = (
        "both_hold" if peak_holds and refill_holds
        else "peak_only" if peak_holds
        else "refill_only" if refill_holds
        else "both_release"
    )
    coverage = _number(demand.get("refill_coverage_percent"))
    covered = demand.get("refill_covered")
    return {
        **base,
        "status": "ready",
        "soc": round(soc, 3),
        "peak_hold_soc": round(peak, 3),
        "peak_source": source,
        "planned_reserve_soc": round(planned, 3) if planned is not None else None,
        "refill_reserve_soc": round(refill, 3),
        "difference_soc": round(difference, 3),
        "difference_kwh": (
            round(difference / 100 * capacity, 3)
            if capacity is not None and capacity > 0 else None
        ),
        "peak_holds": peak_holds,
        "refill_holds": refill_holds,
        "verdict": verdict,
        "refill_covered": covered if isinstance(covered, bool) else None,
        "refill_coverage_percent": round(coverage, 3) if coverage is not None else None,
    }


class RefillReserveComparison:
    """Time-weighted totals of the peak-versus-refill verdicts.

    Zero-order hold over the previous check. Intervals over 90 s, the first
    check after a restart and backwards clock steps never count.
    """

    def __init__(self) -> None:
        self.data = self._fresh()
        self._previous: tuple[datetime, dict[str, Any]] | None = None

    @staticmethod
    def _fresh() -> dict[str, Any]:
        return {
            "version": 1,
            "started_at": None,
            "last_observation": None,
            **{key: 0.0 for key in (*_COUNTERS, *_SIGNED)},
        }

    def snapshot(self) -> dict[str, Any]:
        return dict(self.data)

    def restore(self, saved: Any) -> None:
        self.data = self._fresh()
        self._previous = None
        try:
            if not isinstance(saved, Mapping) or saved.get("version") != 1:
                return
            stamps: dict[str, Any] = {}
            for key in ("started_at", "last_observation"):
                raw = saved.get(key)
                if raw is not None:
                    if datetime.fromisoformat(raw).tzinfo is None:
                        return
                stamps[key] = raw
            counters: dict[str, float] = {}
            for key in (*_COUNTERS, *_SIGNED):
                value = _number(saved.get(key))
                if value is None or (key in _COUNTERS and value < 0):
                    return
                counters[key] = value
            ready = counters["ready_seconds"]
            tolerance = 1e-6 * max(1.0, ready)
            if (abs(sum(counters[key] for key in _VERDICT_COUNTERS) - ready) > tolerance
                    or abs(sum(counters[key] for key in _SOURCE_COUNTERS) - ready) > tolerance):
                return
        except (TypeError, ValueError, OverflowError, AttributeError):
            return
        self.data = {"version": 1, **stamps, **counters}

    def _totals(self) -> dict[str, Any]:
        out: dict[str, Any] = {key: round(self.data[key], 3) for key in _COUNTERS}
        ready = self.data["ready_seconds"]
        out["mean_difference_soc"] = (
            round(self.data["difference_soc_seconds"] / ready, 3) if ready > 0 else None
        )
        out["disagreement_percent"] = (
            round((self.data["peak_only_seconds"] + self.data["refill_only_seconds"]) / ready * 100, 3)
            if ready > 0 else None
        )
        out["started_at"] = self.data["started_at"]
        out["last_observation"] = self.data["last_observation"]
        return out

    def interrupt(self) -> None:
        """A failed observation ends the held verdict; the gap never counts."""
        self._previous = None

    def observe(self, now: datetime, check: Mapping[str, Any]) -> dict[str, Any]:
        if self.data["started_at"] is None:
            self.data["started_at"] = now.isoformat()
        if self._previous is not None:
            before, held = self._previous
            elapsed = (now - before).total_seconds()
            if 0 < elapsed <= MAX_INTERVAL and held.get("status") == "ready":
                self.data["ready_seconds"] += elapsed
                self.data[f"{held['verdict']}_seconds"] += elapsed
                self.data[f"{held['peak_source']}_seconds"] += elapsed
                self.data["difference_soc_seconds"] += elapsed * held["difference_soc"]
        self._previous = (now, dict(check))
        self.data["last_observation"] = now.isoformat()
        return self._totals()
