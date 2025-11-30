
from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict, Any

ZoneCode = Literal["E", "M", "T", "I", "R"]


@dataclass
class ContinuousSegment:
    distance_km: Optional[float] = None
    duration_min: Optional[float] = None
    zone: ZoneCode = "E"
    description: str = ""
    pace_slow_min_km: Optional[float] = None
    pace_fast_min_km: Optional[float] = None
    pace_slow_str: Optional[str] = None
    pace_fast_str: Optional[str] = None

    def __post_init__(self):
        if self.distance_km is None and self.duration_min is None:
            raise ValueError("ContinuousSegment: defina distance_km OU duration_min.")


@dataclass
class IntervalBlock:
    reps: int
    work_distance_m: Optional[float] = None
    work_duration_min: Optional[float] = None
    work_zone: ZoneCode = "I"
    recovery_distance_m: Optional[float] = None
    recovery_duration_min: Optional[float] = None
    recovery_zone: ZoneCode = "E"
    description: str = ""
    work_pace_slow_min_km: Optional[float] = None
    work_pace_fast_min_km: Optional[float] = None
    work_pace_slow_str: Optional[str] = None
    work_pace_fast_str: Optional[str] = None
    rec_pace_slow_min_km: Optional[float] = None
    rec_pace_fast_min_km: Optional[float] = None
    rec_pace_slow_str: Optional[str] = None
    rec_pace_fast_str: Optional[str] = None

    def __post_init__(self):
        if self.work_distance_m is None and self.work_duration_min is None:
            raise ValueError("IntervalBlock: defina work_distance_m OU work_duration_min.")
        if self.recovery_distance_m is None and self.recovery_duration_min is None:
            raise ValueError("IntervalBlock: defina recovery_distance_m OU recovery_duration_min.")


@dataclass
class SessionTemplate:
    code: str
    name: str
    phase: str
    main_zones: List[ZoneCode]
    tags: List[str] = field(default_factory=list)
    warmup: List[ContinuousSegment] = field(default_factory=list)
    main: List[object] = field(default_factory=list)
    cooldown: List[ContinuousSegment] = field(default_factory=list)
    base_distance_km: float = 0.0
    description: str = ""


@dataclass
class Workout:
    athlete_name: str
    week: int
    day_of_week: int
    weekday_name: str
    phase: str
    session_code: str
    session_name: str
    main_zones: List[ZoneCode]
    is_quality: bool
    planned_distance_km: float
    description: str


def build_5k_session_library() -> Dict[str, List[SessionTemplate]]:
    lib: Dict[str, List[SessionTemplate]] = {
        "Base": [],
        "EarlyQ": [],
        "Threshold": [],
        "Interval": [],
        "Repetition": [],
        "RS": [],
        "Taper": [],
    }

    # Base
    lib["Base"].append(
        SessionTemplate(
            code="BASE_EASY_40",
            name="Easy Run 40'",
            phase="Base",
            main_zones=["E"],
            warmup=[ContinuousSegment(duration_min=10, zone="E", description="Easy")],
            main=[ContinuousSegment(duration_min=20, zone="E", description="Easy contínuo")],
            cooldown=[ContinuousSegment(duration_min=10, zone="E", description="Easy leve")],
            base_distance_km=8.0,
            description="Corrida contínua fácil de ~40 minutos.",
        )
    )
    lib["Base"].append(
        SessionTemplate(
            code="BASE_EASY_60",
            name="Easy Long 60'",
            phase="Base",
            main_zones=["E"],
            warmup=[ContinuousSegment(duration_min=10, zone="E")],
            main=[ContinuousSegment(duration_min=40, zone="E")],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=12.0,
            description="Corrida contínua fácil (~60') para desenvolvimento aeróbio.",
        )
    )
    lib["Base"].append(
        SessionTemplate(
            code="BASE_EASY_STRIDES",
            name="Easy + Strides",
            phase="Base",
            main_zones=["E", "R"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=[
                ContinuousSegment(duration_min=20, zone="E", description="Parte contínua em E"),
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=8.5,
            description="Easy com strides curtas para introduzir velocidade de forma leve.",
        )
    )

    # EarlyQ
    lib["EarlyQ"].append(
        SessionTemplate(
            code="EQ_PROGRESSIVE_40",
            name="Progressivo 40' (E → T leve)",
            phase="EarlyQ",
            main_zones=["E", "T"],
            warmup=[ContinuousSegment(duration_min=10, zone="E")],
            main=[
                ContinuousSegment(duration_min=15, zone="E", description="Parte inicial em E"),
                ContinuousSegment(duration_min=10, zone="T", description="Final leve em T"),
            ],
            cooldown=[ContinuousSegment(duration_min=5, zone="E")],
            base_distance_km=9.0,
            description="Corrida progressiva terminando em T leve.",
        )
    )

    # Threshold
    lib["Threshold"].append(
        SessionTemplate(
            code="T_TEMPO_20",
            name="Tempo Run 20'",
            phase="Threshold",
            main_zones=["T"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=[ContinuousSegment(duration_min=20, zone="T", description="Tempo contínuo")],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=10.0,
            description="Tempo contínuo ~20' no ritmo T.",
        )
    )
    lib["Threshold"].append(
        SessionTemplate(
            code="T_CRUISE_4x5",
            name="4 x 5' @ T",
            phase="Threshold",
            main_zones=["T"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=[
                IntervalBlock(
                    reps=4,
                    work_duration_min=5.0,
                    work_zone="T",
                    recovery_duration_min=1.0,
                    recovery_zone="E",
                    description="Cruise intervals em T",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=11.0,
            description="Cruise intervals: 4x5' @ T com 1' E.",
        )
    )

    # Interval
    lib["Interval"].append(
        SessionTemplate(
            code="I_5x1000",
            name="5 x 1000m @ I",
            phase="Interval",
            main_zones=["I"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=[
                IntervalBlock(
                    reps=5,
                    work_distance_m=1000,
                    work_zone="I",
                    recovery_distance_m=400,
                    recovery_zone="E",
                    description="Clássico 5x1000m @ I",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=11.0,
            description="Sessão clássica de VO2max para 5K.",
        )
    )
    lib["Interval"].append(
        SessionTemplate(
            code="I_6x800",
            name="6 x 800m @ I",
            phase="Interval",
            main_zones=["I"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=[
                IntervalBlock(
                    reps=6,
                    work_distance_m=800,
                    work_zone="I",
                    recovery_distance_m=400,
                    recovery_zone="E",
                    description="6x800m @ I",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=11.0,
            description="Alternativa ao 5x1000m @ I.",
        )
    )

    # Repetition
    lib["Repetition"].append(
        SessionTemplate(
            code="R_10x200",
            name="10 x 200m @ R",
            phase="Repetition",
            main_zones=["R"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=[
                IntervalBlock(
                    reps=10,
                    work_distance_m=200,
                    work_zone="R",
                    recovery_distance_m=200,
                    recovery_zone="E",
                    description="10x200m @ R",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=8.0,
            description="Sessão de velocidade/neuromuscular.",
        )
    )
    lib["Repetition"].append(
        SessionTemplate(
            code="R_8x300",
            name="8 x 300m @ R",
            phase="Repetition",
            main_zones=["R"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=[
                IntervalBlock(
                    reps=8,
                    work_distance_m=300,
                    work_zone="R",
                    recovery_distance_m=200,
                    recovery_zone="E",
                    description="8x300m @ R",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=8.5,
            description="Repetições um pouco mais longas em R.",
        )
    )

    # RS
    lib["RS"].append(
        SessionTemplate(
            code="RS_3x1600",
            name="3 x 1600m (entre T e I)",
            phase="RS",
            main_zones=["T", "I"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=[
                IntervalBlock(
                    reps=3,
                    work_distance_m=1600,
                    work_zone="T",
                    recovery_duration_min=3.0,
                    recovery_zone="E",
                    description="3x1600m em ritmo entre T e I",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=10.0,
            description="Sessão específica aproximando ritmo de prova.",
        )
    )
    lib["RS"].append(
        SessionTemplate(
            code="RS_5K_SIM",
            name="Simulado de 5K",
            phase="RS",
            main_zones=["T", "I", "R"],
            warmup=[ContinuousSegment(duration_min=20, zone="E")],
            main=[ContinuousSegment(distance_km=5.0, zone="I", description="5K race-pace / time trial")],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=10.0,
            description="Simulado de 5K (time trial).",
        )
    )

    # Taper
    lib["Taper"].append(
        SessionTemplate(
            code="TP_EASY_30",
            name="Easy 30' + 4x20\" strides",
            phase="Taper",
            main_zones=["E", "R"],
            warmup=[ContinuousSegment(duration_min=10, zone="E")],
            main=[ContinuousSegment(duration_min=20, zone="E", description="Easy")],
            cooldown=[ContinuousSegment(duration_min=5, zone="E")],
            base_distance_km=6.0,
            description="Manter leveza, incluir alguns strides curtos.",
        )
    )
    lib["Taper"].append(
        SessionTemplate(
            code="TP_2x1K",
            name="2 x 1000m leve @ I",
            phase="Taper",
            main_zones=["I"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=[
                IntervalBlock(
                    reps=2,
                    work_distance_m=1000,
                    work_zone="I",
                    recovery_duration_min=3.0,
                    recovery_zone="E",
                    description="2x1000m apenas para manter sensação de ritmo.",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=8.0,
            description="Touch de I em volume bem reduzido.",
        )
    )

    return lib
