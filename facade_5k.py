
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
import pandas as pd

from .athlete import AthleteConfig
from .sessions import build_5k_session_library
from .selection import WeeklySessionSelector
from .volume import WeeklyVolumePlanner
from .zones import DanielsZones
from .pacing import weekly_plan_to_workouts, workouts_to_dataframe


def estimate_vdot_from_race(distance_km: float, time_min: float) -> float:
    distance_m = distance_km * 1000.0
    v = distance_m / time_min  # m/min
    vo2 = -4.60 + 0.182258 * v + 0.000104 * v * v
    frac = 0.8 + 0.1894393 * np.exp(-0.012778 * time_min) + 0.2989558 * np.exp(-0.1932605 * time_min)
    vdot = vo2 / frac
    return float(vdot)


@dataclass
class SimplePhaseDef:
    name: str
    proportion: float
    priority: int


def build_5k_phase_sequence_simple(total_weeks: int) -> List[str]:
    phases = [
        SimplePhaseDef("Base", 0.30, priority=1),
        SimplePhaseDef("EarlyQ", 0.15, priority=2),
        SimplePhaseDef("Threshold", 0.20, priority=3),
        SimplePhaseDef("Interval", 0.30, priority=5),
        SimplePhaseDef("Repetition", 0.20, priority=4),
        SimplePhaseDef("RS", 0.05, priority=10),
        SimplePhaseDef("Taper", 0.05, priority=10),
    ]
    S = sum(p.proportion for p in phases)
    for p in phases:
        p.proportion = p.proportion / S
    weeks_map = {}
    for p in phases:
        w = max(1, round(p.proportion * total_weeks))
        weeks_map[p.name] = w
    current_total = sum(weeks_map.values())
    diff = current_total - total_weeks
    classic_order = ["Base", "EarlyQ", "Threshold", "Interval", "Repetition", "RS", "Taper"]
    if diff > 0:
        phases_sorted = sorted(phases, key=lambda p: (p.priority, classic_order.index(p.name)))
        while diff > 0:
            for p in phases_sorted:
                if weeks_map[p.name] > 1:
                    weeks_map[p.name] -= 1
                    diff -= 1
                    if diff == 0:
                        break
    elif diff < 0:
        phases_sorted = sorted(phases, key=lambda p: (-p.priority, -classic_order.index(p.name)))
        while diff < 0:
            for p in phases_sorted:
                weeks_map[p.name] += 1
                diff += 1
                if diff == 0:
                    break
    phase_sequence: List[str] = []
    for name in classic_order:
        n_weeks = weeks_map.get(name, 0)
        phase_sequence.extend([name] * n_weeks)
    return phase_sequence[:total_weeks]


def generate_5k_plan_from_race(
    athlete_name: str,
    race_distance_km: float,
    race_time_min: float,
    frequency_per_week: int,
    total_weeks: int = 8,
    initial_weekly_volume: float = 30.0,
    peak_weekly_volume: float = 50.0,
) -> Tuple[pd.DataFrame, float]:
    vdot = estimate_vdot_from_race(distance_km=race_distance_km, time_min=race_time_min)
    athlete = AthleteConfig(
        name=athlete_name,
        frequency_per_week=frequency_per_week,
        objective="5K",
        initial_weekly_volume=initial_weekly_volume,
        peak_weekly_volume=peak_weekly_volume,
    )
    phase_sequence = build_5k_phase_sequence_simple(total_weeks)
    session_lib = build_5k_session_library()
    selector = WeeklySessionSelector(athlete, session_lib)
    weekly_plan = selector.build_weekly_plan(phase_sequence)
    volume_planner = WeeklyVolumePlanner(athlete)
    weekly_targets = volume_planner.compute_weekly_targets(phase_sequence)
    weekly_plan_with_vol = volume_planner.apply_volume_to_plan(weekly_plan, weekly_targets)
    zones_df = DanielsZones(vdot).build_dataframe()
    workouts = weekly_plan_to_workouts(weekly_plan_with_vol, athlete, zones_df)
    df_plan = workouts_to_dataframe(workouts)
    return df_plan, vdot
