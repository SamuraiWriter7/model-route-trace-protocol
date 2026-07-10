#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Callable

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
    {
        "name": "Unified Model Route Trace Lifecycle",
        "schema": ROOT_DIR
        / "schemas"
        / "unified-model-route-trace-lifecycle.schema.json",
        "example": ROOT_DIR
        / "examples"
        / "unified-model-route-trace-lifecycle.example.yaml",
        "semantic_validator": "unified_lifecycle",
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
        candidate_id = selected_candidates[0].get(
            "route_id"
        )

        if candidate_id != selected_route_id:
            errors.append(
                "selection.selected_route_id does not "
                "match the candidate marked selected"
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
                "contain rejection_reasons"
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
                f"{edge_id}: unknown from_node "
                f"'{from_node}'"
            )

        if to_node not in node_id_set:
            errors.append(
                f"{edge_id}: unknown to_node "
                f"'{to_node}'"
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
                f"unknown entry node '{node_id}'"
            )
        elif indegree.get(node_id, 0) != 0:
            errors.append(
                f"entry node '{node_id}' has "
                "incoming edges"
            )

    for node_id in terminal_node_ids:
        if node_id not in node_id_set:
            errors.append(
                f"unknown terminal node '{node_id}'"
            )
        elif outdegree.get(node_id, 0) != 0:
            errors.append(
                f"terminal node '{node_id}' has "
                "outgoing edges"
            )

    if has_cycle(
        node_id_set,
        adjacency,
        indegree,
    ):
        errors.append(
            "route graph contains a cycle"
        )

    valid_entries = [
        node_id
        for node_id in entry_node_ids
        if node_id in node_id_set
    ]

    if valid_entries:
        reachable = reachable_nodes(
            valid_entries,
            adjacency,
        )

        unreachable = node_id_set - reachable

        if unreachable:
            errors.append(
                "nodes unreachable from entry nodes: "
                + ", ".join(sorted(unreachable))
            )

    valid_terminals = [
        node_id
        for node_id in terminal_node_ids
        if node_id in node_id_set
    ]

    if valid_terminals:
        reaches_terminal = reachable_nodes(
            valid_terminals,
            reverse_adjacency,
        )

        dead_ends = node_id_set - reaches_terminal

        if dead_ends:
            errors.append(
                "nodes unable to reach terminal: "
                + ", ".join(sorted(dead_ends))
            )

    metrics = document.get(
        "graph_metrics",
        {},
    )

    if (
        "node_count" in metrics
        and metrics["node_count"] != len(nodes)
    ):
        errors.append(
            "graph_metrics.node_count mismatch"
        )

    if (
        "edge_count" in metrics
        and metrics["edge_count"] != len(edges)
    ):
        errors.append(
            "graph_metrics.edge_count mismatch"
        )

    return errors


def validate_unified_lifecycle_semantics(
    document: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    required_phases = {
        "origin",
        "decision",
        "binding",
        "placement",
        "execution",
        "route_graph",
        "artifact",
        "trace_integrity",
        "audit_readiness",
        "royalty_readiness",
    }

    phases = document.get(
        "lifecycle_phases",
        [],
    )

    phase_names = [
        phase.get("phase")
        for phase in phases
        if isinstance(phase, dict)
    ]

    if len(phase_names) != len(set(phase_names)):
        errors.append(
            "lifecycle_phases contains duplicate phases"
        )

    missing_phases = (
        required_phases - set(phase_names)
    )

    if missing_phases:
        errors.append(
            "missing lifecycle phases: "
            + ", ".join(sorted(missing_phases))
        )

    trace_integrity = document.get(
        "trace_integrity",
        {},
    )

    integrity_links = [
        trace_integrity.get("origin_link_complete"),
        trace_integrity.get("decision_link_complete"),
        trace_integrity.get("binding_link_complete"),
        trace_integrity.get("placement_link_complete"),
        trace_integrity.get("execution_link_complete"),
        trace_integrity.get("graph_link_complete"),
        trace_integrity.get("artifact_link_complete"),
    ]

    integrity_status = trace_integrity.get(
        "overall_status"
    )

    if (
        integrity_status == "complete"
        and not all(integrity_links)
    ):
        errors.append(
            "trace_integrity.overall_status cannot be "
            "'complete' while one or more links are incomplete"
        )

    audit = document.get(
        "audit_readiness",
        {},
    )

    audit_checks = [
        audit.get("route_decision_auditable"),
        audit.get("provider_path_auditable"),
        audit.get("placement_auditable"),
        audit.get("cross_agent_path_auditable"),
        audit.get("artifact_lineage_auditable"),
    ]

    if (
        audit.get("overall_status") == "ready"
        and not all(audit_checks)
    ):
        errors.append(
            "audit_readiness cannot be 'ready' while "
            "one or more auditability checks are false"
        )

    royalty = document.get(
        "royalty_readiness",
        {},
    )

    royalty_checks = [
        royalty.get("origin_attribution_ready"),
        royalty.get("agent_contribution_path_ready"),
        royalty.get("model_route_path_ready"),
        royalty.get("tool_contribution_path_ready"),
        royalty.get("human_contribution_path_ready"),
        royalty.get("artifact_binding_ready"),
    ]

    if (
        royalty.get("overall_status") == "ready"
        and not all(royalty_checks)
    ):
        errors.append(
            "royalty_readiness cannot be 'ready' while "
            "one or more readiness checks are false"
        )

    if document.get("status") == "completed":
        incomplete_phases = [
            phase.get("phase")
            for phase in phases
            if phase.get("status")
            not in {"completed", "skipped"}
        ]

        if incomplete_phases:
            errors.append(
                "completed lifecycle contains incomplete phases: "
                + ", ".join(
                    sorted(
                        phase
                        for phase in incomplete_phases
                        if phase is not None
                    )
                )
            )

    return errors


def run_semantic_validation(
    validator_name: str | None,
    document: dict[str, Any],
) -> list[str]:
    validators: dict[
        str,
        Callable[[dict[str, Any]], list[str]],
    ] = {
        "route_decision":
            validate_route_decision_semantics,
        "route_graph":
            validate_route_graph_semantics,
        "unified_lifecycle":
            validate_unified_lifecycle_semantics,
    }

    if validator_name is None:
        return []

    validator = validators.get(validator_name)

    if validator is None:
        return [
            f"Unknown semantic validator: "
            f"{validator_name}"
        ]

    return validator(document)


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


def validate_cross_record_references() -> list[str]:
    errors: list[str] = []

    model_route = load_yaml(
        ROOT_DIR
        / "examples"
        / "model-route-record.example.yaml"
    )

    provider_binding = load_yaml(
        ROOT_DIR
        / "examples"
        / "provider-endpoint-binding.example.yaml"
    )

    route_decision = load_yaml(
        ROOT_DIR
        / "examples"
        / "route-decision-receipt.example.yaml"
    )

    route_graph = load_yaml(
        ROOT_DIR
        / "examples"
        / "cross-agent-model-route-graph.example.yaml"
    )

    lifecycle = load_yaml(
        ROOT_DIR
        / "examples"
        / "unified-model-route-trace-lifecycle.example.yaml"
    )

    lifecycle_decision_ref = lifecycle[
        "decision"
    ]["route_decision_ref"]

    if (
        lifecycle_decision_ref
        != route_decision["route_decision_id"]
    ):
        errors.append(
            "lifecycle decision reference does not "
            "match Route Decision Receipt"
        )

    lifecycle_graph_ref = lifecycle[
        "route_graph"
    ]["route_graph_ref"]

    if lifecycle_graph_ref != route_graph["graph_id"]:
        errors.append(
            "lifecycle graph reference does not "
            "match Cross-Agent Model Route Graph"
        )

    binding_refs = set(
        lifecycle["bindings"][
            "provider_binding_refs"
        ]
    )

    if (
        provider_binding["binding_id"]
        not in binding_refs
    ):
        errors.append(
            "lifecycle does not include the example "
            "Provider Endpoint Binding"
        )

    route_trace_refs = set(
        lifecycle["execution"][
            "route_trace_refs"
        ]
    )

    if (
        model_route["route_trace_id"]
        not in route_trace_refs
    ):
        errors.append(
            "lifecycle does not include the example "
            "Model Route Record"
        )

    if (
        lifecycle["task_ref"]
        != route_decision["task_ref"]
    ):
        errors.append(
            "task_ref mismatch between lifecycle "
            "and Route Decision Receipt"
        )

    if (
        lifecycle["task_ref"]
        != route_graph["task_ref"]
    ):
        errors.append(
            "task_ref mismatch between lifecycle "
            "and Route Graph"
        )

    return errors


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

    print("[validate] Cross-record references")

    try:
        reference_errors = (
            validate_cross_record_references()
        )
    except RuntimeError as exc:
        print(f"[error] {exc}")
        reference_errors = [str(exc)]

    if reference_errors:
        all_valid = False

        for error in reference_errors:
            print(
                f"  Reference Error: {error}"
            )
    else:
        print(
            "[reference-ok] "
            "Cross-record references are consistent"
        )

    print()

    if all_valid:
        print("All examples are valid.")
        return 0

    print("Validation failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
