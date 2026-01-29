#!/usr/bin/env python3
"""
Circuit Training Interval Exercise Generator

Generates randomized lists of interval training exercises for circuit workouts
with balanced muscle group distribution.
"""

import random
import yaml
import os
from pathlib import Path
from typing import List, Dict, Tuple
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


def generate_circuit(num_exercises: int = 8, avoid_consecutive_overlap: float = 0.5, available_equipment: List[str] = None, avoid_ankle_impact: bool = False) -> List[Exercise]:
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
    
    parser = argparse.ArgumentParser(
        description="Generate randomized circuit training workouts with balanced muscle groups"
    )
    parser.add_argument(
        "-n", "--num-exercises",
        type=int,
        default=8,
        help="Number of exercises in the circuit (default: 8)"
    )
    parser.add_argument(
        "-o", "--overlap-threshold",
        type=float,
        default=0.5,
        help="Maximum allowed muscle group overlap between consecutive exercises (0-1, default: 0.5)"
    )
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=1,
        help="Number of different circuits to generate (default: 1)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output with muscle groups (default: compact single-line format)"
    )
    parser.add_argument(
        "-e", "--equipment",
        nargs="+",
        default=None,
        help="Available equipment (space-separated). Options: pull_up_bar, box, bench, wall, weight. "
             "If not specified, all exercises are available. If empty list provided, only bodyweight exercises."
    )
    parser.add_argument(
        "--no-ankle-impact",
        action="store_true",
        help="Exclude exercises that involve ankle impact (jumping, running, etc.)"
    )
    
    args = parser.parse_args()
    
    # Handle equipment argument
    available_equipment = args.equipment if args.equipment is not None else None
    
    for i in range(args.count):
        if args.count > 1:
            workout_name = f"Circuit Training Workout #{i+1}"
        else:
            workout_name = "Circuit Training Workout"
        
        circuit = generate_circuit(args.num_exercises, args.overlap_threshold, available_equipment, args.no_ankle_impact)
        print_circuit(circuit, workout_name, args.verbose)
        
        if i < args.count - 1:
            print("\n" + "-"*60 + "\n")


if __name__ == "__main__":
    main()
