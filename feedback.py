
from dataclasses import dataclass
from typing import Optional, List
from .athlete import AthleteConfig

@dataclass
class CompletedWorkoutFeedback:
    week: int
    day_of_week: int
    completed_distance_km: Optional[float] = None
    rpe: Optional[int] = None
    notes: str = ""

@dataclass
class WeeklyFeedback:
    week: int
    planned_volume_km: float
    completed_volume_km: float
    missed_workouts: int
    avg_rpe_quality: Optional[float] = None
    fatigue_score: Optional[int] = None
    soreness_score: Optional[int] = None
    notes: str = ""

@dataclass
class FeedbackAdjustment:
    week: int
    volume_factor: float
    quality_bias: float
    comment: str = ""

class FeedbackEngine:
    def __init__(self, athlete: AthleteConfig):
        self.athlete = athlete

    def compute_adjustment_from_week(self, fb: WeeklyFeedback) -> FeedbackAdjustment:
        A = fb.completed_volume_km / max(fb.planned_volume_km, 1e-3)
        fatigue = fb.fatigue_score if fb.fatigue_score is not None else 5
        soreness = fb.soreness_score if fb.soreness_score is not None else 5
        volume_factor = 1.0
        quality_bias = 1.0
        comment = []

        if A < 0.6 or fatigue >= 8 or soreness >= 8:
            volume_factor = 0.8
            quality_bias = 0.7
            comment.append("Redução forte por baixa adesão ou fadiga/dor alta.")
        elif A < 0.9 or fatigue >= 7:
            volume_factor = 0.9
            quality_bias = 0.85
            comment.append("Redução moderada de volume e qualidade.")
        elif 0.9 <= A <= 1.1 and fatigue <= 6 and soreness <= 6:
            volume_factor = 1.0
            quality_bias = 1.0
            comment.append("Manter progressão planejada.")
        elif A > 1.1 and fatigue <= 5 and soreness <= 5:
            volume_factor = 1.05
            quality_bias = 1.05
            comment.append("Atleta suportando bem — leve aumento permitido.")
        else:
            comment.append("Situação intermediária — manter plano.")
            volume_factor = 1.0
            quality_bias = 1.0

        return FeedbackAdjustment(
            week=fb.week,
            volume_factor=volume_factor,
            quality_bias=quality_bias,
            comment=" ".join(comment),
        )

    def apply_adjustment_to_targets(self, weekly_targets: List[float], adjustment: FeedbackAdjustment, from_week_exclusive: int) -> List[float]:
        new_targets = []
        for w_idx, Vw in enumerate(weekly_targets, start=1):
            if w_idx > from_week_exclusive:
                new_targets.append(Vw * adjustment.volume_factor)
            else:
                new_targets.append(Vw)
        return new_targets
