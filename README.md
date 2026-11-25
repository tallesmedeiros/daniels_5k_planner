# 🏃‍♂️ Daniels 5K Planner

Bem-vindo ao **Daniels 5K Planner**, um micro toolkit em Python que converte tempos de prova em planos semanais para 5 km segundo a metodologia de Jack Daniels. O projeto é modular e pronto para ser usado em notebooks, scripts ou pipelines de dados.

## 📚 Visão geral rápida
- 🔢 **Estimativa fisiológica**: converta um resultado de prova em VDOT e derive zonas oficiais (E/M/T/I/R).
- 🧭 **Fases de ciclo**: sequência automática de:
  - Base
  - EarlyQ
  - Threshold
  - Interval
  - Repetition
  - RS
  - Taper
- 📅 **Planejamento semanal**: escolha de sessões por fase, distribuição em dias e ajuste por volume-alvo.
- 🏷️ **Workouts anotados**: cada sessão recebe ritmos alvo, descrição human-friendly e metadados prontos para análise (DataFrame).
- 🔁 **Feedback**: módulo para ajustar volumes e carga de qualidade a partir de dados semanais.

## 🗂️ Estrutura de módulos e responsabilidades

### 👤 `athlete.AthleteConfig`
Representa o perfil do atleta (nome, frequência semanal, objetivo e volumes inicial/pico). É usado como base por todos os componentes de planejamento.【F:athlete.py†L1-L8】

### 📦 `sessions.py`: vocabulário de treinos
- `ContinuousSegment` e `IntervalBlock` modelam partes de uma sessão (contínuo por distância/tempo ou blocos intervalados), validando que ao menos um campo de distância/tempo foi preenchido.【F:sessions.py†L8-L48】
- `SessionTemplate` descreve um treino completo com aquecimento, parte principal, desaquecimento, zonas principais e distância-base para escalonamento.【F:sessions.py†L50-L61】
- `Workout` é o objeto final (já agendado por semana/dia) que pode ser exportado para tabelas.【F:sessions.py†L64-L77】
- `build_5k_session_library()` fornece uma biblioteca curada de treinos para cada fase (Base, EarlyQ, Threshold, Interval, Repetition, RS e Taper), incluindo descrições e distâncias base.【F:sessions.py†L79-L354】

### 🧠 `selection.WeeklySessionSelector`
- Calcula quantas sessões de qualidade cabem em cada fase com base na frequência semanal.【F:selection.py†L13-L27】
- Define dias-alvo para treinar conforme a frequência (ex.: 3x/semana → terça/quinta/sábado).【F:selection.py†L29-L45】
- Gira as sessões de qualidade e easy da biblioteca para evitar repetições diretas, distribuindo-as nos dias preferenciais.【F:selection.py†L47-L88】
- Produz um plano semanal bruto (fase + sessões com dia da semana e template).【F:selection.py†L90-L106】

### 📈 `volume.WeeklyVolumePlanner`
- Gera uma curva de volume que progride do volume inicial ao pico e aplica reduções específicas por fase (Interval, Repetition, RS, Taper).【F:volume.py†L6-L41】
- Aplica o volume alvo ao plano semanal escalonando a distância-base de cada sessão; se não houver base, mantém valores originais.【F:volume.py†L43-L68】

### 🧪 `zones.DanielsZones`
Calcula zonas oficiais de Daniels para um VDOT dado, resolvendo a equação de VO₂ ↔ velocidade e formatando ritmos em mm:ss. Retorna um DataFrame pronto para consulta ou exportação.【F:zones.py†L1-L73】【F:zones.py†L82-L101】

### 🎯 `pacing.WorkoutPaceAnnotator` & helpers
- Anota ritmos (lento/rápido) em cada segmento de um template usando as zonas calculadas.【F:pacing.py†L7-L48】
- Gera descrições legíveis da sessão (aquecimento, parte principal, desaquecimento) e marca se é treino de qualidade.【F:pacing.py†L50-L107】
- Converte o plano semanal (com volume aplicado) em uma lista de `Workout` e depois para `DataFrame` ordenado por semana/dia.【F:pacing.py†L113-L168】

### 🔮 `feedback.FeedbackEngine`
- Recebe feedback semanal (volume planejado x realizado, fadiga, dores, RPE) e calcula fatores de ajuste para volume e carga de qualidade com comentários explicativos.【F:feedback.py†L24-L63】
- Aplica o ajuste ao vetor de volumes-alvo a partir de uma semana específica, permitindo replanejamento dinâmico.【F:feedback.py†L65-L73】

### 🧰 `utils.parse_time_mmss_to_min`
Converte strings "mm:ss" em minutos decimais — útil para entrada de tempo de prova.【F:utils.py†L1-L4】

### 🎬 `facade_5k.py`: orquestração ponta a ponta
- `estimate_vdot_from_race`: converte distância/tempo em VDOT seguindo fórmulas de Daniels.【F:facade_5k.py†L15-L21】
- `build_5k_phase_sequence_simple`: cria uma sequência de fases proporcional ao total de semanas, ajustando sobras/faltas com base em prioridades clássicas.【F:facade_5k.py†L25-L71】
- `generate_5k_plan_from_race`: pipeline completo ⏩ cria atleta, fases, biblioteca de sessões, seleciona treinos semanais, calcula volumes, aplica ritmos e entrega um `DataFrame` pronto + VDOT estimado.【F:facade_5k.py†L73-L105】

## 🔧 Como o gerador de treinos funciona
```mermaid
graph TD;
    A[Tempo de prova (km + min)] --> B[estimate_vdot_from_race];
    B --> C[DanielsZones.build_dataframe];
    C --> D[WorkoutPaceAnnotator];
    B --> E[AthleteConfig];
    E --> F[build_5k_phase_sequence_simple];
    F --> G[WeeklySessionSelector.build_weekly_plan];
    E --> H[WeeklyVolumePlanner];
    G --> H;
    H --> I[apply_volume_to_plan];
    I --> J[weekly_plan_to_workouts];
    J --> K[workouts_to_dataframe];
    K --> L[Plano final + ritmos];
```

1. **Entrada**: informe distância (km) e tempo (min) de uma prova recente.
2. **VDOT & zonas**: o VDOT é calculado e usado para gerar zonas E/M/T/I/R.
3. **Fases**: o ciclo recebe proporções ajustadas ao número total de semanas.
4. **Seleção de sessões**: para cada semana, o seletor decide quantas sessões de qualidade cabem, rota os templates e agenda dias conforme a frequência do atleta.
5. **Volume**: o planejador gera a curva de volume, aplica fatores por fase e escala as sessões para bater a meta semanal.
6. **Ritmos & descrição**: cada segmento recebe ritmos de acordo com as zonas, e o treino ganha descrição detalhada.
7. **Saída**: um `DataFrame` com todas as sessões (semana, dia, fase, código, zonas principais, distância planejada e descrição legível). Use feedback semanal para ajustar volumes e cargas futuras.

## 🚀 Exemplo rápido
```python
import daniels_5k_planner as d5k

plan_df, vdot = d5k.generate_5k_plan_from_race(
    athlete_name="Patrícia",
    race_distance_km=5.0,
    race_time_min=24.5,
    frequency_per_week=4,
    total_weeks=8,
)
print(vdot)
print(plan_df.head())
```

## 🤝 Contribuição
Sinta-se livre para abrir issues ou PRs com novos templates de sessão, ajustes de curva de volume ou melhorias nas descrições. Bons treinos! 🏅

## Mesociclos configuráveis e planos curtos

O gerador aceita planejamentos a partir de **duas semanas**. O argumento opcional
`mesocycles=[Mesocycle("Base", 4), Mesocycle("Threshold", 3)]` permite definir
as fases e suas durações exatas. Consulte [PERIODIZATION.md](PERIODIZATION.md)
para regras, exemplos, política de volume e instruções dos testes automatizados.
