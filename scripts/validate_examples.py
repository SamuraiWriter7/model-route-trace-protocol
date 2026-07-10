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
        "schema": ROOT_DIR
        / "schemas"
        / "model-route-record.schema.json",
        "example": ROOT_DIR
        / "examples"
        / "model-route-record.example.yaml",
        "semantic_validator": None,
    },
    {
        "name": "Provider and Endpoint Binding",
        "schema": ROOT_DIR
        / "schemas"
        / "provider-endpoint-binding.schema.json",
        "example": ROOT_DIR
        / "examples"
        / "provider-endpoint-binding.example.yaml",
        "semantic_validator": None,
    },
    {
        "name": "Route Decision Receipt",
        "schema": ROOT_DIR
        / "schemas"
        / "route-decision-receipt.schema.json",
        "example": ROOT_DIR
        / "examples"
        / "route-decision-receipt.example.yaml",
        "semantic_validator": "route_decision",
    },
]


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise RuntimeError(
            f"JSON file not found: {path}"
        ) from None
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in {path}: {exc}"
        ) from exc


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError:
        raise RuntimeError(
            f"YAML file not found: {path}"
        ) from None
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

    return ".".join(
        str(part)
        for part in error.absolute_path
    )


def validate_route_decision_semantics(
    document: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    candidate_routes = document.get(
        "candidate_routes",
        [],
    )

    selection = document.get(
        "selection",
        {},
    )

    route_ids = [
        route.get("route_id")
        for route in candidate_routes
        if isinstance(route, dict)
    ]

    if len(route_ids) != len(set(route_ids)):
        errors.append(
            "candidate_routes contains duplicate route_id values"
        )

    selected_route_id = selection.get(
        "selected_route_id"
    )

    if selected_route_id not in route_ids:
        errors.append(
            "selection.selected_route_id does not reference "
            "an existing candidate route"
        )

    selected_candidates = [
        route
        for route in candidate_routes
        if route.get("disposition") == "selected"
    ]

    if len(selected_candidates) != 1:
        errors.append(
            "exactly one candidate route must have "
            "disposition='selected'"
        )

    if selected_candidates:
        disposition_route_id = selected_candidates[
            0
        ].get("route_id")

        if disposition_route_id != selected_route_id:
            errors.append(
                "selection.selected_route_id does not match "
                "the candidate marked as selected"
            )

    for route in candidate_routes:
        disposition = route.get("disposition")
        rejection_reasons = route.get(
            "rejection_reasons",
            [],
        )

        if (
            disposition == "selected"
            and rejection_reasons
        ):
            errors.append(
                f"{route.get('route_id')}: selected route "
                "must not contain rejection_reasons"
            )

        if (
            disposition == "rejected"
            and not rejection_reasons
        ):
            errors.append(
                f"{route.get('route_id')}: rejected route "
                "must contain at least one rejection reason"
            )

    return errors


def run_semantic_validation(
    validator_name: str | None,
    document: dict[str, Any],
) -> list[str]:
    if validator_name is None:
        return []

    if validator_name == "route_decision":
        return validate_route_decision_semantics(
            document
        )

    return [
        f"Unknown semantic validator: {validator_name}"
    ]


def validate_target(
    name: str,
    schema_path: Path,
    example_path: Path,
    semantic_validator: str | None,
) -> bool:
    print(f"[validate] {name}")
    print(
        f"  schema : "
        f"{schema_path.relative_to(ROOT_DIR)}"
    )
    print(
        f"  example: "
        f"{example_path.relative_to(ROOT_DIR)}"
    )

    schema = load_json(schema_path)
    example = load_yaml(example_path)

    Draft202012Validator.check_schema(schema)

    validator = Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )

    schema_errors = sorted(
        validator.iter_errors(example),
        key=lambda error: list(
            error.absolute_path
        ),
    )

    semantic_errors = run_semantic_validation(
        semantic_validator,
        example,
    )

    if schema_errors or semantic_errors:
        print(f"[failed] {name}")

        for error in schema_errors:
            path = format_error_path(error)
            print(
                f"  Schema Error: {path}: "
                f"{error.message}"
            )

        for error in semantic_errors:
            print(
                f"  Semantic Error: {error}"
            )

        return False

    print(
        f"[schema-ok] {name}"
    )

    if semantic_validator is not None:
        print(
            f"[semantic-ok] {name}"
        )

    print(
        f"[example-ok] "
        f"{example_path.name}"
    )

    return True


def main() -> int:
    print(
        "=== Model Route Trace Protocol Validation ==="
    )
    print()

    all_valid = True

    for target in VALIDATION_TARGETS:
        try:
            result = validate_target(
                name=target["name"],
                schema_path=target["schema"],
                example_path=target["example"],
                semantic_validator=target[
                    "semantic_validator"
                ],
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
