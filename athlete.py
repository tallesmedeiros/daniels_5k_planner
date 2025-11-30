
from dataclasses import dataclass

@dataclass
class AthleteConfig:
    name: str
    frequency_per_week: int
    objective: str = "5K"
    initial_weekly_volume: float = 30.0  # km
    peak_weekly_volume: float = 50.0     # km
