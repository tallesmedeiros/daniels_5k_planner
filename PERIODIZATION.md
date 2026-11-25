# Planejamentos curtos e mesociclos configuráveis

## Contrato da API

- `total_weeks` deve ser um inteiro maior ou igual a 2. Não há limite máximo de 24;
  2–24 semanas é a faixa de validação sistemática desta alteração.
- `Mesocycle(phase, weeks)` define a ênfase e a duração exata de cada bloco.
  A duração deve ser um inteiro positivo; valores booleanos não são aceitos.
- `mesocycles=None` seleciona a distribuição automática. Uma lista vazia é erro.
- No modo explícito, a soma das durações deve coincidir com `total_weeks`.
  Não há truncamento, preenchimento ou redistribuição silenciosa.
- As fases conhecidas seguem a ordem da biblioteca existente:
  `Base → EarlyQ → Threshold → Interval → Repetition → RS → Taper`.
- É permitido omitir fases, iniciar em uma fase intermediária, não incluir Taper
  e definir blocos adjacentes com a mesma fase. A ordem não pode retroceder.
  Este contrato representa uma janela com uma progressão; múltiplos picos ou
  retorno à base devem ser modelados como janelas separadas.
- A configuração é uma lista ou tupla de objetos `Mesocycle`. Dicionários de JSON
  podem ser convertidos explicitamente com `[Mesocycle(**item) for item in dados]`.

## Por que o laço anterior travava

Havia sete fases, todas com o limite inferior de uma semana. Logo,
`sum(weeks_map.values()) >= 7`. Para `total_weeks < 7`, a redução nunca podia
alcançar o total solicitado: depois de todas as fases chegarem a uma semana,
nenhuma condição do corpo do `while diff > 0` alterava `diff`.

A correção seleciona uma sequência apropriada ao tamanho da janela antes de
distribuir semanas. Os ajustes proporcionais de planos com pelo menos sete
semanas usam laços limitados. A saída é verificada por igualdade de comprimento;
não se utiliza mais `phase_sequence[:total_weeks]` para esconder uma divergência.

## Política metodológica adotada

O modo automático conserva a orientação a uma prova, com introdução e polimento
final. Para janelas curtas, utiliza menos ênfases distintas:

| Semanas | Sequência automática |
| --- | --- |
| 2 | Base → Taper |
| 3 | Base → Threshold → Taper |
| 4 | Base → Threshold → Interval → Taper |
| 5 | Base → Threshold → Interval → RS → Taper |
| 6 | Base → EarlyQ → Threshold → Interval → RS → Taper |
| 7–24 | Mesmas sequências proporcionais da versão anterior |

Cada entrada nas linhas de 2–6 semanas corresponde a uma semana. A política é
uma decisão explícita de implementação compatível com as fases já existentes;
não representa uma nova regra universal atribuída a Jack Daniels. Janelas de
duas a seis semanas não equivalem à preparação fisiológica completa de sete
fases. A adequação das sessões depende do histórico do atleta e da seleção do
treinador. Um bloco de uma semana pode representar a parte final de um período
anterior ou o polimento; não implica que uma adaptação se complete em uma semana.

Quando a janela não termina em prova, o treinador deve fornecer os blocos
explicitamente. Por exemplo, `Mesocycle("Base", 2)` mantém duas semanas de base,
sem introduzir polimento nem qualidade automaticamente.

## Volume semanal

A correção também ajusta a integração com `WeeklyVolumePlanner`:

1. Em janelas menores que sete semanas, o volume de referência permanece em
   `initial_weekly_volume`, com os fatores de fase já existentes. Não se força
   a progressão até `peak_weekly_volume` em uma janela curta.
2. No modo explícito, para janelas de pelo menos sete semanas, a referência
   progride linearmente do volume inicial ao pico nas semanas anteriores ao
   Taper. Os fatores de fase continuam sendo aplicados.
3. Nas semanas de Taper desse modo, aplica-se o fator existente de 0,70 ao volume
   efetivo da semana anterior. Em uma janela composta apenas por Taper, a
   primeira redução usa o volume inicial. Tapers consecutivos aplicam reduções
   sucessivas de 30%.
4. Não há queda automática nas últimas três semanas de um bloco explícito sem
   Taper. A curva legada permanece para planos automáticos de sete ou mais
   semanas, preservando compatibilidade.

Com os volumes padrão de 30 e 50 km, a antiga regra de volume produziria
30 km e 35 km para `["Base", "Taper"]`. A nova regra produz **30 km e 21 km**.
Os fatores e essa curva são uma política do software; não substituem ajuste de
carga pelo treinador. A alteração não redesenha os templates, zonas ou mecanismo
existente de escalonamento das sessões.

## Código de uso

```python
from daniels_5k_planner import (
    Mesocycle,
    build_5k_mesocycles,
    build_5k_phase_sequence_simple,
    generate_5k_plan_from_race,
)

assert build_5k_phase_sequence_simple(2) == ["Base", "Taper"]
assert build_5k_phase_sequence_simple(
    2, mesocycles=[Mesocycle("Base", 2)]
) == ["Base", "Base"]

mesocycles = [
    Mesocycle("Base", 4),
    Mesocycle("Threshold", 3),
    Mesocycle("Interval", 3),
    Mesocycle("Taper", 2),
]

sequence = build_5k_phase_sequence_simple(12, mesocycles=mesocycles)
assert len(sequence) == 12

plan_df, vdot = generate_5k_plan_from_race(
    athlete_name="Exemplo",
    race_distance_km=5.0,
    race_time_min=20.0,
    frequency_per_week=3,
    total_weeks=12,
    initial_weekly_volume=30.0,
    peak_weekly_volume=50.0,
    mesocycles=mesocycles,
)

print(plan_df[["week", "phase", "mesocycle", "week_in_mesocycle"]])
```

O retorno continua sendo `(DataFrame, vdot)`. Chamadas anteriores continuam
válidas. As colunas `mesocycle` e `week_in_mesocycle` são acrescentadas somente
quando a configuração explícita é fornecida, preservando as colunas do modo
automático. Ambas começam em 1. Blocos consecutivos com a mesma fase mantêm IDs
distintos. Os novos argumentos são exclusivos de palavra-chave.

## Testes automatizados

Na raiz do repositório, com NumPy e pandas disponíveis:

```bash
python -m unittest discover -s tests -v
```

Os testes usam `unittest`, da biblioteca padrão. Não exigem pytest, acesso à
rede, serviços externos ou alterações no GitHub. Python 3.10 ou superior é
necessário pelas anotações de tipo já presentes no projeto.

| Grupo | Testes |
| --- | ---: |
| Alocação automática, cada duração de 2 a 24 | 23 |
| Compatibilidade com sequências originais de 7 a 24 | 18 |
| Terminação, isolamento, inteiro NumPy e janela de 52 semanas | 4 |
| Configuração explícita e preservação dos limites dos blocos | 26 |
| Geração completa automática: 23 durações × 5 frequências (3–7) | 115 |
| Geração completa explícita: 23 durações × 2 frequências (3 e 5) | 46 |
| Comportamento do volume e polimento | 6 |
| Entradas inválidas e propagação de validação | 26 |
| **Total** | **264** |

A regressão do laço infinito é executada em um processo separado, com limite de
10 segundos. Assim, uma regressão não bloqueia indefinidamente a suíte. As
sequências de referência de 7–24 semanas foram capturadas da versão original,
não recalculadas por uma cópia do algoritmo novo.

Os testes de integração verificam número de semanas e sessões, sequência das
fases, ausência de duplicação de dias, volumes finitos e positivos, descrições,
redução final do volume e metadados dos mesociclos. Validam o comportamento do
software; não constituem validação experimental das adaptações de treinamento.
