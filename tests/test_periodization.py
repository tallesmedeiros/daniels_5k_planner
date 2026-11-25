"""Run from the repository root: python -m unittest discover -s tests -v."""

import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np

# The repository itself is a package (no src/ layout or installation metadata).
# Load it under its public name even if a downloaded folder has another name.
ROOT = Path(__file__).resolve().parents[1]
if "daniels_5k_planner" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "daniels_5k_planner", ROOT / "__init__.py",
        submodule_search_locations=[str(ROOT)],
    )
    package = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = package
    spec.loader.exec_module(package)

from daniels_5k_planner import (
    AthleteConfig, Mesocycle, WeeklyVolumePlanner, build_5k_mesocycles,
    build_5k_phase_sequence_simple, generate_5k_plan_from_race,
)


ORDER = ("Base", "EarlyQ", "Threshold", "Interval", "Repetition", "RS", "Taper")
SHORT_EXPECTED = {
    2: ["Base", "Taper"],
    3: ["Base", "Threshold", "Taper"],
    4: ["Base", "Threshold", "Interval", "Taper"],
    5: ["Base", "Threshold", "Interval", "RS", "Taper"],
    6: ["Base", "EarlyQ", "Threshold", "Interval", "RS", "Taper"],
}
LEGACY = json.loads((ROOT / "tests/fixtures/legacy_phase_sequences.json").read_text())


def generate(weeks, frequency=3, mesocycles=None):
    return generate_5k_plan_from_race(
        athlete_name="Regression", race_distance_km=5.0, race_time_min=20.0,
        frequency_per_week=frequency, total_weeks=weeks,
        mesocycles=mesocycles,
    )


def custom_blocks(weeks):
    if weeks == 2:
        return [Mesocycle("Base", 1), Mesocycle("Taper", 1)]
    return [Mesocycle("Base", weeks - 2), Mesocycle("Threshold", 1), Mesocycle("Taper", 1)]


class TestAutomatic(unittest.TestCase):
    def test_termination_in_separate_process(self):
        # A timeout kills a reintroduced infinite loop without hanging the suite.
        code = """
import importlib.util, json, sys
from pathlib import Path
root = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location(
    'daniels_5k_planner', root / '__init__.py', submodule_search_locations=[str(root)])
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
spec.loader.exec_module(package)
print(json.dumps([len(package.build_5k_phase_sequence_simple(w)) for w in range(2, 25)]))
"""
        result = subprocess.run(
            [sys.executable, "-c", code, str(ROOT)],
            capture_output=True, text=True, timeout=10, check=True,
        )
        self.assertEqual(json.loads(result.stdout), list(range(2, 25)))

    def test_no_shared_mutable_state(self):
        first = build_5k_phase_sequence_simple(12)
        first.clear()
        self.assertEqual(len(build_5k_phase_sequence_simple(12)), 12)

    def test_numpy_integer(self):
        self.assertEqual(len(build_5k_phase_sequence_simple(np.int64(2))), 2)

    def test_supported_beyond_requested_range(self):
        self.assertEqual(len(build_5k_phase_sequence_simple(52)), 52)


def allocation_test(weeks):
    def test(self):
        sequence = build_5k_phase_sequence_simple(weeks)
        self.assertEqual(len(sequence), weeks)
        self.assertEqual(sequence[0], "Base")
        self.assertEqual(sequence[-1], "Taper")
        positions = [ORDER.index(phase) for phase in sequence]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(sequence, build_5k_phase_sequence_simple(weeks))
        blocks = build_5k_mesocycles(weeks)
        self.assertEqual(sum(block.weeks for block in blocks), weeks)
        self.assertTrue(all(block.weeks > 0 for block in blocks))
        self.assertEqual(sequence, [b.phase for b in blocks for _ in range(b.weeks)])
        if weeks < 7:
            self.assertEqual(sequence, SHORT_EXPECTED[weeks])
        else:
            self.assertEqual(set(sequence), set(ORDER))
    return test


def legacy_test(weeks):
    def test(self):
        # Fixed outputs captured from the untouched source, not a reimplementation.
        self.assertEqual(build_5k_phase_sequence_simple(weeks), LEGACY[str(weeks)])
    return test


class TestCustom(unittest.TestCase):
    def test_exact_arbitrary_durations(self):
        blocks = [Mesocycle("Base", 4), Mesocycle("Threshold", 3),
                  Mesocycle("Interval", 3), Mesocycle("Taper", 2)]
        self.assertEqual(
            build_5k_phase_sequence_simple(12, mesocycles=blocks),
            ["Base"] * 4 + ["Threshold"] * 3 + ["Interval"] * 3 + ["Taper"] * 2,
        )

    def test_partial_window_can_start_after_base(self):
        blocks = (Mesocycle("RS", 1), Mesocycle("Taper", 1))
        self.assertEqual(build_5k_phase_sequence_simple(2, mesocycles=blocks), ["RS", "Taper"])

    def test_adjacent_same_phase_boundaries_survive_generation(self):
        blocks = [Mesocycle("Base", 2), Mesocycle("Base", 3), Mesocycle("Threshold", 2)]
        original = blocks.copy()
        df, _ = generate(7, mesocycles=blocks)
        weekly = df.groupby("week").first()
        self.assertEqual(weekly["mesocycle"].tolist(), [1, 1, 2, 2, 2, 3, 3])
        self.assertEqual(weekly["week_in_mesocycle"].tolist(), [1, 2, 1, 2, 3, 1, 2])
        self.assertEqual(blocks, original)
        resolved = build_5k_mesocycles(7, mesocycles=blocks)
        resolved.clear()
        self.assertEqual(blocks, original)


def custom_test(weeks):
    def test(self):
        blocks = custom_blocks(weeks)
        expected = [block.phase for block in blocks for _ in range(block.weeks)]
        self.assertEqual(build_5k_phase_sequence_simple(weeks, mesocycles=blocks), expected)
        # A trainer may request only a base segment, with no forced taper.
        self.assertEqual(
            build_5k_phase_sequence_simple(weeks, mesocycles=[Mesocycle("Base", weeks)]),
            ["Base"] * weeks,
        )
    return test


class TestGeneration(unittest.TestCase):
    pass


def generation_test(weeks, frequency, explicit):
    def test(self):
        blocks = custom_blocks(weeks) if explicit else None
        df, vdot = generate(weeks, frequency, blocks)
        expected = build_5k_phase_sequence_simple(weeks, mesocycles=blocks)
        self.assertTrue(math.isfinite(vdot) and vdot > 0)
        self.assertEqual(len(df), weeks * frequency)
        self.assertEqual(sorted(df["week"].unique()), list(range(1, weeks + 1)))
        self.assertEqual(df.groupby("week").size().tolist(), [frequency] * weeks)
        self.assertFalse(df.duplicated(["week", "day_of_week"]).any())
        self.assertTrue(df["day_of_week"].between(1, 7).all())
        self.assertEqual(df.groupby("week")["phase"].first().tolist(), expected)
        self.assertTrue((df.groupby("week")["phase"].nunique() == 1).all())
        self.assertTrue(np.isfinite(df["planned_distance_km"]).all())
        self.assertTrue((df["planned_distance_km"] > 0).all())
        self.assertTrue(df["description"].str.len().gt(0).all())
        weekly_volume = df.groupby("week")["planned_distance_km"].sum()
        self.assertLess(weekly_volume.iloc[-1], weekly_volume.iloc[-2])
        if weeks < 7:
            self.assertLessEqual(weekly_volume.max(), 30.0 + 1e-9)
        if explicit:
            weekly = df.groupby("week").first()
            self.assertEqual(weekly["mesocycle"].tolist(),
                             [i for i, block in enumerate(blocks, 1) for _ in range(block.weeks)])
            self.assertEqual(weekly["week_in_mesocycle"].tolist(),
                             [w for block in blocks for w in range(1, block.weeks + 1)])
        else:
            self.assertEqual(list(df.columns), [
                "athlete", "week", "day_of_week", "weekday", "phase", "session_code",
                "session_name", "main_zones", "is_quality", "planned_distance_km", "description",
            ])
    return test


class TestVolume(unittest.TestCase):
    def setUp(self):
        self.planner = WeeklyVolumePlanner(AthleteConfig("Volume", 3))

    def test_two_week_taper_is_based_on_initial_load(self):
        self.assertEqual(self.planner.compute_weekly_targets(["Base", "Taper"]), [30.0, 21.0])

    def test_explicit_base_window_has_no_implicit_final_drop(self):
        df, _ = generate(8, mesocycles=[Mesocycle("Base", 8)])
        volumes = df.groupby("week")["planned_distance_km"].sum().tolist()
        self.assertAlmostEqual(volumes[0], 30.0)
        self.assertAlmostEqual(volumes[-1], 50.0)
        self.assertTrue(all(a <= b for a, b in zip(volumes, volumes[1:])))

    def test_two_week_base_is_a_maintenance_window(self):
        df, _ = generate(2, mesocycles=[Mesocycle("Base", 2)])
        for volume in df.groupby("week")["planned_distance_km"].sum():
            self.assertAlmostEqual(volume, 30.0)

    def test_multiple_taper_weeks_reduce_from_previous_load(self):
        blocks = [Mesocycle("Interval", 6), Mesocycle("Taper", 2)]
        df, _ = generate(8, mesocycles=blocks)
        volumes = df.groupby("week")["planned_distance_km"].sum().tolist()
        self.assertAlmostEqual(volumes[-3], 47.5)
        self.assertAlmostEqual(volumes[-2], 33.25)
        self.assertAlmostEqual(volumes[-1], 23.275)

    def test_taper_only_window(self):
        df, _ = generate(2, mesocycles=[Mesocycle("Taper", 2)])
        volumes = df.groupby("week")["planned_distance_km"].sum().tolist()
        self.assertAlmostEqual(volumes[0], 21.0)
        self.assertAlmostEqual(volumes[1], 14.7)

    def test_legacy_eight_week_volume_unchanged(self):
        sequence = build_5k_phase_sequence_simple(8)
        actual = self.planner.compute_weekly_targets(sequence)
        for target, expected in zip(actual, [30.0, 34.0, 38.0, 39.9, 43.7, 40.5, 36.0, 21.0]):
            self.assertAlmostEqual(target, expected)


class TestValidation(unittest.TestCase):
    def test_empty_explicit_blocks_are_not_automatic(self):
        with self.assertRaises(ValueError):
            build_5k_phase_sequence_simple(2, mesocycles=[])

    def test_unknown_phase(self):
        with self.assertRaises(ValueError):
            Mesocycle("Unknown", 2)

    def test_sum_mismatch(self):
        for blocks in ([Mesocycle("Base", 1)], [Mesocycle("Base", 3)]):
            with self.subTest(blocks=blocks), self.assertRaises(ValueError):
                build_5k_phase_sequence_simple(2, mesocycles=blocks)

    def test_backward_progression(self):
        for phases in (("Taper", "Base"), ("Interval", "Threshold"), ("RS", "Repetition")):
            with self.subTest(phases=phases), self.assertRaises(ValueError):
                build_5k_phase_sequence_simple(2, mesocycles=[Mesocycle(p, 1) for p in phases])

    def test_bad_block_containers(self):
        for blocks in ("Base", {"Base": 2}, 2, [None], [{"phase": "Base", "weeks": 2}]):
            with self.subTest(blocks=blocks), self.assertRaises(TypeError):
                build_5k_phase_sequence_simple(2, mesocycles=blocks)

    def test_generator_validates_before_race_calculation(self):
        with self.assertRaises(ValueError):
            generate_5k_plan_from_race("Invalid", 5.0, 0.0, 3, total_weeks=1)
        with self.assertRaises(ValueError):
            generate_5k_plan_from_race("Invalid", 5.0, 0.0, 3, total_weeks=2,
                                       mesocycles=[Mesocycle("Base", 3)])


def invalid_total_test(value, exception):
    def test(self):
        with self.assertRaises(exception):
            build_5k_phase_sequence_simple(value)
        with self.assertRaises(exception):
            build_5k_phase_sequence_simple(value, mesocycles=[Mesocycle("Base", 2)])
    return test


def invalid_duration_test(value, exception):
    def test(self):
        with self.assertRaises(exception):
            Mesocycle("Base", value)
    return test


# Named parameterized tests make each duration/frequency visible in unittest logs.
for weeks in range(2, 25):
    setattr(TestAutomatic, f"test_allocation_{weeks:02d}_weeks", allocation_test(weeks))
    setattr(TestCustom, f"test_configuration_{weeks:02d}_weeks", custom_test(weeks))
    if weeks >= 7:
        setattr(TestAutomatic, f"test_legacy_{weeks:02d}_weeks", legacy_test(weeks))
    for frequency in range(3, 8):
        setattr(TestGeneration, f"test_auto_{weeks:02d}_weeks_{frequency}_sessions",
                generation_test(weeks, frequency, False))
    for frequency in (3, 5):
        setattr(TestGeneration, f"test_custom_{weeks:02d}_weeks_{frequency}_sessions",
                generation_test(weeks, frequency, True))

for index, value in enumerate((-5, -1, 0, 1, 2.0, 2.5, "2", None, True, False, float("nan"), float("inf"))):
    error = ValueError if type(value) is int else TypeError
    setattr(TestValidation, f"test_invalid_total_{index:02d}", invalid_total_test(value, error))
for index, value in enumerate((-1, 0, 1.0, 1.5, "1", None, True, False)):
    error = ValueError if type(value) is int else TypeError
    setattr(TestValidation, f"test_invalid_duration_{index:02d}", invalid_duration_test(value, error))


if __name__ == "__main__":
    unittest.main()
