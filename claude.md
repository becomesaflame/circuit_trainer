# Cursor Rules for Interval Trainer Project

## Testing Requirements

**IMPORTANT: Keep tests updated with every code change**

- All code changes must include corresponding test updates
- Run tests after every code modification: `python3 -m pytest test_circuit_trainer.py -v` or `python3 test_circuit_trainer.py`
- Tests should cover all features including:
  - Exercise dataclass functionality
  - Muscle group overlap calculations
  - Equipment filtering
  - Side-specific exercise pairing
  - Circuit generation with various parameters
  - Output formatting (verbose and non-verbose)
  - Edge cases and error handling
- When adding new features, add corresponding tests
- When modifying existing features, update relevant tests
- Ensure all tests pass before committing changes

## Code Quality

- Follow Python best practices and PEP 8 style guide
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and testable

## Project Structure

- Exercise data is stored in `exercises.yaml`
- Main script: `circuit_trainer.py`
- Tests: `test_circuit_trainer.py`
- Always update tests when modifying code
