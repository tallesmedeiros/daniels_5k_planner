
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
            base_distance_km=12.0,
            description="Intervalos de limiar mais longos para consolidar o ritmo T.",
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
    lib["Threshold"].append(
        SessionTemplate(
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
            base_distance_km=13.0,
            description="Maior volume em T para elevar capacidade no ritmo de prova.",
        )
    )
    lib["Threshold"].append(
        SessionTemplate(
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
            base_distance_km=12.5,
            description="Tempo prolongado seguido de toques rápidos para reforço neuromuscular.",
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
            base_distance_km=12.0,
            description="Aumenta o tempo total em I mantendo recuperações curtas.",
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
    lib["Interval"].append(
        SessionTemplate(
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
            base_distance_km=12.0,
            description="Três repetições longas para maturar ritmo de 5K.",
        )
    )
    lib["Interval"].append(
        SessionTemplate(
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
            base_distance_km=11.5,
            description="Pirâmide progressiva para variar cadência mantendo estímulo de VO2max.",
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
            base_distance_km=8.5,
            description="Aumenta contatos rápidos mantendo boa técnica.",
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
    lib["Repetition"].append(
        SessionTemplate(
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
            base_distance_km=9.0,
            description="R de maior duração para resistência de velocidade.",
        )
    )
    lib["Repetition"].append(
        SessionTemplate(
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
            base_distance_km=8.0,
            description="Combina volume leve com strides para velocidade controlada.",
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
