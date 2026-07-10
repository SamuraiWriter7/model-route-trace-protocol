#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
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
    {
        "name": "Cross-Agent Model Route Graph",
        "schema": ROOT_DIR
        / "schemas"
        / "cross-agent-model-route-graph.schema.json",
        "example": ROOT_DIR
        / "examples"
        / "cross-agent-model-route-graph.example.yaml",
        "semantic_validator": "route_graph",
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
            "candidate_routes contains duplicate "
            "route_id values"
        )

    selected_route_id = selection.get(
        "selected_route_id"
    )

    if selected_route_id not in route_ids:
        errors.append(
            "selection.selected_route_id does not "
            "reference an existing candidate route"
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
                "selection.selected_route_id does not "
                "match the selected candidate"
            )

    for route in candidate_routes:
        route_id = route.get(
            "route_id",
            "<unknown>",
        )

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
                f"{route_id}: selected route must not "
                "contain rejection_reasons"
            )

        if (
            disposition == "rejected"
            and not rejection_reasons
        ):
            errors.append(
                f"{route_id}: rejected route must "
                "contain at least one rejection reason"
            )

    return errors


def reachable_nodes(
    start_nodes: list[str],
    adjacency: dict[str, list[str]],
) -> set[str]:
    visited: set[str] = set()

    queue: deque[str] = deque(start_nodes)

    while queue:
        current = queue.popleft()

        if current in visited:
            continue

        visited.add(current)

        for next_node in adjacency.get(
            current,
            [],
        ):
            if next_node not in visited:
                queue.append(next_node)

    return visited


def has_cycle(
    node_ids: set[str],
    adjacency: dict[str, list[str]],
    indegree: dict[str, int],
) -> bool:
    working_indegree = {
        node_id: indegree.get(node_id, 0)
        for node_id in node_ids
    }

    queue: deque[str] = deque(
        node_id
        for node_id in node_ids
        if working_indegree[node_id] == 0
    )

    visited_count = 0

    while queue:
        node_id = queue.popleft()

        visited_count += 1

        for next_node in adjacency.get(
            node_id,
            [],
        ):
            working_indegree[next_node] -= 1

            if working_indegree[next_node] == 0:
                queue.append(next_node)

    return visited_count != len(node_ids)


def validate_route_graph_semantics(
    document: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    nodes = document.get("nodes", [])
    edges = document.get("edges", [])

    entry_node_ids = document.get(
        "entry_node_ids",
        [],
    )

    terminal_node_ids = document.get(
        "terminal_node_ids",
        [],
    )

    node_ids = [
        node.get("node_id")
        for node in nodes
        if isinstance(node, dict)
    ]

    edge_ids = [
        edge.get("edge_id")
        for edge in edges
        if isinstance(edge, dict)
    ]

    if len(node_ids) != len(set(node_ids)):
        errors.append(
            "nodes contains duplicate node_id values"
        )

    if len(edge_ids) != len(set(edge_ids)):
        errors.append(
            "edges contains duplicate edge_id values"
        )

    node_id_set = set(node_ids)

    adjacency: dict[str, list[str]] = defaultdict(
        list
    )

    reverse_adjacency: dict[
        str,
        list[str],
    ] = defaultdict(list)

    indegree: dict[str, int] = defaultdict(int)

    outdegree: dict[str, int] = defaultdict(int)

    for edge in edges:
        edge_id = edge.get(
            "edge_id",
            "<unknown>",
        )

        from_node = edge.get("from_node")
        to_node = edge.get("to_node")

        if from_node not in node_id_set:
            errors.append(
                f"{edge_id}: from_node references "
                f"unknown node '{from_node}'"
            )

        if to_node not in node_id_set:
            errors.append(
                f"{edge_id}: to_node references "
                f"unknown node '{to_node}'"
            )

        if from_node == to_node:
            errors.append(
                f"{edge_id}: self-loop is not allowed"
            )

        if (
            from_node in node_id_set
            and to_node in node_id_set
        ):
            adjacency[from_node].append(to_node)

            reverse_adjacency[to_node].append(
                from_node
            )

            indegree[to_node] += 1
            outdegree[from_node] += 1

    for node_id in entry_node_ids:
        if node_id not in node_id_set:
            errors.append(
                f"entry_node_ids references unknown "
                f"node '{node_id}'"
            )
            continue

        if indegree.get(node_id, 0) != 0:
            errors.append(
                f"entry node '{node_id}' has incoming edges"
            )

    for node_id in terminal_node_ids:
        if node_id not in node_id_set:
            errors.append(
                f"terminal_node_ids references unknown "
                f"node '{node_id}'"
            )
            continue

        if outdegree.get(node_id, 0) != 0:
            errors.append(
                f"terminal node '{node_id}' has outgoing edges"
            )

    if has_cycle(
        node_id_set,
        adjacency,
        indegree,
    ):
        errors.append(
            "route graph contains at least one cycle; "
            "v0.4 graphs must be DAGs"
        )

    valid_entry_nodes = [
        node_id
        for node_id in entry_node_ids
        if node_id in node_id_set
    ]

    if valid_entry_nodes:
        reachable_from_entries = reachable_nodes(
            valid_entry_nodes,
            adjacency,
        )

        unreachable_nodes = (
            node_id_set - reachable_from_entries
        )

        if unreachable_nodes:
            errors.append(
                "nodes unreachable from entry nodes: "
                + ", ".join(
                    sorted(unreachable_nodes)
                )
            )

    valid_terminal_nodes = [
        node_id
        for node_id in terminal_node_ids
        if node_id in node_id_set
    ]

    if valid_terminal_nodes:
        reaches_terminal = reachable_nodes(
            valid_terminal_nodes,
            reverse_adjacency,
        )

        dead_end_nodes = (
            node_id_set - reaches_terminal
        )

        if dead_end_nodes:
            errors.append(
                "nodes that cannot reach a terminal node: "
                + ", ".join(
                    sorted(dead_end_nodes)
                )
            )

    parallel_groups = document.get(
        "parallel_groups",
        [],
    )

    for group in parallel_groups:
        group_id = group.get(
            "group_id",
            "<unknown>",
        )

        for member_node_id in group.get(
            "member_node_ids",
            [],
        ):
            if member_node_id not in node_id_set:
                errors.append(
                    f"{group_id}: member_node_ids "
                    f"references unknown node "
                    f"'{member_node_id}'"
                )

        join_node_id = group.get("join_node_id")

        if (
            join_node_id is not None
            and join_node_id not in node_id_set
        ):
            errors.append(
                f"{group_id}: join_node_id references "
                f"unknown node '{join_node_id}'"
            )

    graph_metrics = document.get(
        "graph_metrics",
        {},
    )

    if (
        "node_count" in graph_metrics
        and graph_metrics["node_count"] != len(nodes)
    ):
        errors.append(
            "graph_metrics.node_count does not match "
            "the actual number of nodes"
        )

    if (
        "edge_count" in graph_metrics
        and graph_metrics["edge_count"] != len(edges)
    ):
        errors.append(
            "graph_metrics.edge_count does not match "
            "the actual number of edges"
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

    if validator_name == "route_graph":
        return validate_route_graph_semantics(
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

    print(f"[schema-ok] {name}")

    if semantic_validator is not None:
        print(f"[semantic-ok] {name}")

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
