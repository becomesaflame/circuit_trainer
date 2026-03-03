# Interval Trainer

Generate randomized circuit training workouts from a YAML exercise library, with:
- muscle-group-aware ordering
- equipment filtering
- optional ankle-impact filtering
- automatic left/right pairing for side-specific movements
- interactive per-exercise re-rolls

## Requirements

- Python 3.10+ (tested with Python 3.12)
- `PyYAML`

Install dependency:

```bash
python3 -m pip install pyyaml
```

## Files

- `interval-trainer.py` - main script
- `exercises.yaml` - exercise database and metadata
- `test_circuit_trainer.py` - test suite

## Basic Usage

Generate one workout with default settings:

```bash
python3 interval-trainer.py
```

Generate a 12-exercise workout:

```bash
python3 interval-trainer.py -n 12
```

Generate 3 different workouts:

```bash
python3 interval-trainer.py -c 3
```

Use verbose output:

```bash
python3 interval-trainer.py -v
```

## Command-Line Options

- `-n, --num-exercises`  
  Number of exercises to generate (default from local config, initial value: `10`)
- `-o, --overlap-threshold`  
  Max allowed muscle-group overlap between consecutive exercises, from `0` to `1` (default from local config, initial value: `0.5`)
- `-c, --count`  
  Number of different circuits to generate (default from local config, initial value: `1`)
- `-v, --verbose` / `--no-verbose`  
  Enable or disable detailed multi-line output per exercise
- `-e, --equipment`  
  Space-separated available equipment (examples: `pull_up_bar box bench wall weight`)
  When omitted, value comes from local config. Initial default is bodyweight-only (`[]`).
- `--all-equipment`  
  Allow all exercises regardless of equipment requirements (stores `equipment: null` in config)
- `--bodyweight-only`  
  Force bodyweight-only workouts (stores `equipment: []` in config)
- `--no-ankle-impact`  
  Exclude exercises marked with ankle impact (jumping/running style moves)
- `--allow-ankle-impact`  
  Allow ankle-impact exercises

Example with filters:

```bash
python3 interval-trainer.py -n 10 -e pull_up_bar box --no-ankle-impact
```

## Local Config Defaults

The script stores defaults in a local config file:

- `.interval-trainer.config.yaml` (created automatically in the project folder)

Behavior:
- If no config file exists, it is created with program defaults.
- Program default for equipment is bodyweight-only.
- Whenever you pass CLI options, those values are written to the local config file.
- Future runs use the saved config values as defaults.

Examples:

```bash
# Set preferred defaults for future runs
python3 interval-trainer.py -n 12 --all-equipment --no-ankle-impact

# Next run uses those saved defaults, even without flags
python3 interval-trainer.py
```

## Interactive Re-roll Feature

After a workout is printed (in an interactive terminal), the script asks:

`Enter exercise number to reroll (press Enter to keep this workout):`

- Enter a number (for example `4`) to re-roll that exercise.
- Press Enter with no input to keep the workout and continue.
- If the selected exercise is part of a left/right pair, both sides are re-rolled together.

Notes:
- Re-roll keeps the same number of slots.
- Re-roll respects the same equipment and ankle-impact filters used to build the workout.

## Side-Specific Exercises

Exercises marked `side_specific: true` in `exercises.yaml` are added as a pair:
- `Left <Exercise Name>`
- `Right <Exercise Name>`

These paired entries count as two workout slots.

## Running Tests

Run tests with:

```bash
python3 test_circuit_trainer.py
```

Or with pytest (if installed):

```bash
python3 -m pytest test_circuit_trainer.py -v
```

