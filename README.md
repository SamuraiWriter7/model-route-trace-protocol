# Model Route Trace Protocol

**A protocol for recording and auditing how AI tasks traverse agents, models, providers, compute environments, trust boundaries, and artifact-generation paths.**

`model-route-trace-protocol` defines interoperable records for tracing how an AI task moves through a distributed execution environment.

The protocol is designed for a world where a single task may pass through:

* multiple agents,
* multiple model families,
* BYOK providers,
* local runtimes,
* enterprise endpoints,
* edge or on-premise compute,
* retrieval systems,
* tools,
* policy boundaries,
* human review gates,
* and final artifact-generation stages.

The protocol does not assume that one application is permanently bound to one model or one cloud provider.

Instead, it records:

> **Which route was considered, why a route was selected, which provider and endpoint were used, where execution occurred, how multiple agents interacted, and whether the resulting lineage is ready for audit and downstream attribution.**

---

## Why This Protocol Exists

AI systems are moving from fixed execution paths toward dynamic routing.

A modern AI task may follow a path such as:

```text
Human Request
      │
      ▼
Routing Agent
      │
      ├── Local Small Model
      │
      ├── Enterprise Endpoint
      │
      └── Frontier Model
              │
              ▼
         Analyst Agent
              │
        ┌─────┴─────┐
        ▼           ▼
    Verifier     Boundary
        │           │
        └─────┬─────┘
              ▼
          Human Gate
              │
              ▼
           Artifact
```

Traditional logs often record only that a model was called.

That is no longer enough.

In a multi-model and multi-agent environment, important questions include:

* Why was this route selected?
* Which alternatives were rejected?
* Which provider handled the request?
* Which endpoint and trust domain were crossed?
* Where did computation physically or logically occur?
* Which agent handed work to which agent?
* Where did parallel branches split and merge?
* Which artifact resulted from the route?
* Is the lineage complete enough for audit?
* Is attribution evidence sufficient for a downstream royalty or contribution system?

The Model Route Trace Protocol provides records for answering these questions.

---

# Core Principle

The protocol separates five different concerns:

```text
Decision
   ↓
Binding
   ↓
Execution
   ↓
Graph
   ↓
Lifecycle
```

Each concern is represented by an independent record.

This separation allows systems to inspect planned routes, actual routes, provider boundaries, multi-agent execution graphs, and lifecycle integrity without collapsing them into one oversized log object.

---

# First Arc

The first protocol arc consists of five versions.

## v0.1 — Model Route Record

Records:

> **What route segment actually executed?**

It captures the minimum execution lineage:

```text
Task
  ↓
Agent
  ↓
Model
  ↓
Provider
  ↓
Execution Environment
  ↓
Artifact
```

Primary schema:

```text
schemas/model-route-record.schema.json
```

Primary example:

```text
examples/model-route-record.example.yaml
```

---

## v0.2 — Provider and Endpoint Binding

Records:

> **Which provider, endpoint, trust boundary, data boundary, authentication mode, and network path were associated with the route?**

The binding layer separates model identity from execution path.

The same model family may be accessed through:

* managed cloud APIs,
* enterprise tenants,
* private endpoints,
* self-hosted runtimes,
* local inference engines,
* OpenAI-compatible gateways,
* isolated or air-gapped environments.

The protocol records the relationship without storing secret material.

Primary schema:

```text
schemas/provider-endpoint-binding.schema.json
```

Primary example:

```text
examples/provider-endpoint-binding.example.yaml
```

---

## v0.3 — Route Decision Receipt

Records:

> **Why was one route selected instead of another?**

The receipt preserves:

* candidate routes,
* capability assessments,
* latency assessments,
* cost assessments,
* energy assessments,
* policy results,
* rejection reasons,
* route selection reasons,
* minimum-sufficient-compute checks,
* local-first checks,
* escalation decisions.

Example:

```text
Local SLM
  └── rejected: insufficient capability

Enterprise Endpoint
  └── selected: capability and boundary requirements satisfied

Public Frontier Model
  └── rejected: data boundary violation and cost limit exceeded
```

Primary schema:

```text
schemas/route-decision-receipt.schema.json
```

Primary example:

```text
examples/route-decision-receipt.example.yaml
```

---

## v0.4 — Cross-Agent Model Route Graph

Records:

> **How did execution branch, hand off, run in parallel, and merge across agents and models?**

The record represents execution as a directed acyclic graph.

Example:

```text
                    ┌── Verifier ──┐
Origin → Router → Analyst           ├→ Human Gate → Artifact
                    └── Boundary ──┘
```

Graph nodes may represent:

* origin traces,
* routers,
* agent executions,
* model executions,
* retrieval stages,
* tool executions,
* boundary checks,
* human gates,
* artifacts.

Graph edges may represent:

* routing,
* handoff,
* context transfer,
* evidence transfer,
* verification,
* boundary checks,
* approval dependencies,
* merges,
* artifact production,
* fallback paths.

Primary schema:

```text
schemas/cross-agent-model-route-graph.schema.json
```

Primary example:

```text
examples/cross-agent-model-route-graph.example.yaml
```

---

## v0.5 — Unified Model Route Trace Lifecycle

Records:

> **Is the entire path from origin to artifact complete, auditable, and ready for downstream attribution analysis?**

The lifecycle connects:

```text
Origin
  ↓
Route Decision
  ↓
Provider Binding
  ↓
Compute Placement
  ↓
Model Execution
  ↓
Cross-Agent Graph
  ↓
Artifact
  ↓
Trace Integrity
  ↓
Audit Readiness
  ↓
Royalty Readiness
```

The lifecycle does not calculate payments or contribution percentages.

Its responsibility is to determine whether sufficient evidence exists for downstream audit and attribution systems.

Primary schema:

```text
schemas/unified-model-route-trace-lifecycle.schema.json
```

Primary example:

```text
examples/unified-model-route-trace-lifecycle.example.yaml
```

---

# Repository Structure

```text
model-route-trace-protocol/
├── README.md
├── CHANGELOG.md
├── LICENSE
├── requirements.txt
│
├── schemas/
│   ├── model-route-record.schema.json
│   ├── provider-endpoint-binding.schema.json
│   ├── route-decision-receipt.schema.json
│   ├── cross-agent-model-route-graph.schema.json
│   └── unified-model-route-trace-lifecycle.schema.json
│
├── examples/
│   ├── model-route-record.example.yaml
│   ├── provider-endpoint-binding.example.yaml
│   ├── route-decision-receipt.example.yaml
│   ├── cross-agent-model-route-graph.example.yaml
│   └── unified-model-route-trace-lifecycle.example.yaml
│
├── scripts/
│   └── validate_examples.py
│
└── .github/
    └── workflows/
        └── validate.yml
```

---

# Protocol Architecture

The protocol separates planning, execution, topology, and lifecycle accountability.

```text
                 ┌───────────────────────┐
                 │        Origin         │
                 └───────────┬───────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │ Route Decision Receipt│
                 └───────────┬───────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
    ┌────────────────────┐    ┌────────────────────┐
    │ Provider Binding   │    │ Compute Placement  │
    └──────────┬─────────┘    └──────────┬─────────┘
               └────────────┬─────────────┘
                            ▼
                 ┌───────────────────────┐
                 │  Model Route Records  │
                 └───────────┬───────────┘
                             ▼
                 ┌───────────────────────┐
                 │ Cross-Agent Graph     │
                 └───────────┬───────────┘
                             ▼
                 ┌───────────────────────┐
                 │       Artifact        │
                 └───────────┬───────────┘
                             ▼
                 ┌───────────────────────┐
                 │   Trace Integrity     │
                 └───────────┬───────────┘
                             ▼
                 ┌───────────────────────┐
                 │   Audit Readiness     │
                 └───────────┬───────────┘
                             ▼
                 ┌───────────────────────┐
                 │  Royalty Readiness    │
                 └───────────────────────┘
```

---

# Record Relationships

## Model Route Record

Represents an actual execution segment.

```text
Route Trace ID
   ├── Task
   ├── Agent
   ├── Model
   ├── Provider
   ├── Execution Environment
   ├── Input Trace
   └── Output Artifact
```

---

## Provider and Endpoint Binding

Represents the execution boundary associated with a route.

```text
Binding
   ├── Provider
   ├── Endpoint
   ├── Trust Boundary
   ├── Data Boundary
   ├── Authentication Mode
   └── Network Path
```

---

## Route Decision Receipt

Represents the decision process preceding execution.

```text
Task Context
     │
     ▼
Constraints
     │
     ▼
Candidate Routes
     │
     ├── Capability
     ├── Latency
     ├── Cost
     ├── Energy
     └── Policy
     │
     ▼
Selected Route
```

---

## Cross-Agent Model Route Graph

Represents distributed execution topology.

```text
Nodes = workers, checks, gates, tools, artifacts
Edges = routing, handoffs, evidence, verification, merges
```

The graph is validated as a DAG in v0.4.

---

## Unified Lifecycle

Represents cross-record continuity.

```text
Origin
→ Decision
→ Binding
→ Placement
→ Execution
→ Graph
→ Artifact
→ Integrity
→ Audit Readiness
→ Royalty Readiness
```

---

# Validation

The repository includes schema validation and semantic validation.

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run validation:

```bash
python scripts/validate_examples.py
```

Expected successful result:

```text
=== Model Route Trace Protocol Validation ===

[validate] Model Route Record
[schema-ok] Model Route Record
[example-ok] model-route-record.example.yaml

[validate] Provider and Endpoint Binding
[schema-ok] Provider and Endpoint Binding
[example-ok] provider-endpoint-binding.example.yaml

[validate] Route Decision Receipt
[schema-ok] Route Decision Receipt
[semantic-ok] Route Decision Receipt
[example-ok] route-decision-receipt.example.yaml

[validate] Cross-Agent Model Route Graph
[schema-ok] Cross-Agent Model Route Graph
[semantic-ok] Cross-Agent Model Route Graph
[example-ok] cross-agent-model-route-graph.example.yaml

[validate] Unified Model Route Trace Lifecycle
[schema-ok] Unified Model Route Trace Lifecycle
[semantic-ok] Unified Model Route Trace Lifecycle
[example-ok] unified-model-route-trace-lifecycle.example.yaml

[validate] Cross-record references
[reference-ok] Cross-record references are consistent

All examples are valid.
```

---

# Semantic Validation

JSON Schema validates document structure.

The protocol also requires semantic checks.

## Route Decision checks

The validator verifies:

* candidate route IDs are unique,
* the selected route exists,
* exactly one route is marked as selected,
* the selected route ID matches the selected candidate,
* rejected routes contain rejection reasons,
* selected routes do not contain rejection reasons.

---

## Route Graph checks

The validator verifies:

* node IDs are unique,
* edge IDs are unique,
* edge references resolve to existing nodes,
* self-loops are prohibited,
* entry nodes have no incoming edges,
* terminal nodes have no outgoing edges,
* the graph contains no cycle,
* all nodes are reachable from an entry node,
* all nodes can reach a terminal node,
* graph metrics match actual node and edge counts.

---

## Lifecycle checks

The validator verifies:

* required lifecycle phases are present,
* lifecycle phases are unique,
* complete trace integrity requires all major links to be complete,
* audit readiness cannot be `ready` when an auditability check is false,
* royalty readiness cannot be `ready` when a required contribution path is unresolved,
* a completed lifecycle cannot contain unfinished required phases.

---

# Cross-Record Validation

v0.5 introduces validation across protocol records.

Examples include:

```text
Lifecycle.route_decision_ref
        =
RouteDecisionReceipt.route_decision_id
```

```text
Lifecycle.route_graph_ref
        =
CrossAgentModelRouteGraph.graph_id
```

```text
Lifecycle.route_trace_refs
        contains
ModelRouteRecord.route_trace_id
```

The purpose is to prevent structurally valid but disconnected evidence collections.

---

# Security Principle

## Never store secret material

The protocol records authentication mode and non-secret configuration references.

Example:

```yaml
authentication:
  auth_mode: "managed_identity"
  credential_ref: "auth-profile-ai-prod-03"
  secret_material_recorded: false
```

The following must not be embedded in protocol records:

* API keys,
* passwords,
* access tokens,
* private keys,
* session secrets,
* credentials embedded in endpoint URLs.

The protocol records:

> **which authentication mechanism was used**

not:

> **the authentication secret itself**

---

# Design Principles

## 1. Record routes, not vendor assumptions

The protocol is provider-neutral.

It may be used with:

* hosted frontier models,
* enterprise AI platforms,
* local inference runtimes,
* self-hosted model servers,
* OpenAI-compatible endpoints,
* edge inference,
* private cloud deployments,
* multi-agent orchestration systems.

---

## 2. Separate decision from execution

A planned route may differ from the route that actually executed.

Example:

```text
Planned Route
Enterprise Endpoint
      │
      X unavailable
      │
      ▼
Fallback Route
Local Model
```

Decision records and execution records must therefore remain separate.

---

## 3. Preserve rejected alternatives

A selected route alone does not explain why the route was reasonable.

The protocol preserves candidate routes and rejection reasons.

This enables later analysis of:

* policy compliance,
* cost efficiency,
* energy efficiency,
* local-first adherence,
* escalation necessity,
* fallback quality.

---

## 4. Prefer minimum sufficient compute

The protocol can record whether:

* local-first execution was checked,
* a smaller model was considered,
* escalation was required,
* the selected route represented minimum sufficient compute.

This connects route tracing with computational efficiency and Computational Pranayama principles.

---

## 5. Represent distributed execution as a graph

Multi-agent systems are not always linear pipelines.

The protocol therefore supports:

* parallel branches,
* review branches,
* merge points,
* fallback paths,
* human escalation,
* evidence convergence.

---

## 6. Separate audit readiness from royalty readiness

An execution path may be fully auditable while attribution remains incomplete.

Example:

```text
Audit Ready: Yes
Royalty Ready: No
```

This may occur when:

* human contribution boundaries remain unresolved,
* external data rights are unclear,
* contribution weights are not determined,
* tool ownership attribution is incomplete.

The protocol preserves this distinction.

---

# Relationship to Adjacent Protocols

This protocol can reference or bridge to adjacent specifications.

## Compute Placement Receipt

Answers:

> Why was computation placed on this node or environment?

---

## Agent Handoff Record

Answers:

> What responsibility, context, or evidence was transferred between agents?

---

## Trace Relay Protocol

Answers:

> What trace was inherited, transformed, and passed forward?

---

## Origin Trace Receipt

Answers:

> What is the originating trace or source structure?

---

## Origin and Royalty Audit Systems

Answer:

> How does origin and contribution evidence connect to downstream value circulation?

---

# Civilizational Position

The protocol is based on a structural transition:

```text
Compute Ownership
        ↓
Compute Placement
        ↓
Model Routing
        ↓
Agent Coordination
        ↓
Trace Accountability
        ↓
Auditability
        ↓
Value Circulation
```

In fixed-model systems, knowing the application name may have been enough to infer the execution path.

In multi-model systems, that assumption no longer holds.

A single application may route work across:

```text
Local Model
Enterprise Model
Private Endpoint
Frontier Model
Retrieval System
Tool Agent
Verifier Agent
Human Gate
```

The core question becomes:

> **How did intelligence move?**

The Model Route Trace Protocol treats that movement as a first-class auditable object.

---

# Non-Goals

The first arc does not define:

* model benchmarking methodology,
* billing calculation,
* royalty percentage calculation,
* legal ownership determination,
* cryptographic signature infrastructure,
* model quality ranking,
* universal agent identity infrastructure,
* provider-specific API configuration.

The protocol records evidence and readiness states.

Downstream systems may use that evidence for audit, governance, optimization, attribution, or economic settlement.

---

# Status

The first protocol arc is complete through:

```text
v0.5 — Unified Model Route Trace Lifecycle
```

The first arc establishes:

```text
Record
→ Bind
→ Decide
→ Graph
→ Unify
```

Future work may be developed as separate protocol families for:

* model route policy,
* route cost and energy audit,
* route deviation and fallback analysis,
* model route attribution,
* royalty bridge integration.

---

# License

See the repository `LICENSE` file.

---

# Summary

`model-route-trace-protocol` provides a structured way to answer:

```text
Where did the task begin?
Why was this route selected?
Which alternatives were rejected?
Which provider and endpoint were used?
Which trust boundaries were crossed?
Where did computation occur?
Which agents participated?
Where did execution branch and merge?
Which artifact was produced?
Is the lineage complete?
Is the system ready for audit?
Is contribution evidence ready for downstream attribution?
```

The protocol is designed for an AI environment where intelligence is no longer located in one model, one provider, or one data center.

> **The central problem is no longer only who owns intelligence.
> The problem is how intelligence moves, where it is placed, and whether that movement can be traced.**
