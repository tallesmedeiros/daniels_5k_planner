
from typing import List, Dict
from .athlete import AthleteConfig

class WeeklyVolumePlanner:
    def __init__(self, athlete: AthleteConfig):
        self.athlete = athlete

    def _base_volume_curve(self, total_weeks: int) -> List[float]:
        V0 = self.athlete.initial_weekly_volume
        Vp = self.athlete.peak_weekly_volume
        W = total_weeks
        if W <= 1:
            return [V0]
        vols = []
        if W <= 3:
            for w in range(W):
                t = w / (W - 1)
                vols.append(V0 + (Vp - V0) * t)
            return vols
        for w in range(1, W - 2):
            t = (w - 1) / (W - 3)
            vols.append(V0 + (Vp - V0) * t)
        vols.append(0.90 * Vp)
        vols.append(0.80 * Vp)
        vols.append(0.60 * Vp)
        return vols

    def _phase_volume_factor(self, phase: str) -> float:
        phase_factors = {
            "Base": 1.00,
            "EarlyQ": 1.00,
            "Threshold": 1.00,
            "Interval": 0.95,
            "Repetition": 0.90,
            "RS": 0.90,
            "Taper": 0.70,
        }
        return phase_factors.get(phase, 1.00)

    def compute_weekly_targets(self, phase_sequence: List[str]) -> List[float]:
        W = len(phase_sequence)
        base_curve = self._base_volume_curve(W)
        targets = []
        for w, phase in enumerate(phase_sequence):
            Vw = base_curve[w]
            factor = self._phase_volume_factor(phase)
            targets.append(Vw * factor)
        return targets

    def apply_volume_to_plan(self, weekly_plan: List[Dict], weekly_targets: List[float]) -> List[Dict]:
        if len(weekly_plan) != len(weekly_targets):
            raise ValueError("weekly_plan e weekly_targets têm tamanhos diferentes.")
        new_plan = []
        for week_idx, week_data in enumerate(weekly_plan):
            target_vol = weekly_targets[week_idx]
            sessions = week_data["sessions"]
            base_sum = sum(s["template"].base_distance_km for s in sessions if s["template"].base_distance_km > 0)
            if base_sum <= 0:
                scaled_sessions = []
                for s in sessions:
                    s_new = dict(s)
                    s_new["planned_distance_km"] = s["template"].base_distance_km
                    scaled_sessions.append(s_new)
            else:
                scale = target_vol / base_sum
                scaled_sessions = []
                for s in sessions:
                    tpl = s["template"]
                    planned = tpl.base_distance_km * scale
                    s_new = dict(s)
                    s_new["planned_distance_km"] = planned
                    scaled_sessions.append(s_new)
            new_week_data = dict(week_data)
            new_week_data["sessions"] = scaled_sessions
            new_plan.append(new_week_data)
        return new_plan
