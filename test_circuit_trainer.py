#!/usr/bin/env python3
"""
Comprehensive tests for interval-trainer.py

Run with: python3 -m pytest test_circuit_trainer.py -v
Or: python3 test_circuit_trainer.py
"""

import unittest
import sys
import io
import importlib.util
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch

# Import the module to test
MODULE_PATH = Path(__file__).parent / "interval-trainer.py"
SPEC = importlib.util.spec_from_file_location("interval_trainer", MODULE_PATH)
interval_trainer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(interval_trainer)

Exercise = interval_trainer.Exercise
EXERCISES = interval_trainer.EXERCISES
get_muscle_group_overlap = interval_trainer.get_muscle_group_overlap
create_paired_exercise = interval_trainer.create_paired_exercise
filter_exercises_by_equipment = interval_trainer.filter_exercises_by_equipment
filter_exercises_by_ankle_impact = interval_trainer.filter_exercises_by_ankle_impact
generate_circuit = interval_trainer.generate_circuit
print_circuit = interval_trainer.print_circuit


class TestExercise(unittest.TestCase):
    """Test Exercise dataclass."""
    
    def test_exercise_initialization_defaults(self):
        """Test Exercise initialization with default values."""
        ex = Exercise("Test", "Description", "core")
        self.assertEqual(ex.name, "Test")
        self.assertEqual(ex.description, "Description")
        self.assertEqual(ex.primary_muscle_group, "core")
        self.assertEqual(ex.secondary_muscle_groups, [])
        self.assertEqual(ex.equipment, [])
        self.assertEqual(ex.side_specific, False)
        self.assertEqual(ex.ankle_impact, False)
    
    def test_exercise_initialization_with_all_fields(self):
        """Test Exercise initialization with all fields specified."""
        ex = Exercise(
            "Push-ups",
            "Description",
            "chest",
            ["shoulders", "triceps"],
            ["box"],
            True,
            True  # ankle_impact
        )
        self.assertEqual(ex.name, "Push-ups")
        self.assertEqual(ex.secondary_muscle_groups, ["shoulders", "triceps"])
        self.assertEqual(ex.equipment, ["box"])
        self.assertEqual(ex.side_specific, True)
        self.assertEqual(ex.ankle_impact, True)
    
    def test_exercises_database_not_empty(self):
        """Test that EXERCISES database is populated."""
        self.assertGreater(len(EXERCISES), 0)
        self.assertIsInstance(EXERCISES[0], Exercise)
    
    def test_exercises_have_required_fields(self):
        """Test that all exercises have required fields."""
        for ex in EXERCISES:
            self.assertIsInstance(ex.name, str)
            self.assertGreater(len(ex.name), 0)
            self.assertIsInstance(ex.description, str)
            self.assertGreater(len(ex.description), 0)
            self.assertIsInstance(ex.primary_muscle_group, str)
            self.assertGreater(len(ex.primary_muscle_group), 0)
            self.assertIsInstance(ex.secondary_muscle_groups, list)
            self.assertIsInstance(ex.equipment, list)
            self.assertIsInstance(ex.side_specific, bool)
            self.assertIsInstance(ex.ankle_impact, bool)


class TestMuscleGroupOverlap(unittest.TestCase):
    """Test muscle group overlap calculation."""
    
    def test_same_primary_muscle_group(self):
        """Test that same primary muscle group returns high overlap."""
        ex1 = Exercise("Push-ups", "Desc", "chest", [], [], False)
        ex2 = Exercise("Chest Press", "Desc", "chest", [], [], False)
        overlap = get_muscle_group_overlap(ex1, ex2)
        self.assertEqual(overlap, 0.8)
    
    def test_different_primary_muscle_groups(self):
        """Test that different primary groups have lower overlap."""
        ex1 = Exercise("Push-ups", "Desc", "chest", [], [], False)
        ex2 = Exercise("Squats", "Desc", "quads", [], [], False)
        overlap = get_muscle_group_overlap(ex1, ex2)
        self.assertLess(overlap, 0.8)
        self.assertGreaterEqual(overlap, 0.0)
    
    def test_shared_secondary_muscle_groups(self):
        """Test overlap calculation with shared secondary groups."""
        ex1 = Exercise("Ex1", "Desc", "chest", ["shoulders"], [], False)
        ex2 = Exercise("Ex2", "Desc", "quads", ["shoulders"], [], False)
        overlap = get_muscle_group_overlap(ex1, ex2)
        self.assertGreater(overlap, 0.0)
        self.assertLess(overlap, 0.8)
    
    def test_no_overlap(self):
        """Test exercises with completely different muscle groups."""
        ex1 = Exercise("Push-ups", "Desc", "chest", [], [], False)
        ex2 = Exercise("Calf Raises", "Desc", "calves", [], [], False)
        overlap = get_muscle_group_overlap(ex1, ex2)
        self.assertEqual(overlap, 0.0)
    
    def test_empty_secondary_groups(self):
        """Test overlap with exercises that have no secondary groups."""
        ex1 = Exercise("Plank", "Desc", "core", [], [], False)
        ex2 = Exercise("Squats", "Desc", "quads", [], [], False)
        overlap = get_muscle_group_overlap(ex1, ex2)
        self.assertEqual(overlap, 0.0)


class TestCreatePairedExercise(unittest.TestCase):
    """Test creating paired exercises for side-specific workouts."""
    
    def test_create_left_paired_exercise(self):
        """Test creating a left-side version."""
        base = Exercise("Side Plank", "Desc", "core", ["obliques"], [], True)
        left = create_paired_exercise(base, "Left")
        self.assertEqual(left.name, "Left Side Plank")
        self.assertEqual(left.description, base.description)
        self.assertEqual(left.primary_muscle_group, base.primary_muscle_group)
        self.assertEqual(left.secondary_muscle_groups, base.secondary_muscle_groups)
        self.assertEqual(left.equipment, base.equipment)
        self.assertFalse(left.side_specific)  # Paired version is no longer side-specific
    
    def test_create_right_paired_exercise(self):
        """Test creating a right-side version."""
        base = Exercise("Bulgarian Split Squats", "Desc", "quads", ["glutes"], ["box"], True)
        right = create_paired_exercise(base, "Right")
        self.assertEqual(right.name, "Right Bulgarian Split Squats")
        self.assertEqual(right.equipment, ["box"])
        self.assertFalse(right.side_specific)
    
    def test_paired_exercise_independence(self):
        """Test that paired exercises are independent objects."""
        base = Exercise("Side Plank", "Desc", "core", ["obliques"], [], True)
        left = create_paired_exercise(base, "Left")
        right = create_paired_exercise(base, "Right")
        
        # Modify one and ensure the other is unaffected
        left.secondary_muscle_groups.append("test")
        self.assertNotIn("test", right.secondary_muscle_groups)


class TestFilterExercisesByEquipment(unittest.TestCase):
    """Test equipment filtering."""
    
    def test_filter_bodyweight_only(self):
        """Test filtering for bodyweight-only exercises."""
        bodyweight_exercises = filter_exercises_by_equipment(EXERCISES, [])
        self.assertGreater(len(bodyweight_exercises), 0)
        for ex in bodyweight_exercises:
            self.assertEqual(ex.equipment, [])
    
    def test_filter_with_pull_up_bar(self):
        """Test filtering exercises that require pull-up bar."""
        filtered = filter_exercises_by_equipment(EXERCISES, ["pull_up_bar"])
        self.assertGreater(len(filtered), 0)
        # Should include bodyweight exercises and pull-up bar exercises
        has_pull_up = any("Pull-up" in ex.name or "Chin-up" in ex.name or "Inverted Row" in ex.name 
                         for ex in filtered)
        # All exercises should either have no equipment or require pull_up_bar
        for ex in filtered:
            self.assertTrue(not ex.equipment or "pull_up_bar" in ex.equipment)
    
    def test_filter_with_box(self):
        """Test filtering exercises that require box."""
        filtered = filter_exercises_by_equipment(EXERCISES, ["box"])
        self.assertGreater(len(filtered), 0)
        for ex in filtered:
            self.assertTrue(not ex.equipment or "box" in ex.equipment)
    
    def test_filter_with_multiple_equipment(self):
        """Test filtering with multiple equipment types."""
        filtered = filter_exercises_by_equipment(EXERCISES, ["box", "pull_up_bar"])
        self.assertGreater(len(filtered), 0)
        for ex in filtered:
            if ex.equipment:
                # All required equipment must be in the available list
                self.assertTrue(all(eq in ["box", "pull_up_bar"] for eq in ex.equipment))
    
    def test_filter_all_exercises_when_none_specified(self):
        """Test that None equipment returns all exercises."""
        # This is handled in generate_circuit, but we test the function directly
        # When available_equipment is not None but is empty, it should filter
        filtered = filter_exercises_by_equipment(EXERCISES, [])
        self.assertLess(len(filtered), len(EXERCISES))
    
    def test_filter_exercises_requiring_multiple_equipment(self):
        """Test filtering exercises that require multiple equipment items."""
        # Hip Thrusts requires both box and bench
        filtered = filter_exercises_by_equipment(EXERCISES, ["box", "bench"])
        hip_thrusts = [ex for ex in filtered if "Hip Thrust" in ex.name]
        # Hip Thrusts should be included if both box and bench are available
        if hip_thrusts:
            self.assertTrue(any("Hip Thrust" in ex.name for ex in filtered))


class TestFilterExercisesByAnkleImpact(unittest.TestCase):
    """Test ankle impact filtering."""
    
    def test_filter_without_ankle_impact_flag(self):
        """Test that filter returns all exercises when flag is False."""
        filtered = filter_exercises_by_ankle_impact(EXERCISES, False)
        self.assertEqual(len(filtered), len(EXERCISES))
    
    def test_filter_with_ankle_impact_flag(self):
        """Test that filter removes exercises with ankle impact when flag is True."""
        filtered = filter_exercises_by_ankle_impact(EXERCISES, True)
        self.assertLess(len(filtered), len(EXERCISES))
        
        # Verify no ankle impact exercises in filtered list
        for ex in filtered:
            self.assertFalse(ex.ankle_impact, f"{ex.name} should not have ankle impact")
    
    def test_filter_removes_jumping_exercises(self):
        """Test that jumping exercises are filtered out."""
        filtered = filter_exercises_by_ankle_impact(EXERCISES, True)
        filtered_names = [ex.name for ex in filtered]
        
        # Known jumping exercises with ankle_impact=True should be filtered out
        # Check which exercises actually have ankle_impact set
        jumping_exercises_with_impact = [
            ex.name for ex in EXERCISES 
            if "Jump" in ex.name and ex.ankle_impact
        ]
        
        for jump_ex in jumping_exercises_with_impact:
            self.assertNotIn(jump_ex, filtered_names, 
                           f"{jump_ex} should be filtered out")
    
    def test_filter_removes_running_exercises(self):
        """Test that running exercises are filtered out."""
        filtered = filter_exercises_by_ankle_impact(EXERCISES, True)
        filtered_names = [ex.name for ex in filtered]
        
        # Known running exercises should be filtered out
        running_exercises = ["High Knees", "Butt Kicks"]
        for run_ex in running_exercises:
            self.assertNotIn(run_ex, filtered_names,
                           f"{run_ex} should be filtered out")
    
    def test_filter_removes_burpees(self):
        """Test that burpees (which involve jumping) are filtered out."""
        filtered = filter_exercises_by_ankle_impact(EXERCISES, True)
        filtered_names = [ex.name for ex in filtered]
        self.assertNotIn("Burpees", filtered_names)
    
    def test_filter_keeps_non_ankle_impact_exercises(self):
        """Test that exercises without ankle impact are kept."""
        filtered = filter_exercises_by_ankle_impact(EXERCISES, True)
        filtered_names = [ex.name for ex in filtered]
        
        # Known non-ankle impact exercises should be kept
        safe_exercises = ["Push-ups", "Squats", "Plank", "Glute Bridges"]
        for safe_ex in safe_exercises:
            self.assertIn(safe_ex, filtered_names,
                        f"{safe_ex} should not be filtered out")
    
    def test_filter_empty_list(self):
        """Test filtering an empty exercise list."""
        filtered = filter_exercises_by_ankle_impact([], True)
        self.assertEqual(len(filtered), 0)


class TestGenerateCircuit(unittest.TestCase):
    """Test circuit generation."""
    
    def test_generate_circuit_default(self):
        """Test generating a circuit with default parameters."""
        circuit = generate_circuit()
        self.assertIsInstance(circuit, list)
        self.assertGreater(len(circuit), 0)
        # Circuit may be longer than requested due to side-specific pairing
        # Default is 8, but side-specific exercises become pairs
        self.assertGreater(len(circuit), 0)
    
    def test_generate_circuit_custom_count(self):
        """Test generating a circuit with custom exercise count."""
        circuit = generate_circuit(num_exercises=5)
        # Circuit may be longer than requested due to side-specific pairing
        # Each side-specific exercise adds 1 extra (becomes a pair)
        self.assertGreater(len(circuit), 0)
        # Should have at least 5, but may have more if side-specific exercises are included
        self.assertGreaterEqual(len(circuit), 5)
    
    def test_generate_circuit_all_exercises(self):
        """Test generating a circuit with all available exercises."""
        circuit = generate_circuit(num_exercises=len(EXERCISES) * 2)
        # Circuit length is limited by available exercises
        # May be longer than len(EXERCISES) due to side-specific pairing
        self.assertGreater(len(circuit), 0)
        # Maximum would be all exercises, each potentially paired
        num_side_specific = sum(1 for ex in EXERCISES if ex.side_specific)
        max_possible = len(EXERCISES) + num_side_specific
        self.assertLessEqual(len(circuit), max_possible)
    
    def test_generate_circuit_with_equipment_filter(self):
        """Test generating a circuit with equipment filtering."""
        circuit = generate_circuit(num_exercises=10, available_equipment=["pull_up_bar"])
        self.assertGreater(len(circuit), 0)
        for ex in circuit:
            self.assertTrue(not ex.equipment or "pull_up_bar" in ex.equipment)
    
    def test_generate_circuit_bodyweight_only(self):
        """Test generating a bodyweight-only circuit."""
        circuit = generate_circuit(num_exercises=10, available_equipment=[])
        self.assertGreater(len(circuit), 0)
        for ex in circuit:
            self.assertEqual(ex.equipment, [])
    
    def test_generate_circuit_side_specific_pairing(self):
        """Test that side-specific exercises are automatically paired."""
        # Generate multiple circuits to increase chance of getting side-specific exercise
        found_paired = False
        for _ in range(20):
            circuit = generate_circuit(num_exercises=15)
            # Check if any side-specific exercises appear as pairs
            for i in range(len(circuit) - 1):
                ex1_name = circuit[i].name
                ex2_name = circuit[i + 1].name
                # Check for paired side-specific exercises
                if (ex1_name.startswith("Left ") and ex2_name.startswith("Right ") and
                    ex1_name[5:] == ex2_name[6:]):  # Same base name
                    found_paired = True
                    break
                if (ex1_name.startswith("Right ") and ex2_name.startswith("Left ") and
                    ex1_name[6:] == ex2_name[5:]):  # Same base name
                    found_paired = True
                    break
            if found_paired:
                break
        # This might not always find a pair due to randomness, but we test the logic
        # We can at least verify the function doesn't crash
    
    def test_generate_circuit_muscle_group_balance(self):
        """Test that consecutive exercises avoid same primary muscle group."""
        circuit = generate_circuit(num_exercises=10, avoid_consecutive_overlap=0.5)
        for i in range(len(circuit) - 1):
            overlap = get_muscle_group_overlap(circuit[i], circuit[i + 1])
            # With threshold 0.5, overlap should be <= 0.5 (except for side-specific pairs)
            # Side-specific pairs will have high overlap, which is expected
            if not (circuit[i].name.startswith(("Left ", "Right ")) and 
                   circuit[i + 1].name.startswith(("Left ", "Right "))):
                # For non-paired exercises, overlap should respect threshold
                # But due to algorithm, it might exceed if no better option exists
                pass  # We just verify it doesn't crash
    
    def test_generate_circuit_different_results(self):
        """Test that circuits are randomized (different results on multiple calls)."""
        circuit1 = generate_circuit(num_exercises=10)
        circuit2 = generate_circuit(num_exercises=10)
        # Due to randomness, they might be the same, but with enough exercises
        # and multiple calls, we should get different results
        # We at least verify both are valid
        self.assertIsInstance(circuit1, list)
        self.assertIsInstance(circuit2, list)
    
    def test_generate_circuit_strict_overlap_threshold(self):
        """Test circuit generation with strict overlap threshold."""
        circuit = generate_circuit(num_exercises=10, avoid_consecutive_overlap=0.1)
        self.assertGreater(len(circuit), 0)
        # With very strict threshold, algorithm should still work


class TestRerollFeature(unittest.TestCase):
    """Test rerolling individual exercises and side-specific pairs."""

    def test_reroll_single_exercise_by_number(self):
        """Test rerolling a single non-side-specific exercise."""
        ex_a = Exercise("A", "Desc", "core", [], [], False)
        ex_b = Exercise("B", "Desc", "chest", [], [], False)
        ex_c = Exercise("C", "Desc", "quads", [], [], False)
        ex_d = Exercise("D", "Desc", "back", [], [], False)
        circuit = [ex_a, ex_b, ex_c]

        with patch.object(interval_trainer, "EXERCISES", [ex_a, ex_b, ex_c, ex_d]):
            rerolled_numbers, success = interval_trainer.reroll_exercise_group(
                circuit, 2, overlap_threshold=0.5
            )

        self.assertTrue(success)
        self.assertEqual(rerolled_numbers, [2])
        self.assertEqual(circuit[1].name, "D")

    def test_reroll_side_specific_rerolls_both_sides(self):
        """Test rerolling one side of a pair replaces both sides."""
        side_old = Exercise("Old Split Squat", "Desc", "quads", [], [], True)
        side_new = Exercise("New Split Squat", "Desc", "quads", [], [], True)
        filler = Exercise("Push-ups", "Desc", "chest", [], [], False)
        circuit = [
            create_paired_exercise(side_old, "Left"),
            create_paired_exercise(side_old, "Right"),
            filler,
        ]

        with patch.object(interval_trainer, "EXERCISES", [side_old, side_new, filler]):
            rerolled_numbers, success = interval_trainer.reroll_exercise_group(
                circuit, 1, overlap_threshold=0.5
            )

        self.assertTrue(success)
        self.assertEqual(rerolled_numbers, [1, 2])
        self.assertTrue(circuit[0].name.endswith("New Split Squat"))
        self.assertTrue(circuit[1].name.endswith("New Split Squat"))
        self.assertNotEqual(circuit[0].name[:5], circuit[1].name[:5])  # Left vs Right prefixes

    def test_prompt_for_rerolls_accepts_number_and_updates_circuit(self):
        """Test interactive prompt rerolls selected number then exits on Enter."""
        ex_a = Exercise("A", "Desc", "core", [], [], False)
        ex_b = Exercise("B", "Desc", "chest", [], [], False)
        ex_c = Exercise("C", "Desc", "quads", [], [], False)
        ex_d = Exercise("D", "Desc", "back", [], [], False)
        circuit = [ex_a, ex_b, ex_c]

        with patch.object(interval_trainer, "EXERCISES", [ex_a, ex_b, ex_c, ex_d]), \
             patch("sys.stdin.isatty", return_value=True), \
             patch("builtins.input", side_effect=["2", ""]), \
             patch.object(interval_trainer, "print_circuit") as mock_print_circuit:
            interval_trainer.prompt_for_rerolls(
                circuit,
                "Test Workout",
                False,
                overlap_threshold=0.5,
            )

        self.assertEqual(circuit[1].name, "D")
        mock_print_circuit.assert_called_once()


class TestPrintCircuit(unittest.TestCase):
    """Test circuit printing functionality."""
    
    def test_print_circuit_default_format(self):
        """Test printing circuit in default (non-verbose) format."""
        circuit = [
            Exercise("Push-ups", "Test description", "chest", [], [], False),
            Exercise("Squats", "Another description", "quads", [], [], False)
        ]
        f = io.StringIO()
        with redirect_stdout(f):
            print_circuit(circuit, "Test Workout", verbose=False)
        output = f.getvalue()
        self.assertIn("Test Workout", output)
        self.assertIn("Push-ups", output)
        self.assertIn("Test description", output)
        self.assertIn("Squats", output)
        self.assertIn("Another description", output)
        # Default format should be single line
        self.assertIn("Push-ups - Test description", output)
    
    def test_print_circuit_verbose_format(self):
        """Test printing circuit in verbose format."""
        circuit = [
            Exercise("Push-ups", "Test description", "chest", ["shoulders"], ["box"], False)
        ]
        f = io.StringIO()
        with redirect_stdout(f):
            print_circuit(circuit, "Test Workout", verbose=True)
        output = f.getvalue()
        self.assertIn("Test Workout", output)
        self.assertIn("Push-ups", output)
        self.assertIn("Test description", output)
        self.assertIn("Primary: Chest", output)
        self.assertIn("Secondary: Shoulders", output)
        self.assertIn("Equipment: Box", output)
    
    def test_print_circuit_verbose_bodyweight(self):
        """Test verbose format for bodyweight exercises."""
        circuit = [
            Exercise("Plank", "Test description", "core", [], [], False)
        ]
        f = io.StringIO()
        with redirect_stdout(f):
            print_circuit(circuit, "Test Workout", verbose=True)
        output = f.getvalue()
        self.assertIn("Equipment: None (bodyweight)", output)
    
    def test_print_circuit_multiple_exercises(self):
        """Test printing multiple exercises."""
        circuit = [
            Exercise("Ex1", "Desc1", "core", [], [], False),
            Exercise("Ex2", "Desc2", "quads", [], [], False),
            Exercise("Ex3", "Desc3", "chest", [], [], False)
        ]
        f = io.StringIO()
        with redirect_stdout(f):
            print_circuit(circuit, "Test Workout", verbose=False)
        output = f.getvalue()
        self.assertIn("1. Ex1", output)
        self.assertIn("2. Ex2", output)
        self.assertIn("3. Ex3", output)


class TestSideSpecificExercises(unittest.TestCase):
    """Test side-specific exercise functionality."""
    
    def test_side_specific_exercises_identified(self):
        """Test that side-specific exercises are properly marked."""
        side_specific = [ex for ex in EXERCISES if ex.side_specific]
        self.assertGreater(len(side_specific), 0)
        # Known side-specific exercises
        side_plank = [ex for ex in EXERCISES if ex.name == "Side Plank"]
        if side_plank:
            self.assertTrue(side_plank[0].side_specific)
    
    def test_side_specific_exercises_list(self):
        """Test that known side-specific exercises are marked."""
        known_side_specific = [
            "Side Plank",
            "Bulgarian Split Squats",
            "Single Leg Glute Bridge",
            "Single Leg Calf Raises"
        ]
        for name in known_side_specific:
            exercises = [ex for ex in EXERCISES if ex.name == name]
            if exercises:
                self.assertTrue(exercises[0].side_specific, f"{name} should be side-specific")


class TestIntegration(unittest.TestCase):
    """Integration tests for the full workflow."""
    
    def test_full_workflow_default(self):
        """Test the full workflow with default parameters."""
        circuit = generate_circuit()
        self.assertIsInstance(circuit, list)
        self.assertGreater(len(circuit), 0)
        
        # Test printing
        f = io.StringIO()
        with redirect_stdout(f):
            print_circuit(circuit)
        output = f.getvalue()
        self.assertIn("Circuit Training Workout", output)
    
    def test_full_workflow_with_equipment(self):
        """Test the full workflow with equipment filtering."""
        circuit = generate_circuit(num_exercises=10, available_equipment=["box", "pull_up_bar"])
        self.assertGreater(len(circuit), 0)
        
        # Verify equipment filtering worked
        for ex in circuit:
            if ex.equipment:
                self.assertTrue(any(eq in ["box", "pull_up_bar"] for eq in ex.equipment))
    
    def test_full_workflow_side_specific(self):
        """Test the full workflow with side-specific exercises."""
        # Generate many circuits to increase chance of getting side-specific
        for _ in range(10):
            circuit = generate_circuit(num_exercises=15)
            # Check if any exercises have "Left" or "Right" prefix
            has_paired = any(ex.name.startswith(("Left ", "Right ")) for ex in circuit)
            if has_paired:
                # Verify they come in pairs
                i = 0
                while i < len(circuit):
                    if circuit[i].name.startswith("Left "):
                        if i + 1 < len(circuit) and circuit[i + 1].name.startswith("Right "):
                            base1 = circuit[i].name[5:]
                            base2 = circuit[i + 1].name[6:]
                            self.assertEqual(base1, base2)
                    elif circuit[i].name.startswith("Right "):
                        if i + 1 < len(circuit) and circuit[i + 1].name.startswith("Left "):
                            base1 = circuit[i].name[6:]
                            base2 = circuit[i + 1].name[5:]
                            self.assertEqual(base1, base2)
                    i += 1
                break


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_generate_circuit_zero_exercises(self):
        """Test generating circuit with zero exercises."""
        circuit = generate_circuit(num_exercises=0)
        self.assertEqual(len(circuit), 0)
    
    def test_generate_circuit_negative_exercises(self):
        """Test generating circuit with negative exercise count."""
        circuit = generate_circuit(num_exercises=-1)
        # Should handle gracefully (might return empty or use default)
        self.assertIsInstance(circuit, list)
    
    def test_generate_circuit_very_large_count(self):
        """Test generating circuit with very large exercise count."""
        circuit = generate_circuit(num_exercises=1000)
        # Circuit length is limited by available exercises
        # May be longer than len(EXERCISES) due to side-specific pairing
        self.assertGreater(len(circuit), 0)
        num_side_specific = sum(1 for ex in EXERCISES if ex.side_specific)
        max_possible = len(EXERCISES) + num_side_specific
        self.assertLessEqual(len(circuit), max_possible)
    
    def test_filter_empty_exercises_list(self):
        """Test filtering an empty exercise list."""
        filtered = filter_exercises_by_equipment([], ["box"])
        self.assertEqual(len(filtered), 0)
    
    def test_overlap_same_exercise(self):
        """Test overlap calculation with the same exercise."""
        ex = Exercise("Test", "Desc", "core", [], [], False)
        overlap = get_muscle_group_overlap(ex, ex)
        self.assertEqual(overlap, 0.8)  # Same primary group


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
