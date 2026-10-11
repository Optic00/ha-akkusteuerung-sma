from datetime import UTC, datetime, timedelta

from custom_components.opti_akku.refill_comparison import (
    RefillReserveComparison,
    refill_reserve_check,
)

T0 = datetime(2026, 10, 1, 22, 0, tzinfo=UTC)
DEMAND = {"status": "ready", "suggested_reserve_soc": 40.0, "refill_profile_ready": True,
          "refill_covered": True, "refill_coverage_percent": 95.0}
PLAN = {"planned_reserve_soc": 50.0, "hold_threshold_soc": 55.0}
STATES = {"binary_sensor.opti_peak_reserve_aktiv": "on", "sensor.opti_soc": "45",
          "sensor.opti_battery_capacity_kwh": "10"}


def check(demand=None, plan=None, states=None):
    return refill_reserve_check(
        DEMAND if demand is None else demand,
        PLAN if plan is None else plan,
        STATES if states is None else states,
    )


def test_ready_result_and_flags():
    result = check()
    assert result["status"] == "ready"
    assert result["informational_only"] is True
    assert result["controls_battery"] is False
    assert result["compares"] == "hold_floor_only"
    assert result["note"]
    assert result["peak_hold_soc"] == 55.0
    assert result["planned_reserve_soc"] == 50.0
    assert result["refill_reserve_soc"] == 40.0
    assert result["difference_soc"] == 15.0
    assert result["difference_kwh"] == 1.5
    assert result["verdict"] == "peak_only"
    assert result["refill_covered"] is True
    assert result["refill_coverage_percent"] == 95.0


def test_four_verdicts():
    def verdict(soc, peak, refill):
        return check(
            {**DEMAND, "suggested_reserve_soc": refill},
            {"hold_threshold_soc": peak},
            {**STATES, "sensor.opti_soc": soc},
        )["verdict"]

    assert verdict(30, 55, 40) == "both_hold"
    assert verdict(60, 55, 40) == "both_release"
    assert verdict(45, 55, 40) == "peak_only"
    assert verdict(45, 40, 55) == "refill_only"


def test_boundary_equality_holds():
    result = check(states={**STATES, "sensor.opti_soc": 55})
    assert result["peak_holds"] is True
    assert result["refill_holds"] is False
    result = check(states={**STATES, "sensor.opti_soc": 40})
    assert result["refill_holds"] is True


def test_not_applicable():
    assert check(states={**STATES, "binary_sensor.opti_peak_reserve_aktiv": "off"})["status"] == "not_applicable"
    assert check(plan={})["status"] == "not_applicable"
    assert refill_reserve_check(None, None, None)["status"] == "not_applicable"


def test_planned_reserve_is_fallback_for_missing_hold_threshold():
    result = check(plan={"planned_reserve_soc": 50.0, "hold_threshold_soc": None})
    assert result["peak_hold_soc"] == 50.0
    assert result["peak_source"] == "planned_reserve"
    assert check()["peak_source"] == "hold_threshold"


def test_totals_keep_peak_sources_apart():
    acc = RefillReserveComparison()
    acc.observe(T0, check())
    acc.observe(T0 + timedelta(seconds=30), check(plan={"planned_reserve_soc": 50.0}))
    totals = acc.observe(T0 + timedelta(seconds=50), check())
    assert totals["hold_threshold_seconds"] == 30
    assert totals["planned_reserve_seconds"] == 20
    assert totals["ready_seconds"] == 50


def test_forecast_unavailable_and_profile():
    assert check({**DEMAND, "status": "learning"})["status"] == "forecast_unavailable"
    assert check({**DEMAND, "suggested_reserve_soc": None})["status"] == "forecast_unavailable"
    assert check({**DEMAND, "suggested_reserve_soc": float("nan")})["status"] == "forecast_unavailable"
    assert check({**DEMAND, "suggested_reserve_soc": True})["status"] == "forecast_unavailable"
    assert check({**DEMAND, "refill_profile_ready": False})["status"] == "profile_not_ready"
    assert check({**DEMAND, "refill_profile_ready": "yes"})["status"] == "profile_not_ready"


def test_soc_missing_and_invalid_numbers():
    for bad in (None, "unknown", float("inf"), True):
        assert check(states={**STATES, "sensor.opti_soc": bad})["status"] == "soc_missing"
    assert check(plan={"hold_threshold_soc": True, "planned_reserve_soc": "x"})["status"] == "not_applicable"


def test_capacity_missing_gives_no_kwh():
    for bad in (None, "unknown", 0, -5, True):
        result = check(states={**STATES, "sensor.opti_battery_capacity_kwh": bad})
        assert result["status"] == "ready"
        assert result["difference_kwh"] is None


def _ready(verdict_soc=45):
    return check(states={**STATES, "sensor.opti_soc": verdict_soc})


def test_accumulator_holds_previous_check_and_ignores_gaps():
    acc = RefillReserveComparison()
    totals = acc.observe(T0, _ready(45))
    assert totals["ready_seconds"] == 0
    assert totals["mean_difference_soc"] is None
    totals = acc.observe(T0 + timedelta(seconds=30), _ready(30))
    assert totals["peak_only_seconds"] == 30
    totals = acc.observe(T0 + timedelta(seconds=50), _ready(30))
    assert totals["both_hold_seconds"] == 20
    assert totals["ready_seconds"] == 50
    assert totals["mean_difference_soc"] == 15.0
    assert totals["disagreement_percent"] == 60.0
    # gap over 90 s does not count
    totals = acc.observe(T0 + timedelta(seconds=200), _ready(30))
    assert totals["ready_seconds"] == 50
    # a non-ready held check does not count
    totals = acc.observe(T0 + timedelta(seconds=210), check(states={**STATES, "sensor.opti_soc": None}))
    assert totals["ready_seconds"] == 60
    totals = acc.observe(T0 + timedelta(seconds=220), _ready(30))
    assert totals["ready_seconds"] == 60


def test_accumulator_clock_backwards_and_interrupt():
    acc = RefillReserveComparison()
    acc.observe(T0, _ready())
    totals = acc.observe(T0 - timedelta(seconds=10), _ready())
    assert totals["ready_seconds"] == 0
    acc.interrupt()
    acc.observe(T0, _ready())
    acc.interrupt()
    totals = acc.observe(T0 + timedelta(seconds=30), _ready())
    assert totals["ready_seconds"] == 0


def test_snapshot_restore_roundtrip_and_broken_input():
    acc = RefillReserveComparison()
    acc.observe(T0, _ready(45))
    acc.observe(T0 + timedelta(seconds=40), _ready(45))
    other = RefillReserveComparison()
    other.restore(acc.snapshot())
    assert other.data == acc.data
    # restored accumulator does not count the first interval after restart
    totals = other.observe(T0 + timedelta(seconds=60), _ready(45))
    assert totals["ready_seconds"] == 40
    for broken in (
        None, "x", {}, {"version": 2},
        {**acc.snapshot(), "ready_seconds": -1},
        {**acc.snapshot(), "ready_seconds": float("nan")},
        {**acc.snapshot(), "peak_only_seconds": True},
        {**acc.snapshot(), "started_at": "not a date"},
        {**acc.snapshot(), "started_at": "2026-10-01T22:00:00"},
        {**acc.snapshot(), "difference_soc_seconds": None},
        {**acc.snapshot(), "last_observation": 5},
        {**acc.snapshot(), "peak_only_seconds": 100.0},
        {**acc.snapshot(), "hold_threshold_seconds": 0.0, "planned_reserve_seconds": 5.0},
    ):
        fresh = RefillReserveComparison()
        fresh.restore(broken)
        assert fresh.data == RefillReserveComparison().data


def test_soc_outside_range_is_invalid():
    for soc in (-0.1, 100.1, 250):
        assert check(states={**STATES, "sensor.opti_soc": soc})["status"] == "soc_invalid"
