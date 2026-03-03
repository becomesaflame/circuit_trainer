#!/usr/bin/env python3
"""
Circuit Training Interval Exercise Generator

Generates randomized lists of interval training exercises for circuit workouts
with balanced muscle group distribution.
"""

import random
import yaml
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Exercise:
    """Represents a single exercise with its details."""
    name: str
    description: str
    primary_muscle_group: str
    secondary_muscle_groups: List[str] = None
    equipment: List[str] = None
    side_specific: bool = False
    ankle_impact: bool = False
    
    def __post_init__(self):
        if self.secondary_muscle_groups is None:
            self.secondary_muscle_groups = []
        if self.equipment is None:
            self.equipment = []


def load_exercises(config_path: str = None) -> List[Exercise]:
    """
    Load exercises from YAML configuration file.
    
    Args:
        config_path: Path to the YAML config file. If None, uses exercises.yaml in the same directory.
    
    Returns:
        List of Exercise objects
    """
    if config_path is None:
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        config_path = script_dir / "exercises.yaml"
    
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    
    exercises = []
    for ex_data in data.get('exercises', []):
        exercise = Exercise(
            name=ex_data['name'],
            description=ex_data['description'],
            primary_muscle_group=ex_data['primary_muscle_group'],
            secondary_muscle_groups=ex_data.get('secondary_muscle_groups', []),
            equipment=ex_data.get('equipment', []),
            side_specific=ex_data.get('side_specific', False),
            ankle_impact=ex_data.get('ankle_impact', False)
        )
        exercises.append(exercise)
    
    return exercises


# Load exercises from YAML configuration file
EXERCISES = load_exercises()
CONFIG_FILE_NAME = ".interval-trainer.config.yaml"


def get_program_defaults() -> Dict[str, object]:
    """Return immutable program defaults for CLI options."""
    return {
        "num_exercises": 10,
        "overlap_threshold": 0.5,
        "count": 1,
        "verbose": False,
        "equipment": [],  # Default to bodyweight-only at the script level
        "no_ankle_impact": False,
    }


def save_local_config(config: Dict[str, object], config_path: Optional[Path] = None):
    """Persist config values to the local config file."""
    path = config_path or (Path(__file__).parent / CONFIG_FILE_NAME)
    with open(path, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False)


def load_or_create_local_config(config_path: Optional[Path] = None) -> Dict[str, object]:
    """
    Load local config from disk, creating it with program defaults if missing.
    """
    defaults = get_program_defaults()
    path = config_path or (Path(__file__).parent / CONFIG_FILE_NAME)

    if not path.exists():
        save_local_config(defaults, path)
        return defaults.copy()

    with open(path, "r") as f:
        loaded = yaml.safe_load(f) or {}

    if not isinstance(loaded, dict):
        loaded = {}

    normalized = defaults.copy()
    for key in defaults:
        if key in loaded:
            normalized[key] = loaded[key]

    # Keep equipment config constrained to expected shapes.
    if normalized["equipment"] is not None and not isinstance(normalized["equipment"], list):
        normalized["equipment"] = defaults["equipment"]

    # Backfill missing/invalid keys for future runs.
    save_local_config(normalized, path)
    return normalized


def merge_cli_options_with_config(
    config: Dict[str, object],
    cli_args: Dict[str, object]
) -> Tuple[Dict[str, object], Dict[str, object]]:
    """
    Merge CLI-provided options onto config values.

    Returns:
        (effective_options, normalized_overrides)
    """
    normalized_overrides: Dict[str, object] = {}

    if cli_args.get("all_equipment"):
        normalized_overrides["equipment"] = None
    elif cli_args.get("bodyweight_only"):
        normalized_overrides["equipment"] = []

    for key in get_program_defaults():
        if key in cli_args:
            normalized_overrides[key] = cli_args[key]

    effective = config.copy()
    effective.update(normalized_overrides)
    return effective, normalized_overrides


def get_muscle_group_overlap(ex1: Exercise, ex2: Exercise) -> float:
    """
    Calculate how much two exercises overlap in muscle groups.
    Returns a value between 0 (no overlap) and 1 (complete overlap).
    Penalizes primary muscle group matches more heavily.
    """
    # If primary muscle groups match, return high overlap
    if ex1.primary_muscle_group == ex2.primary_muscle_group:
        return 0.8
    
    groups1 = set([ex1.primary_muscle_group] + ex1.secondary_muscle_groups)
    groups2 = set([ex2.primary_muscle_group] + ex2.secondary_muscle_groups)
    
    if not groups1 or not groups2:
        return 0.0
    
    intersection = groups1.intersection(groups2)
    union = groups1.union(groups2)
    
    # Jaccard similarity coefficient
    return len(intersection) / len(union) if union else 0.0


def create_paired_exercise(exercise: Exercise, side: str) -> Exercise:
    """
    Create a left or right version of a side-specific exercise.
    
    Args:
        exercise: The base exercise
        side: Either "Left" or "Right"
    
    Returns:
        A new Exercise with the side specified in the name
    """
    side_name = f"{side} {exercise.name}"
    return Exercise(
        name=side_name,
        description=exercise.description,
        primary_muscle_group=exercise.primary_muscle_group,
        secondary_muscle_groups=exercise.secondary_muscle_groups.copy(),
        equipment=exercise.equipment.copy(),
        side_specific=False  # The paired version is no longer side-specific
    )


def split_side_prefix(exercise_name: str) -> Tuple[Optional[str], str]:
    """
    Split side prefix from an exercise name.

    Returns:
        Tuple of (side, base_name) where side is "Left"/"Right" or None.
    """
    if exercise_name.startswith("Left "):
        return "Left", exercise_name[5:]
    if exercise_name.startswith("Right "):
        return "Right", exercise_name[6:]
    return None, exercise_name


def get_paired_indices(circuit: List[Exercise], index: int) -> List[int]:
    """
    Get one or two indices representing the selected reroll group.
    If the selected exercise has an opposite-side pair in the circuit,
    both indices are returned.
    """
    selected = circuit[index]
    side, base_name = split_side_prefix(selected.name)

    if side is None:
        return [index]

    opposite_side = "Right" if side == "Left" else "Left"
    opposite_name = f"{opposite_side} {base_name}"

    for i, ex in enumerate(circuit):
        if i != index and ex.name == opposite_name:
            return sorted([index, i])

    return [index]


def get_filtered_exercise_pool(
    available_equipment: List[str] = None,
    avoid_ankle_impact: bool = False
) -> List[Exercise]:
    """Return the global exercise pool with active filters applied."""
    exercises_pool = filter_exercises_by_ankle_impact(EXERCISES, avoid_ankle_impact)
    if available_equipment is not None:
        exercises_pool = filter_exercises_by_equipment(exercises_pool, available_equipment)
    return exercises_pool


def choose_replacement_exercises(
    candidates: List[Exercise],
    group_size: int,
    previous_exercise: Optional[Exercise],
    next_exercise: Optional[Exercise],
    overlap_threshold: float
) -> Optional[List[Exercise]]:
    """
    Choose one replacement exercise (group_size=1) or one paired side-specific
    replacement (group_size=2), favoring overlap threshold when possible.
    """
    if not candidates:
        return None

    shuffled = candidates.copy()
    random.shuffle(shuffled)
    best_choice = None
    best_score = float("inf")

    for exercise in shuffled:
        if group_size == 2:
            sides = ["Left", "Right"]
            random.shuffle(sides)
            replacement_group = [
                create_paired_exercise(exercise, sides[0]),
                create_paired_exercise(exercise, sides[1]),
            ]
        else:
            replacement_group = [exercise]

        overlap_prev = 0.0
        if previous_exercise is not None:
            overlap_prev = get_muscle_group_overlap(previous_exercise, replacement_group[0])

        overlap_next = 0.0
        if next_exercise is not None:
            overlap_next = get_muscle_group_overlap(replacement_group[-1], next_exercise)

        max_overlap = max(overlap_prev, overlap_next)

        if overlap_prev <= overlap_threshold and overlap_next <= overlap_threshold:
            return replacement_group

        if max_overlap < best_score:
            best_score = max_overlap
            best_choice = replacement_group

    return best_choice


def reroll_exercise_group(
    circuit: List[Exercise],
    exercise_number: int,
    overlap_threshold: float,
    available_equipment: List[str] = None,
    avoid_ankle_impact: bool = False
) -> Tuple[List[int], bool]:
    """
    Re-roll one exercise (1-based index), or both if it has an opposite-side pair.

    Returns:
        (rerolled_indices, success)
    """
    index = exercise_number - 1
    if index < 0 or index >= len(circuit):
        return [], False

    group_indices = get_paired_indices(circuit, index)
    group_size = len(group_indices)

    group_start = min(group_indices)
    group_end = max(group_indices)
    previous_exercise = circuit[group_start - 1] if group_start > 0 else None
    next_exercise = circuit[group_end + 1] if group_end + 1 < len(circuit) else None

    # Avoid duplicate base exercises in the resulting circuit where possible.
    # Side-specific displayed variants are normalized by removing Left/Right prefix.
    remaining_base_names = {
        split_side_prefix(ex.name)[1]
        for i, ex in enumerate(circuit)
        if i not in group_indices
    }
    original_base_names = {split_side_prefix(circuit[i].name)[1] for i in group_indices}

    filtered_pool = get_filtered_exercise_pool(available_equipment, avoid_ankle_impact)
    if group_size == 2:
        candidates = [ex for ex in filtered_pool if ex.side_specific]
    else:
        candidates = [ex for ex in filtered_pool if not ex.side_specific]

    candidates = [
        ex for ex in candidates
        if ex.name not in remaining_base_names and ex.name not in original_base_names
    ]

    replacement_group = choose_replacement_exercises(
        candidates,
        group_size,
        previous_exercise,
        next_exercise,
        overlap_threshold,
    )
    if replacement_group is None:
        return group_indices, False

    # Replace in place while preserving circuit length.
    circuit[group_start:group_end + 1] = replacement_group
    return [i + 1 for i in range(group_start, group_end + 1)], True


def prompt_for_rerolls(
    circuit: List[Exercise],
    workout_name: str,
    verbose: bool,
    overlap_threshold: float,
    available_equipment: List[str] = None,
    avoid_ankle_impact: bool = False
):
    """Interactive prompt to reroll exercise numbers after initial generation."""
    if not sys.stdin.isatty():
        return

    while True:
        user_input = input(
            "\nEnter exercise number to reroll (press Enter to keep this workout): "
        ).strip()
        if not user_input:
            break
        if not user_input.isdigit():
            print("Please enter a valid exercise number.")
            continue

        exercise_number = int(user_input)
        rerolled_numbers, success = reroll_exercise_group(
            circuit,
            exercise_number,
            overlap_threshold,
            available_equipment,
            avoid_ankle_impact,
        )

        if not success:
            print("Unable to reroll that exercise with current constraints. Try another number.")
            continue

        if len(rerolled_numbers) == 2:
            print(f"Re-rolled paired exercises #{rerolled_numbers[0]} and #{rerolled_numbers[1]}.")
        else:
            print(f"Re-rolled exercise #{rerolled_numbers[0]}.")

        print_circuit(circuit, workout_name, verbose)


def filter_exercises_by_ankle_impact(exercises: List[Exercise], avoid_ankle_impact: bool = False) -> List[Exercise]:
    """
    Filter exercises to exclude those with ankle impact if requested.
    
    Args:
        exercises: List of exercises to filter
        avoid_ankle_impact: If True, remove exercises with ankle impact
    
    Returns:
        Filtered list of exercises
    """
    if not avoid_ankle_impact:
        return exercises
    
    return [ex for ex in exercises if not ex.ankle_impact]


def filter_exercises_by_equipment(exercises: List[Exercise], available_equipment: List[str]) -> List[Exercise]:
    """
    Filter exercises to only include those that can be performed with available equipment.
    
    Args:
        exercises: List of exercises to filter
        available_equipment: List of available equipment (empty list means bodyweight only)
    
    Returns:
        Filtered list of exercises
    """
    if not available_equipment:
        # If no equipment specified, only return exercises that require no equipment
        return [ex for ex in exercises if not ex.equipment]
    
    available_set = set(available_equipment)
    filtered = []
    
    for ex in exercises:
        # Exercise is available if all required equipment is in available_equipment
        if not ex.equipment or all(eq in available_set for eq in ex.equipment):
            filtered.append(ex)
    
    return filtered


def generate_circuit(num_exercises: int = 10, avoid_consecutive_overlap: float = 0.5, available_equipment: List[str] = None, avoid_ankle_impact: bool = False) -> List[Exercise]:
    """
    Generate a randomized circuit training list with balanced muscle groups.
    
    Args:
        num_exercises: Number of exercises to include in the circuit
        avoid_consecutive_overlap: Maximum allowed overlap between consecutive exercises (0-1)
        available_equipment: List of available equipment (None means all exercises available)
        avoid_ankle_impact: If True, exclude exercises with ankle impact (jumping, running, etc.)
    
    Returns:
        List of Exercise objects in randomized order
    """
    # Start with all exercises
    exercises_pool = EXERCISES
    
    # Filter exercises by ankle impact first
    exercises_pool = filter_exercises_by_ankle_impact(exercises_pool, avoid_ankle_impact)
    
    # Filter exercises by available equipment
    if available_equipment is not None:
        exercises_pool = filter_exercises_by_equipment(exercises_pool, available_equipment)
    
    if num_exercises > len(exercises_pool):
        num_exercises = len(exercises_pool)
    
    available_exercises = exercises_pool.copy()
    random.shuffle(available_exercises)
    
    circuit = []
    slots_used = 0
    
    while slots_used < num_exercises:
        if not available_exercises:
            break
        
        # Determine how many slots we have left
        slots_remaining = num_exercises - slots_used
        
        # If only 1 slot remains, only consider non-side-specific exercises
        if slots_remaining == 1:
            eligible_exercises = [ex for ex in available_exercises if not ex.side_specific]
            if not eligible_exercises:
                # No non-side-specific exercises available, we're done
                break
        else:
            # Can consider all exercises
            eligible_exercises = available_exercises
        
        if slots_used == 0:
            # First exercise can be anything from eligible exercises
            selected_exercise = eligible_exercises[0]
            available_exercises.remove(selected_exercise)
        else:
            # Find an exercise that doesn't overlap too much with the previous one
            best_exercise = None
            
            for exercise in eligible_exercises:
                overlap = get_muscle_group_overlap(circuit[-1], exercise)
                if overlap <= avoid_consecutive_overlap:
                    best_exercise = exercise
                    break
            
            # If no good match found, pick the one with least overlap
            if best_exercise is None:
                best_overlap = float('inf')
                for exercise in eligible_exercises:
                    overlap = get_muscle_group_overlap(circuit[-1], exercise)
                    if overlap < best_overlap:
                        best_overlap = overlap
                        best_exercise = exercise
            
            available_exercises.remove(best_exercise)
            selected_exercise = best_exercise
        
        # If exercise is side-specific, create paired versions (left and right)
        # Side-specific exercises count as 2 exercises in the circuit
        if selected_exercise.side_specific:
            # Randomly choose which side comes first
            sides = ["Left", "Right"]
            random.shuffle(sides)
            circuit.append(create_paired_exercise(selected_exercise, sides[0]))
            circuit.append(create_paired_exercise(selected_exercise, sides[1]))
            slots_used += 2
        else:
            circuit.append(selected_exercise)
            slots_used += 1
    
    return circuit


def print_circuit(circuit: List[Exercise], workout_name: str = "Circuit Training Workout", verbose: bool = False):
    """Print a formatted circuit workout."""
    print(f"\n{'='*60}")
    print(f"  {workout_name}")
    print(f"{'='*60}\n")
    
    for i, exercise in enumerate(circuit, 1):
        if verbose:
            # Verbose format: multi-line with muscle groups and equipment
            print(f"{i}. {exercise.name}")
            print(f"   {exercise.description}")
            primary_display = exercise.primary_muscle_group.replace('_', ' ').title()
            print(f"   Primary: {primary_display}")
            if exercise.secondary_muscle_groups:
                secondary_display = ', '.join(m.replace('_', ' ').title() for m in exercise.secondary_muscle_groups)
                print(f"   Secondary: {secondary_display}")
            if exercise.equipment:
                equipment_display = ', '.join(e.replace('_', ' ').title() for e in exercise.equipment)
                print(f"   Equipment: {equipment_display}")
            else:
                print(f"   Equipment: None (bodyweight)")
            print()
        else:
            # Default format: single line with name and description
            print(f"{i}. {exercise.name} - {exercise.description}")


def main():
    """Main function to generate and display circuit workouts."""
    import argparse
    config_path = Path(__file__).parent / CONFIG_FILE_NAME
    config = load_or_create_local_config(config_path)

    parser = argparse.ArgumentParser(
        description="Generate randomized circuit training workouts with balanced muscle groups"
    )
    parser.add_argument(
        "-n", "--num-exercises",
        type=int,
        default=argparse.SUPPRESS,
        help="Number of exercises in the circuit (default from local config, initial: 10)"
    )
    parser.add_argument(
        "-o", "--overlap-threshold",
        type=float,
        default=argparse.SUPPRESS,
        help="Max allowed overlap between consecutive exercises (default from local config, initial: 0.5)"
    )
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=argparse.SUPPRESS,
        help="Number of different circuits to generate (default from local config, initial: 1)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Show detailed output with muscle groups"
    )
    parser.add_argument(
        "--no-verbose",
        action="store_false",
        dest="verbose",
        default=argparse.SUPPRESS,
        help="Disable detailed output with muscle groups"
    )
    parser.add_argument(
        "-e", "--equipment",
        nargs="+",
        default=argparse.SUPPRESS,
        help="Available equipment (space-separated). Options: pull_up_bar, box, bench, wall, weight. "
             "If omitted, the value from local config is used (initial default is bodyweight-only)."
    )
    parser.add_argument(
        "--all-equipment",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Allow all exercises regardless of equipment requirements"
    )
    parser.add_argument(
        "--bodyweight-only",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Use only exercises with no equipment requirements"
    )
    parser.add_argument(
        "--no-ankle-impact",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Exclude exercises that involve ankle impact (jumping, running, etc.)"
    )
    parser.add_argument(
        "--allow-ankle-impact",
        action="store_false",
        dest="no_ankle_impact",
        default=argparse.SUPPRESS,
        help="Allow ankle-impact exercises"
    )

    args = parser.parse_args()
    cli_args = vars(args)
    effective_options, overrides = merge_cli_options_with_config(config, cli_args)
    if overrides:
        updated_config = config.copy()
        updated_config.update(overrides)
        save_local_config(updated_config, config_path)

    available_equipment = effective_options["equipment"]

    for i in range(effective_options["count"]):
        if effective_options["count"] > 1:
            workout_name = f"Circuit Training Workout #{i+1}"
        else:
            workout_name = "Circuit Training Workout"
        
        circuit = generate_circuit(
            effective_options["num_exercises"],
            effective_options["overlap_threshold"],
            available_equipment,
            effective_options["no_ankle_impact"],
        )
        print_circuit(circuit, workout_name, effective_options["verbose"])
        prompt_for_rerolls(
            circuit,
            workout_name,
            effective_options["verbose"],
            effective_options["overlap_threshold"],
            available_equipment,
            effective_options["no_ankle_impact"],
        )
        
        if i < effective_options["count"] - 1:
            print("\n" + "-"*60 + "\n")


if __name__ == "__main__":
    main()
