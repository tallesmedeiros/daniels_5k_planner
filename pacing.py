
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
        def format_continuous(seg: ContinuousSegment) -> str:
            base = (
                f"{seg.distance_km:.1f} km"
                if seg.distance_km is not None
                else f"{seg.duration_min:.0f} min"
            )
            detail = f"@ {seg.pace_slow_str}–{seg.pace_fast_str} ({seg.zone})"
            extra = f" · {seg.description}" if seg.description else ""
            return f"{base} {detail}{extra}"

        def format_interval(block: IntervalBlock) -> str:
            work = (
                f"{block.work_distance_m:.0f} m"
                if block.work_distance_m is not None
                else f"{block.work_duration_min:.0f} min"
            )
            rec = (
                f"{block.recovery_distance_m:.0f} m"
                if block.recovery_distance_m is not None
                else f"{block.recovery_duration_min:.0f} min"
            )
            work_pace = f"@ {block.work_pace_slow_str}–{block.work_pace_fast_str} ({block.work_zone})"
            rec_pace = f"@ {block.rec_pace_slow_str}–{block.rec_pace_fast_str} ({block.recovery_zone})"
            block_desc = f" · {block.description}" if block.description else ""
            return f"{block.reps} x {work} {work_pace} | rec {rec} {rec_pace}{block_desc}"

        lines = [f"🏃‍♀️ {template.name} · fase {template.phase}"]
        if template.description:
            lines.append(f"   🎯 {template.description}")
        lines.append(f"   🔑 Zonas principais: {'/'.join(template.main_zones)}")

        if template.warmup:
            lines.append("   🔥 Aquecimento:")
            for seg in template.warmup:
                lines.append(f"      • {format_continuous(seg)}")

        if template.main:
            lines.append("   🧭 Parte principal:")
            for item in template.main:
                if isinstance(item, ContinuousSegment):
                    lines.append(f"      • {format_continuous(item)}")
                elif isinstance(item, IntervalBlock):
                    lines.append(f"      • {format_interval(item)}")

        if template.cooldown:
            lines.append("   🧊 Desaquecimento:")
            for seg in template.cooldown:
                lines.append(f"      • {format_continuous(seg)}")

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


def format_plan_for_console(plan_df: pd.DataFrame) -> str:
    """Formata um DataFrame de plano semanal em blocos legíveis no console."""

    if plan_df.empty:
        return "Nenhuma sessão encontrada para o período informado."

    lines: List[str] = []
    last_phase: str | None = None
    sorted_plan = plan_df.sort_values(["week", "day_of_week"])

    for week, week_df in sorted_plan.groupby("week"):
        phases = week_df["phase"].unique()
        phase_label = "/".join(phases)

        if phase_label != last_phase:
            if last_phase is not None:
                lines.append("")
            lines.append(f"🏁 Fase: {phase_label}")
            last_phase = phase_label

        lines.append(f"📅 Semana {week}")

        for _, row in week_df.sort_values("day_of_week").iterrows():
            flag = "🔥" if row["is_quality"] else "🌿"
            dist = f"{row['planned_distance_km']:.1f} km"
            lines.append(
                f"  {flag} {row['weekday']}: {row['session_name']} ({row['session_code']})"
            )
            lines.append(
                f"     → Zonas {row['main_zones']} · Distância alvo: {dist}"
            )
            for desc_line in str(row["description"]).splitlines():
                lines.append(f"     ↳ {desc_line}")

    lines.append("")
    return "\n".join(lines)


def format_plan_as_table(plan_df: pd.DataFrame, columns: List[str] | None = None) -> str:
    """Gera uma tabela textual completa, sem truncar a descrição das sessões.

    Args:
        plan_df: DataFrame retornado por ``workouts_to_dataframe`` ou ``generate_5k_plan_from_race``.
        columns: colunas que devem aparecer na tabela. Se ``None``, todas as colunas são usadas.

    Returns:
        Uma string com a tabela formatada usando ``pandas.DataFrame.to_string`` e
        sem limite de largura de coluna, garantindo que a descrição apareça por completo.
    """

    if plan_df.empty:
        return "Nenhuma sessão encontrada para o período informado."

    cols = columns if columns is not None else list(plan_df.columns)

    # Evita que quebras de linha no texto da descrição baguncem a tabela, mas mantém o conteúdo.
    df_clean = plan_df.copy()
    if "description" in df_clean.columns:
        df_clean["description"] = df_clean["description"].astype(str).str.replace("\n", " | ")

    with pd.option_context("display.max_colwidth", None, "display.width", None):
        # ``line_width=None`` evita que pandas quebre a linha após um número
        # fixo de caracteres, o que poderia cortar visualmente a coluna de
        # descrição em terminais estreitos. ``max_colwidth=None`` garante que
        # o texto não seja truncado com reticências.
        return df_clean[cols].to_string(index=False, line_width=None, max_colwidth=None)


def print_plan(plan_df: pd.DataFrame) -> None:
    """Imprime o plano em formato amigável para leitura no terminal."""

    print(format_plan_for_console(plan_df))
