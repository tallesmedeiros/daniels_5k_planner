
from dataclasses import dataclass
from typing import List, Dict
from .athlete import AthleteConfig
from .sessions import SessionTemplate

@dataclass
class WeeklySessionSelector:
    athlete: AthleteConfig
    session_lib: Dict[str, List[SessionTemplate]]

    def __post_init__(self):
        self.phase_cursor: Dict[str, int] = {phase: 0 for phase in self.session_lib.keys()}

    def _num_quality_sessions(self, phase: str) -> int:
        f = self.athlete.frequency_per_week
        if phase == "Base":
            return 1 if f >= 5 else 0
        if phase == "EarlyQ":
            return 1
        if phase == "Threshold":
            return 2 if f >= 5 else 1
        if phase == "Interval":
            return 1 if f <= 3 else 2
        if phase == "Repetition":
            return 2 if f >= 5 else 1
        if phase == "RS":
            return 1
        if phase == "Taper":
            return 1 if f >= 5 else 0
        return 1

    def _training_days_for_frequency(self, f: int) -> List[int]:
        if f <= 0:
            return []
        if f == 1:
            return [3]
        if f == 2:
            return [3, 6]
        if f == 3:
            return [2, 4, 6]
        if f == 4:
            return [1, 3, 5, 7]
        if f == 5:
            return [1, 2, 4, 6, 7]
        if f == 6:
            return [1, 2, 3, 4, 5, 6]
        return [1, 2, 3, 4, 5, 6, 7]

    def _pick_quality_templates(self, phase: str, n_quality: int) -> List[SessionTemplate]:
        templates = self.session_lib.get(phase, [])
        if not templates or n_quality == 0:
            return []
        chosen = []
        idx = self.phase_cursor[phase]
        for _ in range(n_quality):
            t = templates[idx % len(templates)]
            chosen.append(t)
            idx += 1
        self.phase_cursor[phase] = idx
        return chosen

    def _pick_easy_templates(self, n_easy: int) -> List[SessionTemplate]:
        base_templates = [t for t in self.session_lib["Base"] if t.main_zones == ["E"]]
        if not base_templates:
            base_templates = self.session_lib["Base"]
        chosen = []
        idx = self.phase_cursor["Base"]
        for _ in range(n_easy):
            t = base_templates[idx % len(base_templates)]
            chosen.append(t)
            idx += 1
        self.phase_cursor["Base"] = idx
        return chosen

    def _schedule_week_days(self, quality_sessions, easy_sessions):
        f = self.athlete.frequency_per_week
        training_days = self._training_days_for_frequency(f)
        training_days = training_days[:f]
        day_map = {d: None for d in training_days}
        quality_preferred_days = [3, 5, 7, 2, 4, 6, 1]
        for sess in quality_sessions:
            assigned = False
            for d in quality_preferred_days:
                if d in day_map and day_map[d] is None:
                    day_map[d] = sess
                    assigned = True
                    break
            if not assigned:
                for d in training_days:
                    if day_map[d] is None:
                        day_map[d] = sess
                        assigned = True
                        break
        easy_iter = iter(easy_sessions)
        for d in training_days:
            if day_map[d] is None:
                try:
                    day_map[d] = next(easy_iter)
                except StopIteration:
                    break
        scheduled = []
        for d in sorted(training_days):
            sess = day_map[d]
            if sess is not None:
                scheduled.append({"day_of_week": d, "template": sess})
        return scheduled

    def build_weekly_plan(self, phase_sequence: List[str]) -> List[Dict]:
        plan = []
        week_number = 1
        for phase in phase_sequence:
            n_quality = self._num_quality_sessions(phase)
            n_total = self.athlete.frequency_per_week
            n_easy = max(0, n_total - n_quality)
            quality_sessions = self._pick_quality_templates(phase, n_quality)
            easy_sessions = self._pick_easy_templates(n_easy)
            scheduled_sessions = self._schedule_week_days(quality_sessions, easy_sessions)
            week_plan = {"week": week_number, "phase": phase, "sessions": scheduled_sessions}
            plan.append(week_plan)
            week_number += 1
        return plan
