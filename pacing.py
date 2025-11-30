
from typing import Dict, Any, List
import pandas as pd
from .sessions import ContinuousSegment, IntervalBlock, SessionTemplate, Workout
from .athlete import AthleteConfig


class WorkoutPaceAnnotator:
    def __init__(self, zones_df: pd.DataFrame):
        self.zones_df = zones_df.set_index("zone")

    def _get_zone_paces(self, zone: str) -> Dict[str, Any]:
        row = self.zones_df.loc[zone]
        return {
            "slow_raw": row["pace_slow_min_km_raw"],
            "fast_raw": row["pace_fast_min_km_raw"],
            "slow_str": row["pace_slow_min_km_str"],
            "fast_str": row["pace_fast_min_km_str"],
        }

    def annotate_continuous(self, seg: ContinuousSegment) -> ContinuousSegment:
        p = self._get_zone_paces(seg.zone)
        seg.pace_slow_min_km = p["slow_raw"]
        seg.pace_fast_min_km = p["fast_raw"]
        seg.pace_slow_str = p["slow_str"]
        seg.pace_fast_str = p["fast_str"]
        return seg

    def annotate_interval_block(self, block: IntervalBlock) -> IntervalBlock:
        p_work = self._get_zone_paces(block.work_zone)
        block.work_pace_slow_min_km = p_work["slow_raw"]
        block.work_pace_fast_min_km = p_work["fast_raw"]
        block.work_pace_slow_str = p_work["slow_str"]
        block.work_pace_fast_str = p_work["fast_str"]
        p_rec = self._get_zone_paces(block.recovery_zone)
        block.rec_pace_slow_min_km = p_rec["slow_raw"]
        block.rec_pace_fast_min_km = p_rec["fast_raw"]
        block.rec_pace_slow_str = p_rec["slow_str"]
        block.rec_pace_fast_str = p_rec["fast_str"]
        return block

    def annotate_session(self, template: SessionTemplate) -> SessionTemplate:
        for seg in template.warmup:
            if isinstance(seg, ContinuousSegment):
                self.annotate_continuous(seg)
        for item in template.main:
            if isinstance(item, ContinuousSegment):
                self.annotate_continuous(item)
            elif isinstance(item, IntervalBlock):
                self.annotate_interval_block(item)
        for seg in template.cooldown:
            if isinstance(seg, ContinuousSegment):
                self.annotate_continuous(seg)
        return template

    def describe_session(self, template: SessionTemplate) -> str:
        lines = [f"{template.name} ({template.phase})"]
        if template.warmup:
            lines.append("  Aquecimento:")
            for seg in template.warmup:
                if seg.distance_km is not None:
                    lines.append(
                        f"    - {seg.distance_km:.1f} km @ {seg.pace_slow_str}–{seg.pace_fast_str} ({seg.zone})"
                    )
                else:
                    lines.append(
                        f"    - {seg.duration_min:.0f} min @ {seg.pace_slow_str}–{seg.pace_fast_str} ({seg.zone})"
                    )
        if template.main:
            lines.append("  Parte principal:")
            for item in template.main:
                if isinstance(item, ContinuousSegment):
                    if item.distance_km is not None:
                        lines.append(
                            f"    - {item.distance_km:.1f} km @ {item.pace_slow_str}–{item.pace_fast_str} ({item.zone})"
                        )
                    else:
                        lines.append(
                            f"    - {item.duration_min:.0f} min @ {item.pace_slow_str}–{item.pace_fast_str} ({item.zone})"
                        )
                elif isinstance(item, IntervalBlock):
                    rep_str = []
                    if item.work_distance_m is not None:
                        rep_str.append(f"{item.work_distance_m:.0f} m")
                    else:
                        rep_str.append(f"{item.work_duration_min:.0f} min")
                    rep_str.append(f"@ {item.work_pace_slow_str}–{item.work_pace_fast_str} ({item.work_zone})")
                    rec_str = []
                    if item.recovery_distance_m is not None:
                        rec_str.append(f"{item.recovery_distance_m:.0f} m")
                    else:
                        rec_str.append(f"{item.recovery_duration_min:.0f} min")
                    rec_str.append(f"@ {item.rec_pace_slow_str}–{item.rec_pace_fast_str} ({item.recovery_zone})")
                    lines.append(
                        f"    - {item.reps} x {' '.join(rep_str)} rec {' '.join(rec_str)}"
                    )
        if template.cooldown:
            lines.append("  Desaquecimento:")
            for seg in template.cooldown:
                if seg.distance_km is not None:
                    lines.append(
                        f"    - {seg.distance_km:.1f} km @ {seg.pace_slow_str}–{seg.pace_fast_str} ({seg.zone})"
                    )
                else:
                    lines.append(
                        f"    - {seg.duration_min:.0f} min @ {seg.pace_slow_str}–{seg.pace_fast_str} ({seg.zone})"
                    )
        return "\n".join(lines)


def weekday_name_from_int(d: int) -> str:
    mapping = {1: "Seg", 2: "Ter", 3: "Qua", 4: "Qui", 5: "Sex", 6: "Sáb", 7: "Dom"}
    return mapping.get(d, f"Dia{d}")


def weekly_plan_to_workouts(weekly_plan_with_vol: List[dict], athlete: AthleteConfig, zones_df: pd.DataFrame) -> List[Workout]:
    annotator = WorkoutPaceAnnotator(zones_df)
    workouts: List[Workout] = []
    for week_data in weekly_plan_with_vol:
        week = week_data["week"]
        phase = week_data["phase"]
        for s in week_data["sessions"]:
            day = s["day_of_week"]
            tpl = s["template"]
            planned_dist = s["planned_distance_km"]
            annotator.annotate_session(tpl)
            desc = annotator.describe_session(tpl)
            is_quality = any(z in ("T", "I", "R") for z in tpl.main_zones)
            weekday_name = weekday_name_from_int(day)
            w = Workout(
                athlete_name=athlete.name,
                week=week,
                day_of_week=day,
                weekday_name=weekday_name,
                phase=phase,
                session_code=tpl.code,
                session_name=tpl.name,
                main_zones=tpl.main_zones,
                is_quality=is_quality,
                planned_distance_km=planned_dist,
                description=desc,
            )
            workouts.append(w)
    return workouts


def workouts_to_dataframe(workouts: List[Workout]) -> pd.DataFrame:
    rows = []
    for w in workouts:
        rows.append({
            "athlete": w.athlete_name,
            "week": w.week,
            "day_of_week": w.day_of_week,
            "weekday": w.weekday_name,
            "phase": w.phase,
            "session_code": w.session_code,
            "session_name": w.session_name,
            "main_zones": "/".join(w.main_zones),
            "is_quality": w.is_quality,
            "planned_distance_km": w.planned_distance_km,
            "description": w.description,
        })
    df = pd.DataFrame(rows)
    df = df.sort_values(["week", "day_of_week"]).reset_index(drop=True)
    cols = [
        "athlete", "week", "day_of_week", "weekday", "phase",
        "session_code", "session_name", "main_zones", "is_quality",
        "planned_distance_km", "description",
    ]
    return df[cols]
