
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


PACE_KM_PER_MIN = {"E": 1 / 6.0, "M": 1 / 5.4, "T": 1 / 4.25, "I": 1 / 3.75, "R": 1 / 3.5}


def _estimate_segment_distance_km(segment: object) -> float:
    if isinstance(segment, ContinuousSegment):
        if segment.distance_km is not None:
            return segment.distance_km
        pace = PACE_KM_PER_MIN.get(segment.zone, PACE_KM_PER_MIN["E"])
        return (segment.duration_min or 0) * pace
    if isinstance(segment, IntervalBlock):
        work_distance = (
            segment.work_distance_m / 1000.0
            if segment.work_distance_m is not None
            else (segment.work_duration_min or 0) * PACE_KM_PER_MIN.get(segment.work_zone, PACE_KM_PER_MIN["E"])
        )
        recovery_distance = (
            segment.recovery_distance_m / 1000.0
            if segment.recovery_distance_m is not None
            else (segment.recovery_duration_min or 0) * PACE_KM_PER_MIN.get(segment.recovery_zone, PACE_KM_PER_MIN["E"])
        )
        return segment.reps * (work_distance + recovery_distance)
    return 0.0


def _estimate_session_distance_km(parts: List[List[object]]) -> float:
    distance = sum(_estimate_segment_distance_km(seg) for part in parts for seg in part)
    return round(distance, 1)


def _build_template(
    *,
    code: str,
    name: str,
    phase: str,
    main_zones: List[ZoneCode],
    warmup: List[ContinuousSegment],
    main: List[object],
    cooldown: List[ContinuousSegment],
    description: str,
) -> SessionTemplate:
    base_distance = _estimate_session_distance_km([warmup, main, cooldown])
    return SessionTemplate(
        code=code,
        name=name,
        phase=phase,
        main_zones=main_zones,
        warmup=warmup,
        main=main,
        cooldown=cooldown,
        base_distance_km=base_distance,
        description=description,
    )


def _build_threshold_sessions() -> List[SessionTemplate]:
    sessions: List[SessionTemplate] = []

    def add(**kwargs: Any):
        sessions.append(_build_template(**kwargs))

    # Sessões base existentes
    add(
        code="T_TEMPO_20",
        name="Tempo Run 20'",
        phase="Threshold",
        main_zones=["T"],
        warmup=[ContinuousSegment(duration_min=15, zone="E")],
        main=[ContinuousSegment(duration_min=20, zone="T", description="Tempo contínuo")],
        cooldown=[ContinuousSegment(duration_min=10, zone="E")],
        description="Tempo contínuo ~20' no ritmo T.",
    )
    add(
        code="T_3x8",
        name="3 x 8' @ T",
        phase="Threshold",
        main_zones=["T"],
        warmup=[ContinuousSegment(duration_min=15, zone="E")],
        main=[
            IntervalBlock(
                reps=3,
                work_duration_min=8.0,
                work_zone="T",
                recovery_duration_min=2.0,
                recovery_zone="E",
                description="3 blocos de limiar sustentado",
            )
        ],
        cooldown=[ContinuousSegment(duration_min=10, zone="E")],
        description="Intervalos de limiar mais longos para consolidar o ritmo T.",
    )
    add(
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
        description="Cruise intervals: 4x5' @ T com 1' E.",
    )
    add(
        code="T_5x6",
        name="5 x 6' @ T",
        phase="Threshold",
        main_zones=["T"],
        warmup=[ContinuousSegment(duration_min=15, zone="E")],
        main=[
            IntervalBlock(
                reps=5,
                work_duration_min=6.0,
                work_zone="T",
                recovery_duration_min=1.5,
                recovery_zone="E",
                description="Cruise intervals de 6'",
            )
        ],
        cooldown=[ContinuousSegment(duration_min=10, zone="E")],
        description="Maior volume em T para elevar capacidade no ritmo de prova.",
    )
    add(
        code="T_TEMPO_FINISH",
        name="Tempo 25' + final controlado",
        phase="Threshold",
        main_zones=["T", "I"],
        warmup=[ContinuousSegment(duration_min=15, zone="E")],
        main=[
            ContinuousSegment(duration_min=20, zone="T", description="Tempo contínuo"),
            IntervalBlock(
                reps=4,
                work_duration_min=0.5,
                work_zone="I",
                recovery_duration_min=1.0,
                recovery_zone="E",
                description="Acelerações curtas para facilitar transição a treinos I",
            ),
        ],
        cooldown=[ContinuousSegment(duration_min=10, zone="E")],
        description="Tempo prolongado seguido de toques rápidos para reforço neuromuscular.",
    )

    # Tempos contínuos adicionais
    for duration in [16, 18, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44]:
        add(
            code=f"T_TEMPO_{duration}",
            name=f"Tempo Run {duration}'",
            phase="Threshold",
            main_zones=["T"],
            warmup=[ContinuousSegment(duration_min=12, zone="E")],
            main=[ContinuousSegment(duration_min=duration, zone="T", description="Tempo contínuo controlado")],
            cooldown=[ContinuousSegment(duration_min=8, zone="E")],
            description="Tempo contínuo para sustentar ritmo de limiar.",
        )

    # Cruise intervals variados
    cruise_presets = [
        (4, 6.0, 1.5),
        (5, 6.0, 1.0),
        (6, 5.0, 1.0),
        (7, 4.0, 1.0),
        (8, 3.5, 1.0),
        (5, 7.0, 1.5),
        (3, 10.0, 2.0),
        (4, 9.0, 2.0),
        (6, 4.5, 1.0),
        (7, 5.0, 1.5),
        (8, 3.0, 1.0),
        (5, 8.0, 1.5),
        (4, 12.0, 2.0),
    ]

    for reps, work_min, rec_min in cruise_presets:
        add(
            code=f"T_CRUISE_{reps}x{int(work_min)}",
            name=f"{reps} x {work_min:.0f}' @ T",
            phase="Threshold",
            main_zones=["T"],
            warmup=[ContinuousSegment(duration_min=14, zone="E")],
            main=[
                IntervalBlock(
                    reps=reps,
                    work_duration_min=work_min,
                    work_zone="T",
                    recovery_duration_min=rec_min,
                    recovery_zone="E",
                    description="Cruise intervals em ritmo de limiar",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            description="Séries de limiar com recuperações curtas para acumular tempo de qualidade.",
        )

    # Blocos progressivos e mistos
    progressive_blocks = [
        ("T_PROGRESSIVE_40", [ContinuousSegment(duration_min=15, zone="E"), ContinuousSegment(duration_min=10, zone="T"), ContinuousSegment(duration_min=5, zone="I")]),
        ("T_PROGRESSIVE_45", [ContinuousSegment(duration_min=15, zone="E"), ContinuousSegment(duration_min=15, zone="T"), ContinuousSegment(duration_min=5, zone="I")]),
        ("T_PROGRESSIVE_50", [ContinuousSegment(duration_min=15, zone="E"), ContinuousSegment(duration_min=20, zone="T"), ContinuousSegment(duration_min=5, zone="I")]),
        ("T_E_FLT_6x6", [IntervalBlock(reps=6, work_duration_min=6.0, work_zone="T", recovery_duration_min=2.0, recovery_zone="E", description="Flutuantes T/E")]),
        ("T_E_FLT_5x8", [IntervalBlock(reps=5, work_duration_min=8.0, work_zone="T", recovery_duration_min=2.0, recovery_zone="E", description="Flutuantes T/E longos")]),
        ("T_ALT_20_30", [ContinuousSegment(duration_min=10, zone="T"), ContinuousSegment(duration_min=10, zone="E"), ContinuousSegment(duration_min=10, zone="T")]),
        ("T_ALT_15_45", [ContinuousSegment(duration_min=15, zone="T"), ContinuousSegment(duration_min=15, zone="E"), ContinuousSegment(duration_min=15, zone="T")]),
        ("T_FINISH_STRIDES", [ContinuousSegment(duration_min=25, zone="T"), IntervalBlock(reps=6, work_duration_min=0.33, work_zone="R", recovery_duration_min=1.0, recovery_zone="E", description="Strides pós-tempo")]),
        ("T_SANDWICH_3x10", [ContinuousSegment(duration_min=10, zone="T"), ContinuousSegment(duration_min=10, zone="E"), ContinuousSegment(duration_min=10, zone="T")]),
        ("T_LONG_FINISH", [ContinuousSegment(duration_min=30, zone="T"), ContinuousSegment(duration_min=10, zone="E"), ContinuousSegment(duration_min=5, zone="T")]),
        ("T_PROGRESSIVE_HILL", [ContinuousSegment(duration_min=15, zone="E"), IntervalBlock(reps=6, work_duration_min=0.5, work_zone="I", recovery_duration_min=1.0, recovery_zone="E", description="Subida leve"), ContinuousSegment(duration_min=18, zone="T")]),
        ("T_CRESCENDO_4x7", [IntervalBlock(reps=4, work_duration_min=7.0, work_zone="T", recovery_duration_min=1.5, recovery_zone="E", description="Aumentar levemente o ritmo a cada bloco")]),
    ]

    for code, main_blocks in progressive_blocks:
        add(
            code=code,
            name=code.replace("_", " "),
            phase="Threshold",
            main_zones=["T"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=main_blocks,
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            description="Variação de limiar com blocos progressivos ou mistos.",
        )

    # Sessões de tempo combinado com ritmo moderado
    combo_sets = [
        ("T_COMBO_2x15", 2, 15, 3),
        ("T_COMBO_3x12", 3, 12, 2),
        ("T_COMBO_4x10", 4, 10, 2),
        ("T_COMBO_6x8", 6, 8, 1.5),
        ("T_COMBO_8x6", 8, 6, 1.0),
        ("T_COMBO_10x5", 10, 5, 1.0),
    ]

    for code, reps, work, rec in combo_sets:
        add(
            code=code,
            name=f"{reps} x {work}' @ T (rec {rec}')",
            phase="Threshold",
            main_zones=["T"],
            warmup=[ContinuousSegment(duration_min=12, zone="E")],
            main=[
                IntervalBlock(
                    reps=reps,
                    work_duration_min=float(work),
                    work_zone="T",
                    recovery_duration_min=float(rec),
                    recovery_zone="E",
                    description="Cruise controlados",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=8, zone="E")],
            description="Acúmulo alto de tempo em T com recuperações breves.",
        )

    assert len(sessions) == 50, f"Threshold sessions esperadas: 50, encontradas {len(sessions)}"
    return sessions


def _build_interval_sessions() -> List[SessionTemplate]:
    sessions: List[SessionTemplate] = []

    def add(**kwargs: Any):
        sessions.append(_build_template(**kwargs))

    # Sessões base existentes
    add(
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
        description="Sessão clássica de VO2max para 5K.",
    )
    add(
        code="I_5x1200",
        name="5 x 1200m @ I",
        phase="Interval",
        main_zones=["I"],
        warmup=[ContinuousSegment(duration_min=15, zone="E")],
        main=[
            IntervalBlock(
                reps=5,
                work_distance_m=1200,
                work_zone="I",
                recovery_distance_m=400,
                recovery_zone="E",
                description="Intervalos levemente mais longos para VO2max",
            )
        ],
        cooldown=[ContinuousSegment(duration_min=10, zone="E")],
        description="Aumenta o tempo total em I mantendo recuperações curtas.",
    )
    add(
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
        description="Alternativa ao 5x1000m @ I.",
    )
    add(
        code="I_3x1600",
        name="3 x 1600m @ I",
        phase="Interval",
        main_zones=["I"],
        warmup=[ContinuousSegment(duration_min=15, zone="E")],
        main=[
            IntervalBlock(
                reps=3,
                work_distance_m=1600,
                work_zone="I",
                recovery_duration_min=3.0,
                recovery_zone="E",
                description="Blocos longos para maximizar tempo em VO2",
            )
        ],
        cooldown=[ContinuousSegment(duration_min=10, zone="E")],
        description="Três repetições longas para maturar ritmo de 5K.",
    )
    add(
        code="I_PYRAMID",
        name="Pirâmide 400-800-1200-800-400 @ I",
        phase="Interval",
        main_zones=["I"],
        warmup=[ContinuousSegment(duration_min=15, zone="E")],
        main=[
            IntervalBlock(reps=1, work_distance_m=400, work_zone="I", recovery_distance_m=200, recovery_zone="E", description="Início da pirâmide"),
            IntervalBlock(reps=1, work_distance_m=800, work_zone="I", recovery_distance_m=200, recovery_zone="E", description="Subida"),
            IntervalBlock(reps=1, work_distance_m=1200, work_zone="I", recovery_distance_m=200, recovery_zone="E", description="Pico da pirâmide"),
            IntervalBlock(reps=1, work_distance_m=800, work_zone="I", recovery_distance_m=200, recovery_zone="E", description="Descida"),
            IntervalBlock(reps=1, work_distance_m=400, work_zone="I", recovery_distance_m=200, recovery_zone="E", description="Fechamento"),
        ],
        cooldown=[ContinuousSegment(duration_min=10, zone="E")],
        description="Pirâmide progressiva para variar cadência mantendo estímulo de VO2max.",
    )

    # Séries padronizadas por distância
    distance_sets = [
        ("I_8x400", 8, 400, 200),
        ("I_10x400", 10, 400, 200),
        ("I_12x400", 12, 400, 200),
        ("I_6x600", 6, 600, 300),
        ("I_8x600", 8, 600, 300),
        ("I_10x600", 10, 600, 300),
        ("I_7x800", 7, 800, 300),
        ("I_8x800", 8, 800, 300),
        ("I_10x800", 10, 800, 300),
        ("I_6x1000", 6, 1000, 300),
        ("I_7x1000", 7, 1000, 400),
        ("I_8x1000", 8, 1000, 400),
        ("I_4x1200", 4, 1200, 400),
        ("I_6x1200", 6, 1200, 400),
        ("I_4x1400", 4, 1400, 400),
        ("I_5x1400", 5, 1400, 400),
        ("I_4x1600", 4, 1600, 400),
        ("I_5x1600", 5, 1600, 400),
        ("I_3x2000", 3, 2000, 600),
    ]

    for code, reps, dist, rec in distance_sets:
        add(
            code=code,
            name=f"{reps} x {dist}m @ I",
            phase="Interval",
            main_zones=["I"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=[
                IntervalBlock(
                    reps=reps,
                    work_distance_m=dist,
                    work_zone="I",
                    recovery_distance_m=rec,
                    recovery_zone="E",
                    description="Séries clássicas de VO2max",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            description="Variações de volume para treinar ritmo I com recuperações controladas.",
        )

    extra_distance_sets = [
        ("I_5x1000_LONGREC", 5, 1000, 600),
        ("I_4x1200_LONGREC", 4, 1200, 600),
        ("I_6x800_FASTREC", 6, 800, 200),
        ("I_8x500", 8, 500, 250),
        ("I_10x500", 10, 500, 300),
        ("I_12x500", 12, 500, 300),
        ("I_6x700", 6, 700, 300),
        ("I_8x700", 8, 700, 300),
        ("I_5x1100", 5, 1100, 350),
        ("I_6x1100", 6, 1100, 350),
        ("I_7x900", 7, 900, 300),
        ("I_8x900", 8, 900, 300),
        ("I_3x2000_PROGRESSIVE", 3, 2000, 800),
        ("I_2x2400", 2, 2400, 600),
    ]

    for code, reps, dist, rec in extra_distance_sets:
        add(
            code=code,
            name=f"{reps} x {dist}m @ I",
            phase="Interval",
            main_zones=["I"],
            warmup=[ContinuousSegment(duration_min=16, zone="E")],
            main=[
                IntervalBlock(
                    reps=reps,
                    work_distance_m=dist,
                    work_zone="I",
                    recovery_distance_m=rec,
                    recovery_zone="E",
                    description="Variação de distância mantendo ritmo I",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            description="Ajuste de volume e recuperação para diferentes necessidades.",
        )

    # Séries por tempo em I
    timed_sets = [
        ("I_8x3min", 8, 3.0, 2.0),
        ("I_6x4min", 6, 4.0, 2.0),
        ("I_5x5min", 5, 5.0, 2.5),
        ("I_4x6min", 4, 6.0, 3.0),
        ("I_10x2min", 10, 2.0, 1.5),
        ("I_12x90s", 12, 1.5, 1.5),
        ("I_15x1min", 15, 1.0, 1.0),
        ("I_20x45s", 20, 0.75, 0.75),
    ]

    for code, reps, work, rec in timed_sets:
        add(
            code=code,
            name=f"{reps} x {work * 60:.0f}s @ I",
            phase="Interval",
            main_zones=["I"],
            warmup=[ContinuousSegment(duration_min=12, zone="E")],
            main=[
                IntervalBlock(
                    reps=reps,
                    work_duration_min=work,
                    work_zone="I",
                    recovery_duration_min=rec,
                    recovery_zone="E",
                    description="Blocos cronometrados de VO2max",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=8, zone="E")],
            description="Controle de ritmo por tempo para foco no estímulo fisiológico.",
        )

    # Combinações piramidais e mistas
    mixed_sets = [
        ("I_MIX_400_800", [IntervalBlock(reps=4, work_distance_m=400, work_zone="I", recovery_distance_m=200, recovery_zone="E", description="Abertura"), IntervalBlock(reps=3, work_distance_m=800, work_zone="I", recovery_distance_m=300, recovery_zone="E", description="Meio"), IntervalBlock(reps=4, work_distance_m=400, work_zone="I", recovery_distance_m=200, recovery_zone="E", description="Fecho")]),
        ("I_MIX_600_1000", [IntervalBlock(reps=3, work_distance_m=600, work_zone="I", recovery_distance_m=300, recovery_zone="E", description="Aquecimento específico"), IntervalBlock(reps=4, work_distance_m=1000, work_zone="I", recovery_distance_m=400, recovery_zone="E", description="Miolo"), IntervalBlock(reps=3, work_distance_m=600, work_zone="I", recovery_distance_m=300, recovery_zone="E", description="Fecho")]),
        ("I_PROGRESSIVE_400_1600", [IntervalBlock(reps=1, work_distance_m=400, work_zone="I", recovery_distance_m=200, recovery_zone="E", description="Ramp up"), IntervalBlock(reps=1, work_distance_m=800, work_zone="I", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=1200, work_zone="I", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=1600, work_zone="I", recovery_distance_m=400, recovery_zone="E")]),
        ("I_LADDER_600_1200", [IntervalBlock(reps=1, work_distance_m=600, work_zone="I", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=800, work_zone="I", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=1000, work_zone="I", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=1200, work_zone="I", recovery_distance_m=400, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=1000, work_zone="I", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=800, work_zone="I", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=600, work_zone="I", recovery_distance_m=200, recovery_zone="E")]),
    ]

    for code, main_blocks in mixed_sets:
        add(
            code=code,
            name=code.replace("_", " "),
            phase="Interval",
            main_zones=["I"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=main_blocks,
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            description="Pirâmides e mesclas para ritmo I com variação de estímulo.",
        )

    assert len(sessions) == 50, f"Interval sessions esperadas: 50, encontradas {len(sessions)}"
    return sessions


def _build_repetition_sessions() -> List[SessionTemplate]:
    sessions: List[SessionTemplate] = []

    def add(**kwargs: Any):
        sessions.append(_build_template(**kwargs))

    # Sessões base existentes
    add(
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
        description="Sessão de velocidade/neuromuscular.",
    )
    add(
        code="R_12x200",
        name="12 x 200m @ R",
        phase="Repetition",
        main_zones=["R"],
        warmup=[ContinuousSegment(duration_min=15, zone="E")],
        main=[
            IntervalBlock(
                reps=12,
                work_distance_m=200,
                work_zone="R",
                recovery_distance_m=200,
                recovery_zone="E",
                description="Volume maior em repetições curtas",
            )
        ],
        cooldown=[ContinuousSegment(duration_min=10, zone="E")],
        description="Aumenta contatos rápidos mantendo boa técnica.",
    )
    add(
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
        description="Repetições um pouco mais longas em R.",
    )
    add(
        code="R_6x400",
        name="6 x 400m @ R",
        phase="Repetition",
        main_zones=["R"],
        warmup=[ContinuousSegment(duration_min=15, zone="E")],
        main=[
            IntervalBlock(
                reps=6,
                work_distance_m=400,
                work_zone="R",
                recovery_distance_m=200,
                recovery_zone="E",
                description="Ritmo de repetição com foco em técnica",
            )
        ],
        cooldown=[ContinuousSegment(duration_min=12, zone="E")],
        description="R de maior duração para resistência de velocidade.",
    )
    add(
        code="R_STRIDES_SANDWICH",
        name="Easy 35' + 8x15\" strides",
        phase="Repetition",
        main_zones=["E", "R"],
        warmup=[ContinuousSegment(duration_min=12, zone="E")],
        main=[
            ContinuousSegment(duration_min=20, zone="E", description="Easy contínuo"),
            IntervalBlock(
                reps=8,
                work_duration_min=0.25,
                work_zone="R",
                recovery_duration_min=1.0,
                recovery_zone="E",
                description="Strides curtas para reforço neuromuscular",
            ),
        ],
        cooldown=[ContinuousSegment(duration_min=8, zone="E")],
        description="Combina volume leve com strides para velocidade controlada.",
    )

    # Séries curtas por distância
    repetition_sets = [
        ("R_10x150", 10, 150, 250),
        ("R_12x150", 12, 150, 250),
        ("R_14x150", 14, 150, 250),
        ("R_8x250", 8, 250, 250),
        ("R_10x250", 10, 250, 250),
        ("R_12x250", 12, 250, 250),
        ("R_8x300_SLOWREC", 8, 300, 300),
        ("R_10x300", 10, 300, 300),
        ("R_12x300", 12, 300, 300),
        ("R_8x350", 8, 350, 300),
        ("R_10x350", 10, 350, 300),
        ("R_12x350", 12, 350, 300),
        ("R_8x400", 8, 400, 300),
        ("R_10x400", 10, 400, 300),
        ("R_12x400", 12, 400, 300),
    ]

    for code, reps, dist, rec in repetition_sets:
        add(
            code=code,
            name=f"{reps} x {dist}m @ R",
            phase="Repetition",
            main_zones=["R"],
            warmup=[ContinuousSegment(duration_min=14, zone="E")],
            main=[
                IntervalBlock(
                    reps=reps,
                    work_distance_m=dist,
                    work_zone="R",
                    recovery_distance_m=rec,
                    recovery_zone="E",
                    description="Repetições rápidas com recuperação completa",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            description="Velocidade e técnica com recuperações generosas.",
        )

    extra_repetition_sets = [
        ("R_16x150", 16, 150, 250),
        ("R_15x200", 15, 200, 200),
        ("R_16x200", 16, 200, 200),
        ("R_10x220", 10, 220, 220),
        ("R_12x220", 12, 220, 220),
        ("R_10x250_FASTREC", 10, 250, 200),
        ("R_12x300_FASTREC", 12, 300, 200),
        ("R_8x350_FASTREC", 8, 350, 200),
        ("R_6x400_FLOAT", 6, 400, 200),
        ("R_10x200_FLOAT", 10, 200, 150),
        ("R_12x150_HILL", 12, 150, 200),
        ("R_6x300_HILL", 6, 300, 300),
        ("R_8x500", 8, 500, 300),
        ("R_10x500", 10, 500, 300),
        ("R_12x500", 12, 500, 300),
        ("R_6x600", 6, 600, 300),
        ("R_8x600", 8, 600, 300),
    ]

    for code, reps, dist, rec in extra_repetition_sets:
        add(
            code=code,
            name=f"{reps} x {dist}m @ R",
            phase="Repetition",
            main_zones=["R"],
            warmup=[ContinuousSegment(duration_min=14, zone="E")],
            main=[
                IntervalBlock(
                    reps=reps,
                    work_distance_m=dist,
                    work_zone="R",
                    recovery_distance_m=rec,
                    recovery_zone="E",
                    description="Repetições rápidas com foco em economia",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            description="Maior variedade de volume em ritmo de repetição.",
        )

    # Séries por tempo
    timed_reps = [
        ("R_12x30s", 12, 0.5, 1.5),
        ("R_15x30s", 15, 0.5, 1.5),
        ("R_10x45s", 10, 0.75, 1.75),
        ("R_12x45s", 12, 0.75, 1.75),
        ("R_10x60s", 10, 1.0, 2.0),
        ("R_12x60s", 12, 1.0, 2.0),
        ("R_8x75s", 8, 1.25, 2.0),
        ("R_10x75s", 10, 1.25, 2.0),
    ]

    for code, reps, work, rec in timed_reps:
        add(
            code=code,
            name=f"{reps} x {int(work * 60)}s @ R",
            phase="Repetition",
            main_zones=["R"],
            warmup=[ContinuousSegment(duration_min=12, zone="E")],
            main=[
                IntervalBlock(
                    reps=reps,
                    work_duration_min=work,
                    work_zone="R",
                    recovery_duration_min=rec,
                    recovery_zone="E",
                    description="Repetições controladas por tempo",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=8, zone="E")],
            description="Controle de velocidade pelo relógio, mantendo técnica apurada.",
        )

    # Mistos e fartleks rápidos
    mixed_sets = [
        ("R_STRIDES_10x20", [IntervalBlock(reps=10, work_duration_min=0.33, work_zone="R", recovery_duration_min=1.0, recovery_zone="E", description="Strides"), ContinuousSegment(duration_min=10, zone="E")]),
        ("R_HILL_SPRINTS_10x12s", [IntervalBlock(reps=10, work_duration_min=0.2, work_zone="R", recovery_duration_min=1.5, recovery_zone="E", description="Sprints em ladeira leve"), ContinuousSegment(duration_min=12, zone="E")]),
        ("R_MIX_200_300", [IntervalBlock(reps=6, work_distance_m=200, work_zone="R", recovery_distance_m=200, recovery_zone="E", description="Abertura"), IntervalBlock(reps=4, work_distance_m=300, work_zone="R", recovery_distance_m=200, recovery_zone="E", description="Fecho")]),
        ("R_MIX_200_400", [IntervalBlock(reps=6, work_distance_m=200, work_zone="R", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=4, work_distance_m=400, work_zone="R", recovery_distance_m=300, recovery_zone="E")]),
        ("R_LADDER_150_400", [IntervalBlock(reps=1, work_distance_m=150, work_zone="R", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=200, work_zone="R", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=250, work_zone="R", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=300, work_zone="R", recovery_distance_m=250, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=350, work_zone="R", recovery_distance_m=250, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=400, work_zone="R", recovery_distance_m=300, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=300, work_zone="R", recovery_distance_m=250, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=250, work_zone="R", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=200, work_zone="R", recovery_distance_m=200, recovery_zone="E"), IntervalBlock(reps=1, work_distance_m=150, work_zone="R", recovery_distance_m=200, recovery_zone="E")]),
    ]

    for code, main_blocks in mixed_sets:
        add(
            code=code,
            name=code.replace("_", " "),
            phase="Repetition",
            main_zones=["R"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=main_blocks,
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            description="Mistos curtos para reforço neuromuscular e técnica.",
        )

    assert len(sessions) == 50, f"Repetition sessions esperadas: 50, encontradas {len(sessions)}"
    return sessions

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
            code="BASE_EASY_30",
            name="Easy Run 30'",
            phase="Base",
            main_zones=["E"],
            warmup=[ContinuousSegment(duration_min=8, zone="E", description="Aquecimento leve")],
            main=[ContinuousSegment(duration_min=14, zone="E", description="Easy contínuo")],
            cooldown=[ContinuousSegment(duration_min=8, zone="E", description="Soltar")],
            base_distance_km=6.0,
            description="Sessão curta para fomentar frequência e recuperação ativa.",
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
            code="BASE_HILLS_DRILLS",
            name="Easy 45' + 6x20\" ladeira",
            phase="Base",
            main_zones=["E", "R"],
            warmup=[ContinuousSegment(duration_min=15, zone="E")],
            main=[
                ContinuousSegment(duration_min=25, zone="E", description="Easy contínuo"),
                IntervalBlock(
                    reps=6,
                    work_duration_min=0.33,
                    work_zone="R",
                    recovery_duration_min=1.5,
                    recovery_zone="E",
                    description="Strides em ladeira para técnica e força",
                ),
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=9.0,
            description="Inclui strides em ladeira para força e economia de corrida.",
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
    lib["EarlyQ"].append(
        SessionTemplate(
            code="EQ_FARTLEK_6x3T",
            name="Fartlek 6 x 3' @ T / 2' E",
            phase="EarlyQ",
            main_zones=["T", "E"],
            warmup=[ContinuousSegment(duration_min=12, zone="E")],
            main=[
                IntervalBlock(
                    reps=6,
                    work_duration_min=3.0,
                    work_zone="T",
                    recovery_duration_min=2.0,
                    recovery_zone="E",
                    description="Fartlek controlado em ritmo de limiar",
                )
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=10.0,
            description="Transição suave para treinos de limiar com variação de ritmo.",
        )
    )
    lib["EarlyQ"].append(
        SessionTemplate(
            code="EQ_PROGRESSIVE_55",
            name="Progressivo 55' (E → M/T)",
            phase="EarlyQ",
            main_zones=["E", "M", "T"],
            warmup=[ContinuousSegment(duration_min=10, zone="E")],
            main=[
                ContinuousSegment(duration_min=25, zone="E", description="Inicio controlado"),
                ContinuousSegment(duration_min=12, zone="M", description="Parte central moderada"),
                ContinuousSegment(duration_min=8, zone="T", description="Terminar em T leve"),
            ],
            cooldown=[ContinuousSegment(duration_min=5, zone="E")],
            base_distance_km=11.5,
            description="Progressão longa para construir resistência e sensação de ritmo.",
        )
    )

    # Threshold
    lib["Threshold"] = _build_threshold_sessions()

    # Interval
    lib["Interval"] = _build_interval_sessions()

    # Repetition
    lib["Repetition"] = _build_repetition_sessions()

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
            code="RS_2x2K",
            name="2 x 2000m (T → I)",
            phase="RS",
            main_zones=["T", "I"],
            warmup=[ContinuousSegment(duration_min=18, zone="E")],
            main=[
                IntervalBlock(
                    reps=2,
                    work_distance_m=2000,
                    work_zone="T",
                    recovery_duration_min=3.0,
                    recovery_zone="E",
                    description="Primeiro bloco em T controlado",
                ),
                IntervalBlock(
                    reps=1,
                    work_distance_m=1000,
                    work_zone="I",
                    recovery_duration_min=2.0,
                    recovery_zone="E",
                    description="Fecho próximo ao ritmo de prova",
                ),
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=11.0,
            description="Combina blocos longos em T e um toque em I para ritmo específico.",
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
    lib["RS"].append(
        SessionTemplate(
            code="RS_KM_FINISH",
            name="3K contínuo + 4 x 400m",
            phase="RS",
            main_zones=["T", "I", "R"],
            warmup=[ContinuousSegment(duration_min=18, zone="E")],
            main=[
                ContinuousSegment(distance_km=3.0, zone="T", description="Contínuo forte"),
                IntervalBlock(
                    reps=4,
                    work_distance_m=400,
                    work_zone="I",
                    recovery_distance_m=200,
                    recovery_zone="E",
                    description="400s rápidos para fechar a sessão",
                ),
            ],
            cooldown=[ContinuousSegment(duration_min=10, zone="E")],
            base_distance_km=11.0,
            description="Combina bloco contínuo forte com repetições curtas para finalização.",
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
            code="TP_SHARPEN_3x400",
            name="Easy 25' + 3 x 400m @ I",
            phase="Taper",
            main_zones=["E", "I"],
            warmup=[ContinuousSegment(duration_min=12, zone="E")],
            main=[
                ContinuousSegment(duration_min=13, zone="E", description="Easy contínuo"),
                IntervalBlock(
                    reps=3,
                    work_distance_m=400,
                    work_zone="I",
                    recovery_duration_min=2.0,
                    recovery_zone="E",
                    description="Curto toque em I para sentir ritmo",
                ),
            ],
            cooldown=[ContinuousSegment(duration_min=8, zone="E")],
            base_distance_km=7.0,
            description="Manutenção de ritmo sem gerar fadiga na semana de prova.",
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
    lib["Taper"].append(
        SessionTemplate(
            code="TP_EASY_TUNEUP",
            name="Easy 35' com strides e drills",
            phase="Taper",
            main_zones=["E", "R"],
            warmup=[ContinuousSegment(duration_min=12, zone="E")],
            main=[
                ContinuousSegment(duration_min=18, zone="E", description="Easy solto"),
                IntervalBlock(
                    reps=6,
                    work_duration_min=0.25,
                    work_zone="R",
                    recovery_duration_min=1.0,
                    recovery_zone="E",
                    description="Strides para manter reatividade",
                ),
            ],
            cooldown=[ContinuousSegment(duration_min=5, zone="E")],
            base_distance_km=7.0,
            description="Volume moderado com strides para chegar leve e rápido na prova.",
        )
    )

    return lib
