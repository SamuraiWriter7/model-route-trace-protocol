#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT_DIR = Path(__file__).resolve().parent.parent

VALIDATION_TARGETS = [
    {
        "name": "Model Route Record",
        "schema": ROOT_DIR / "schemas" / "model-route-record.schema.json",
        "example": ROOT_DIR / "examples" / "model-route-record.example.yaml",
    }
]


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise RuntimeError(f"JSON file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in {path}: {exc}"
        ) from exc


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError:
        raise RuntimeError(f"YAML file not found: {path}") from None
    except yaml.YAMLError as exc:
        raise RuntimeError(
            f"Invalid YAML in {path}: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError(
            f"Expected YAML object at root of {path}"
        )

    return data


def format_error_path(error: Any) -> str:
    if not error.absolute_path:
        return "<root>"

    return ".".join(str(part) for part in error.absolute_path)


def validate_target(
    name: str,
    schema_path: Path,
    example_path: Path,
) -> bool:
    print(f"[validate] {name}")
    print(f"  schema : {schema_path.relative_to(ROOT_DIR)}")
    print(f"  example: {example_path.relative_to(ROOT_DIR)}")

    schema = load_json(schema_path)
    example = load_yaml(example_path)

    Draft202012Validator.check_schema(schema)

    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )

    errors = sorted(
        validator.iter_errors(example),
        key=lambda error: list(error.absolute_path),
    )

    if errors:
        print(f"[failed] {name}")

        for error in errors:
            path = format_error_path(error)
            print(f"  Error: {path}: {error.message}")

        return False

    print(f"[ok] {example_path.name} is valid")
    return True


def main() -> int:
    print("=== Model Route Trace Protocol Validation ===")
    print()

    all_valid = True

    for target in VALIDATION_TARGETS:
        try:
            result = validate_target(
                name=target["name"],
                schema_path=target["schema"],
                example_path=target["example"],
            )
        except RuntimeError as exc:
            print(f"[error] {exc}")
            result = False

        all_valid = all_valid and result
        print()

    if all_valid:
        print("All examples are valid.")
        return 0

    print("Validation failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
