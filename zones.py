
import pandas as pd
import numpy as np

class DanielsZones:
    """
    Calculadora de zonas oficiais de Daniels (E/M/T/I/R) para um VDOT dado.
    Produz um DataFrame profissional com metadados.
    """

    def __init__(self, vdot: float):
        self.vdot = float(vdot)

        # Frações fisiológicas slow–fast (%VO2max)
        self.zone_fractions = {
            "E": (0.65, 0.78),
            "M": (0.83, 0.87),
            "T": (0.88, 0.92),
            "I": (0.97, 1.00),
            "R": (1.05, 1.10),
        }

        # Metadados
        self.zone_meta = {
            "E": ("Easy", "Aerobic endurance / recovery", 1),
            "M": ("Marathon", "Specific endurance / economy", 2),
            "T": ("Threshold", "Lactate steady-state", 3),
            "I": ("Interval", "VO2max development", 4),
            "R": ("Repetition", "Speed / neuromuscular", 5),
        }

    def _solve_velocity(self, vo2_target: float) -> float:
        a = 0.000104
        b = 0.182258
        c = -4.60 - vo2_target
        discriminant = b * b - 4 * a * c
        if discriminant < 0:
            raise ValueError("Discriminante negativo — verifique VDOT.")

        v1 = (-b + np.sqrt(discriminant)) / (2 * a)
        v2 = (-b - np.sqrt(discriminant)) / (2 * a)
        return float(max(v1, v2))

    def _pace_from_velocity(self, v_m_min: float) -> float:
        return 1000.0 / v_m_min

    def _compute_zone(self, frac_slow: float, frac_fast: float) -> dict:
        vo2_slow = frac_slow * self.vdot
        vo2_fast = frac_fast * self.vdot

        v_slow = self._solve_velocity(vo2_slow)
        v_fast = self._solve_velocity(vo2_fast)

        pace_slow = self._pace_from_velocity(v_slow)
        pace_fast = self._pace_from_velocity(v_fast)

        return {
            "vo2_slow": vo2_slow,
            "vo2_fast": vo2_fast,
            "v_slow_m_min": v_slow,
            "v_fast_m_min": v_fast,
            "pace_slow_min_km_raw": pace_slow,
            "pace_fast_min_km_raw": pace_fast,
        }

    def _format_pace(self, x: float) -> str:
        minutes = int(x)
        seconds = int(round((x - minutes) * 60))
        if seconds == 60:
            minutes += 1
            seconds = 0
        return f"{minutes:02d}:{seconds:02d}"

    def build_dataframe(self) -> pd.DataFrame:
        rows = []
        for zone, (frac_slow, frac_fast) in self.zone_fractions.items():
            long_name, description, priority = self.zone_meta[zone]
            calc = self._compute_zone(frac_slow, frac_fast)
            row = {
                "zone": zone,
                "long_name": long_name,
                "fraction_slow": frac_slow,
                "fraction_fast": frac_fast,
                "vo2_slow": calc["vo2_slow"],
                "vo2_fast": calc["vo2_fast"],
                "v_slow_m_min": calc["v_slow_m_min"],
                "v_fast_m_min": calc["v_fast_m_min"],
                "pace_slow_min_km_raw": calc["pace_slow_min_km_raw"],
                "pace_fast_min_km_raw": calc["pace_fast_min_km_raw"],
                "pace_slow_min_km_str": self._format_pace(calc["pace_slow_min_km_raw"]),
                "pace_fast_min_km_str": self._format_pace(calc["pace_fast_min_km_raw"]),
                "description": description,
                "intensity_level": priority,
                "priority": priority,
            }
            rows.append(row)
        df = pd.DataFrame(rows)
        df = df.sort_values("priority").reset_index(drop=True)
        return df

    def get_zone(self, zone: str) -> pd.Series:
        df = self.build_dataframe()
        return df[df["zone"] == zone].iloc[0]
