
from dataclasses import dataclass
from itertools import groupby
from numbers import Integral
from typing import List, Optional, Sequence, Tuple
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


PHASE_ORDER = ("Base", "EarlyQ", "Threshold", "Interval", "Repetition", "RS", "Taper")

# These are short planning windows, not seven compressed adaptation phases.
# Keep an introductory week and a final taper; add distinct quality emphases
# only when there is room. This policy follows the existing library's order.
SHORT_PHASE_SEQUENCES = {
    2: ("Base", "Taper"),
    3: ("Base", "Threshold", "Taper"),
    4: ("Base", "Threshold", "Interval", "Taper"),
    5: ("Base", "Threshold", "Interval", "RS", "Taper"),
    6: ("Base", "EarlyQ", "Threshold", "Interval", "RS", "Taper"),
}


def _validate_weeks(value: int, field: str, minimum: int) -> None:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{field} deve ser um número inteiro de semanas.")
    if value < minimum:
        raise ValueError(f"{field} deve ser >= {minimum}.")


@dataclass(frozen=True)
class Mesocycle:
    """One contiguous block with a library phase and an exact week count.

    One-week blocks are allowed at planning-window boundaries (e.g. taper);
    they do not imply a complete physiological adaptation in one week.
    """

    phase: str
    weeks: int

    def __post_init__(self) -> None:
        if self.phase not in PHASE_ORDER:
            raise ValueError(f"Fase desconhecida: {self.phase!r}. Use {PHASE_ORDER}.")
        _validate_weeks(self.weeks, "Mesocycle.weeks", 1)


def _automatic_phase_sequence(total_weeks: int) -> List[str]:
    if total_weeks < len(PHASE_ORDER):
        return list(SHORT_PHASE_SEQUENCES[total_weeks])

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
    classic_order = PHASE_ORDER
    if diff > 0:
        phases_sorted = sorted(phases, key=lambda p: (p.priority, classic_order.index(p.name)))
        # At least seven weeks are available, so the removable capacity is
        # sufficient. Bound every pass instead of waiting for convergence.
        for _ in range(diff):
            for p in phases_sorted:
                if weeks_map[p.name] > 1:
                    weeks_map[p.name] -= 1
                    diff -= 1
                    if diff == 0:
                        break
            if diff == 0:
                break
    elif diff < 0:
        phases_sorted = sorted(phases, key=lambda p: (-p.priority, -classic_order.index(p.name)))
        for _ in range(-diff):
            for p in phases_sorted:
                weeks_map[p.name] += 1
                diff += 1
                if diff == 0:
                    break
            if diff == 0:
                break
    phase_sequence: List[str] = []
    for name in classic_order:
        n_weeks = weeks_map.get(name, 0)
        phase_sequence.extend([name] * n_weeks)
    if len(phase_sequence) != total_weeks:
        raise RuntimeError("A distribuição automática não conservou o total de semanas.")
    return phase_sequence


def build_5k_mesocycles(
    total_weeks: int,
    *,
    mesocycles: Optional[Sequence[Mesocycle]] = None,
) -> List[Mesocycle]:
    """Resolve automatic or coach-defined blocks for a single planning window.

    Explicit blocks must sum exactly to total_weeks, use known phases and
    follow the library order (adjacent blocks of the same phase are allowed).
    A window may start/end within the progression: neither Base nor Taper
    is mandatory in explicit mode. Use separate windows for another peak.
    """
    _validate_weeks(total_weeks, "total_weeks", 2)
    if mesocycles is None:
        sequence = _automatic_phase_sequence(total_weeks)
        return [Mesocycle(phase, len(list(weeks))) for phase, weeks in groupby(sequence)]

    if isinstance(mesocycles, (str, bytes)) or not isinstance(mesocycles, Sequence):
        raise TypeError("mesocycles deve ser uma sequência de objetos Mesocycle.")
    blocks = list(mesocycles)
    if not blocks:
        raise ValueError("mesocycles não pode ser vazio; use None para modo automático.")
    if any(not isinstance(block, Mesocycle) for block in blocks):
        raise TypeError("Cada item de mesocycles deve ser um objeto Mesocycle.")
    if sum(block.weeks for block in blocks) != total_weeks:
        raise ValueError("A soma das semanas dos mesociclos deve ser igual a total_weeks.")
    positions = [PHASE_ORDER.index(block.phase) for block in blocks]
    if any(left > right for left, right in zip(positions, positions[1:])):
        raise ValueError("Mesociclos devem seguir a ordem de fases da biblioteca.")
    return blocks


def build_5k_phase_sequence_simple(
    total_weeks: int,
    *,
    mesocycles: Optional[Sequence[Mesocycle]] = None,
) -> List[str]:
    """Return exactly total_weeks phases, supporting windows of at least two weeks."""
    blocks = build_5k_mesocycles(total_weeks, mesocycles=mesocycles)
    return [block.phase for block in blocks for _ in range(block.weeks)]


def generate_5k_plan_from_race(
    athlete_name: str,
    race_distance_km: float,
    race_time_min: float,
    frequency_per_week: int,
    total_weeks: int = 8,
    initial_weekly_volume: float = 30.0,
    peak_weekly_volume: float = 50.0,
    *,
    mesocycles: Optional[Sequence[Mesocycle]] = None,
) -> Tuple[pd.DataFrame, float]:
    blocks = build_5k_mesocycles(total_weeks, mesocycles=mesocycles)
    phase_sequence = [block.phase for block in blocks for _ in range(block.weeks)]
    vdot = estimate_vdot_from_race(distance_km=race_distance_km, time_min=race_time_min)
    athlete = AthleteConfig(
        name=athlete_name,
        frequency_per_week=frequency_per_week,
        objective="5K",
        initial_weekly_volume=initial_weekly_volume,
        peak_weekly_volume=peak_weekly_volume,
    )
    session_lib = build_5k_session_library()
    selector = WeeklySessionSelector(athlete, session_lib)
    weekly_plan = selector.build_weekly_plan(phase_sequence)
    volume_planner = WeeklyVolumePlanner(athlete)
    weekly_targets = volume_planner.compute_weekly_targets(
        phase_sequence, phase_driven=mesocycles is not None,
    )
    weekly_plan_with_vol = volume_planner.apply_volume_to_plan(weekly_plan, weekly_targets)
    zones_df = DanielsZones(vdot).build_dataframe()
    workouts = weekly_plan_to_workouts(weekly_plan_with_vol, athlete, zones_df)
    df_plan = workouts_to_dataframe(workouts)
    if mesocycles is not None:
        # Preserve explicit block boundaries, including adjacent equal phases.
        block_ids = []
        block_weeks = []
        for block_id, block in enumerate(blocks, start=1):
            block_ids.extend([block_id] * block.weeks)
            block_weeks.extend(range(1, block.weeks + 1))
        df_plan["mesocycle"] = df_plan["week"].map(dict(enumerate(block_ids, start=1)))
        df_plan["week_in_mesocycle"] = df_plan["week"].map(dict(enumerate(block_weeks, start=1)))
    return df_plan, vdot
