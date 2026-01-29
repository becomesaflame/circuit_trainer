#!/usr/bin/env python3
"""
Circuit Training Interval Exercise Generator

Generates randomized lists of interval training exercises for circuit workouts
with balanced muscle group distribution.
"""

import random
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
    
    def __post_init__(self):
        if self.secondary_muscle_groups is None:
            self.secondary_muscle_groups = []
        if self.equipment is None:
            self.equipment = []


# Exercise database organized by muscle groups
EXERCISES = [
    # Upper Body - Push
    Exercise("Push-ups", "Start in plank position, lower body until chest nearly touches floor, push back up", "chest", ["shoulders", "triceps"], []),
    Exercise("Diamond Push-ups", "Push-ups with hands forming a diamond shape, targets triceps more", "triceps", ["chest", "shoulders"], []),
    Exercise("Pike Push-ups", "Push-ups with hips raised, body forms inverted V, targets shoulders", "shoulders", ["triceps", "core"], []),
    Exercise("Incline Push-ups", "Push-ups with hands elevated on a surface, easier variation", "chest", ["shoulders", "triceps"], ["box"]),
    Exercise("Decline Push-ups", "Push-ups with feet elevated, more challenging", "chest", ["shoulders", "triceps"], ["box"]),
    
    # Upper Body - Pull
    Exercise("Pull-ups", "Hang from bar, pull body up until chin clears bar", "back", ["biceps"], ["pull_up_bar"]),
    Exercise("Chin-ups", "Pull-ups with palms facing you, emphasizes biceps", "biceps", ["back"], ["pull_up_bar"]),
    Exercise("Inverted Rows", "Lie under bar, pull chest to bar while keeping body straight", "back", ["biceps", "core"], ["pull_up_bar"]),
    Exercise("Superman", "Lie face down, lift arms and legs off ground simultaneously", "back", ["glutes"], []),
    
    # Core
    Exercise("Plank", "Hold body in straight line supported on forearms and toes", "core", [], [], False),
    Exercise("Side Plank", "Hold body in straight line supported on one forearm and side of foot", "core", ["obliques"], [], True),
    Exercise("Mountain Climbers", "In plank position, alternate bringing knees to chest rapidly", "core", ["shoulders", "legs"], []),
    Exercise("Bicycle Crunches", "Lie on back, bring opposite elbow to knee in cycling motion", "core", ["obliques"], []),
    Exercise("Russian Twists", "Sit with knees bent, lean back slightly, rotate torso side to side", "core", ["obliques"], []),
    Exercise("Dead Bug", "Lie on back, extend opposite arm and leg while keeping core engaged", "core", [], []),
    Exercise("Hollow Body Hold", "Lie on back, lift shoulders and legs off ground, hold position", "core", [], []),
    Exercise("Leg Raises", "Lie on back, lift legs straight up to 90 degrees, lower slowly", "core", ["hip flexors"], []),
    
    # Lower Body - Quad Dominant
    Exercise("Squats", "Stand with feet shoulder-width, lower hips until thighs parallel to floor", "quads", ["glutes", "core"], []),
    Exercise("Jump Squats", "Squat then explosively jump up, land softly and repeat", "quads", ["glutes", "calves"], []),
    Exercise("Lunges", "Step forward into lunge position, lower back knee toward ground, push back", "quads", ["glutes", "hamstrings"], []),
    Exercise("Reverse Lunges", "Step backward into lunge position, more stable than forward lunges", "quads", ["glutes", "hamstrings"], []),
    Exercise("Walking Lunges", "Perform lunges while moving forward, alternating legs", "quads", ["glutes", "hamstrings"], []),
    Exercise("Bulgarian Split Squats", "Single leg squat with rear foot elevated on surface", "quads", ["glutes"], ["box"], True),
    Exercise("Wall Sit", "Slide down wall until thighs parallel to floor, hold position", "quads", ["glutes"], ["wall"]),
    
    # Lower Body - Hip Dominant
    Exercise("Glute Bridges", "Lie on back, lift hips by squeezing glutes, hold briefly", "glutes", ["hamstrings", "core"], []),
    Exercise("Single Leg Glute Bridge", "Glute bridge performed one leg at a time", "glutes", ["hamstrings", "core"], [], True),
    Exercise("Hip Thrusts", "Similar to glute bridge but with shoulders elevated on surface", "glutes", ["hamstrings"], ["box", "bench"]),
    Exercise("Romanian Deadlifts", "Hinge at hips, lower torso while keeping back straight", "hamstrings", ["glutes", "back"], []),
    Exercise("Good Mornings", "Stand with hands behind head, hinge at hips, lower torso", "hamstrings", ["glutes", "back"], []),
    
    # Lower Body - Calves
    Exercise("Calf Raises", "Stand on toes, raise heels as high as possible, lower slowly", "calves", [], []),
    Exercise("Jumping Jacks", "Jump feet apart while raising arms overhead, return to start", "calves", ["shoulders", "cardio"], []),
    Exercise("Single Leg Calf Raises", "Calf raises performed one leg at a time", "calves", [], [], True),
    
    # Full Body / Cardio
    Exercise("Burpees", "Squat, jump back to plank, do push-up, jump forward, jump up", "full_body", ["cardio"], []),
    Exercise("Jumping Lunges", "Alternate lunges with explosive jumps, switch legs mid-air", "full_body", ["quads", "glutes", "cardio"], []),
    Exercise("High Knees", "Run in place while bringing knees up toward chest", "full_body", ["cardio", "quads"], []),
    Exercise("Butt Kicks", "Run in place while kicking heels toward glutes", "full_body", ["cardio", "hamstrings"], []),
    Exercise("Bear Crawl", "Crawl forward on hands and feet, keeping knees slightly off ground", "full_body", ["core", "shoulders"], []),
    Exercise("Crab Walk", "Sit with hands behind you, lift hips, walk forward or backward", "full_body", ["shoulders", "glutes", "core"], []),
    Exercise("Star Jumps", "Jump up spreading arms and legs wide, return to standing", "full_body", ["cardio", "shoulders"], []),
    
    # Plyometric
    Exercise("Box Jumps", "Jump onto elevated surface, step down, repeat", "quads", ["glutes", "calves", "cardio"], ["box"]),
    Exercise("Tuck Jumps", "Jump up bringing knees to chest, land softly", "quads", ["glutes", "calves", "cardio"], []),
    Exercise("Broad Jumps", "Jump forward as far as possible, land softly", "quads", ["glutes", "calves"], []),
]


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


def generate_circuit(num_exercises: int = 8, avoid_consecutive_overlap: float = 0.5, available_equipment: List[str] = None) -> List[Exercise]:
    """
    Generate a randomized circuit training list with balanced muscle groups.
    
    Args:
        num_exercises: Number of exercises to include in the circuit
        avoid_consecutive_overlap: Maximum allowed overlap between consecutive exercises (0-1)
        available_equipment: List of available equipment (None means all exercises available)
    
    Returns:
        List of Exercise objects in randomized order
    """
    # Filter exercises by available equipment
    if available_equipment is not None:
        exercises_pool = filter_exercises_by_equipment(EXERCISES, available_equipment)
    else:
        exercises_pool = EXERCISES
    
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
        help="Available equipment (space-separated). Options: pull_up_bar, box, bench, wall. "
             "If not specified, all exercises are available. If empty list provided, only bodyweight exercises."
    )
    
    args = parser.parse_args()
    
    # Handle equipment argument
    available_equipment = args.equipment if args.equipment is not None else None
    
    for i in range(args.count):
        if args.count > 1:
            workout_name = f"Circuit Training Workout #{i+1}"
        else:
            workout_name = "Circuit Training Workout"
        
        circuit = generate_circuit(args.num_exercises, args.overlap_threshold, available_equipment)
        print_circuit(circuit, workout_name, args.verbose)
        
        if i < args.count - 1:
            print("\n" + "-"*60 + "\n")


if __name__ == "__main__":
    main()
