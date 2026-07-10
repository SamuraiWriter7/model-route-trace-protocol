# Changelog

All notable changes to the Model Route Trace Protocol are documented in this file.

The protocol follows a staged first arc:

```text
v0.1 — Record
v0.2 — Bind
v0.3 — Decide
v0.4 — Graph
v0.5 — Unify
```

---

## [Unreleased]

### Planned

Potential future work may be developed as separate protocol families rather than extending the first arc indefinitely.

Candidate directions include:

* model route policy,
* route deviation and fallback analysis,
* route cost and energy audit,
* cross-route performance comparison,
* model route attribution,
* royalty bridge integration.

The v0.1–v0.5 first arc is considered structurally complete.

---

# [0.5.0-candidate] — Unified Model Route Trace Lifecycle

## Added

### Unified Model Route Trace Lifecycle

Added:

```text
schemas/unified-model-route-trace-lifecycle.schema.json
```

and:

```text
examples/unified-model-route-trace-lifecycle.example.yaml
```

The lifecycle record unifies:

```text
Origin
→ Route Decision
→ Provider Binding
→ Compute Placement
→ Model Execution
→ Cross-Agent Route Graph
→ Artifact
→ Trace Integrity
→ Audit Readiness
→ Royalty Readiness
```

### Origin lifecycle binding

Added support for recording:

* origin reference,
* origin type,
* ignition reference,
* origin verification state,
* verification evidence reference.

Supported origin classes include:

* human request,
* agent request,
* scheduled task,
* event trigger,
* origin trace,
* re-ignition,
* other.

### Decision lifecycle binding

Added:

* route decision reference,
* decision status,
* selected route reference,
* decision policy references.

### Provider binding aggregation

Added lifecycle-level aggregation of:

* provider binding references,
* binding resolution status,
* unresolved binding references.

### Compute placement aggregation

Added support for:

* placement receipt references,
* placement verification status,
* placement policy references.

### Execution trace aggregation

Added support for:

* multiple model route trace references,
* execution status,
* fallback-use indication,
* fallback route references.

### Route graph lifecycle binding

Added:

* cross-agent route graph reference,
* graph status,
* graph integrity verification state,
* graph integrity evidence reference.

### Artifact lifecycle binding

Added:

* artifact references,
* artifact binding status,
* artifact binding evidence references.

### Trace Integrity Layer

Added explicit integrity checks for:

* origin link completeness,
* decision link completeness,
* binding link completeness,
* placement link completeness,
* execution link completeness,
* graph link completeness,
* artifact link completeness.

Supported overall integrity states:

```text
complete
partial
broken
unverified
```

### Audit Readiness

Added explicit readiness checks for:

* route decision auditability,
* provider path auditability,
* compute placement auditability,
* cross-agent path auditability,
* artifact lineage auditability.

Supported states:

```text
ready
conditionally_ready
not_ready
unverified
```

### Royalty Readiness

Added evidence-readiness checks for:

* origin attribution,
* agent contribution paths,
* model route paths,
* tool contribution paths,
* human contribution paths,
* artifact bindings.

Supported states:

```text
ready
conditionally_ready
not_ready
not_applicable
unverified
```

The protocol does not calculate payment or contribution percentages.

It only determines whether sufficient trace evidence exists for downstream attribution systems.

### Lifecycle Phase Record

Added lifecycle phase tracking for:

* origin,
* decision,
* binding,
* placement,
* execution,
* route graph,
* artifact,
* trace integrity,
* audit readiness,
* royalty readiness.

### Lifecycle semantic validation

Added checks ensuring:

* required lifecycle phases are present,
* lifecycle phases are unique,
* `complete` trace integrity requires all required links,
* audit readiness cannot be `ready` while auditability checks are false,
* royalty readiness cannot be `ready` while contribution-path checks are false,
* completed lifecycles do not contain unfinished required phases.

### Cross-record reference validation

Added validation across example records.

Checks include:

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
Lifecycle.execution.route_trace_refs
contains
ModelRouteRecord.route_trace_id
```

Cross-record validation marks the transition from isolated document validation to protocol-collection validation.

## Changed

* Expanded `scripts/validate_examples.py` to validate all v0.1–v0.5 records.
* Added cross-record integrity checking.
* Added lifecycle-level semantic validation.
* Completed the first protocol arc.

---

# [0.4.0-candidate] — Cross-Agent Model Route Graph

## Added

### Cross-Agent Model Route Graph

Added:

```text
schemas/cross-agent-model-route-graph.schema.json
```

and:

```text
examples/cross-agent-model-route-graph.example.yaml
```

The graph records distributed AI execution as a directed acyclic graph.

### Node model

Added node types for:

* origin trace,
* router,
* agent execution,
* model execution,
* retrieval,
* tool execution,
* boundary check,
* human gate,
* artifact,
* other.

Nodes may reference:

* agent identity,
* agent role,
* wing identity,
* model,
* route trace,
* route decision,
* provider binding,
* handoff record,
* placement receipt,
* tool,
* retrieval stage,
* policy,
* human review,
* artifact.

### Edge model

Added edge relationship types for:

* origin,
* routing,
* handoff,
* context transfer,
* evidence transfer,
* verification,
* boundary checking,
* human approval,
* merge,
* artifact production,
* fallback.

Added transfer modes:

```text
sequential
parallel
conditional
fallback
merge
human_escalation
other
```

### Parallel Group model

Added representation of parallel execution branches.

A parallel group can define:

* member nodes,
* join node,
* completion policy,
* governing policy reference.

Supported completion policies:

```text
all_required
any_sufficient
quorum
policy_defined
```

### Graph metrics

Added optional metrics for:

* node count,
* edge count,
* maximum graph depth,
* parallel branch count.

### DAG semantic validation

Added validation for:

* duplicate node IDs,
* duplicate edge IDs,
* invalid node references,
* self-loops,
* invalid entry nodes,
* invalid terminal nodes,
* cycles,
* unreachable nodes,
* nodes unable to reach a terminal node,
* graph metric mismatches.

## Changed

* Expanded `scripts/validate_examples.py` with graph semantic validation.
* Extended the protocol from linear route tracing to multi-agent execution topology.

## Structural significance

v0.4 changes Trace representation from:

```text
Sequence
```

to:

```text
Graph
```

This enables representation of:

* Multi-Wing systems,
* parallel verification,
* policy review branches,
* evidence convergence,
* Human Gate merges,
* distributed artifact production.

---

# [0.3.0-candidate] — Route Decision Receipt

## Added

### Route Decision Receipt

Added:

```text
schemas/route-decision-receipt.schema.json
```

and:

```text
examples/route-decision-receipt.example.yaml
```

The receipt records why one execution route was selected from multiple candidate routes.

### Decision Context

Added task context fields for:

* task complexity,
* data sensitivity,
* latency priority,
* cost priority,
* energy priority,
* quality requirement,
* decision summary.

### Constraint model

Added constraints for:

* required capability level,
* maximum latency,
* maximum cost class,
* allowed execution localities,
* region requirements,
* data boundary policies,
* security policies.

### Candidate Route model

Each route candidate may record:

* route class,
* model reference,
* provider binding reference,
* placement candidate reference,
* execution locality,
* capability assessment,
* latency assessment,
* cost assessment,
* energy assessment,
* policy status,
* policy evidence,
* disposition,
* rejection reasons.

Supported dispositions:

```text
selected
rejected
fallback
deferred
```

### Rejection reason model

Added structured rejection reasons including:

* capability threshold not met,
* latency budget exceeded,
* cost budget exceeded,
* energy budget exceeded,
* data boundary violation,
* region constraint violation,
* security policy violation,
* provider not approved,
* endpoint unavailable,
* placement unavailable,
* lower priority,
* other.

### Selection record

Added:

* selected route ID,
* selection reason codes,
* selection summary,
* decision mode,
* decision agent reference,
* human review reference,
* override state and reason.

### Computational Pranayama assessment

Added:

* local-first check,
* smaller-model check,
* minimum-sufficient-compute check,
* escalation requirement,
* escalation reason,
* compute necessity classification,
* Pranayama policy reference.

### Policy evaluation

Added:

* overall policy status,
* evaluated policies,
* condition references,
* violation references.

### Semantic validation

Added validation ensuring:

* candidate route IDs are unique,
* the selected route exists,
* exactly one route is marked selected,
* selected-route references match,
* selected routes contain no rejection reasons,
* rejected routes contain at least one rejection reason.

## Changed

* Expanded the validator from schema-only checks toward semantic validation.
* Extended the protocol from execution observability to decision provenance.

## Structural significance

v0.3 records not only:

> What happened?

but:

> Why did the system choose this path instead of another?

This introduces explicit decision provenance into the protocol.

---

# [0.2.0-candidate] — Provider and Endpoint Binding

## Added

### Provider and Endpoint Binding

Added:

```text
schemas/provider-endpoint-binding.schema.json
```

and:

```text
examples/provider-endpoint-binding.example.yaml
```

The binding connects a model route to:

* provider identity,
* endpoint class,
* execution locality,
* protocol,
* region,
* compute node,
* trust boundary,
* data boundary,
* authentication mode,
* network path.

### Provider model

Added provider classes:

```text
managed_cloud
enterprise_cloud
self_hosted
local_runtime
openai_compatible
other
```

### Endpoint model

Added endpoint classes:

```text
managed_api
enterprise_endpoint
self_hosted_api
local_runtime
gateway_proxy
openai_compatible_endpoint
other
```

### Trust Boundary model

Added:

* source trust domain,
* destination trust domain,
* boundary-crossing state,
* boundary policy references.

### Data Boundary model

Added:

* data classification,
* residency scope,
* allowed regions,
* retention policy,
* model-training-use policy,
* data policy references.

### Authentication model

Added:

* authentication mode,
* non-secret credential reference,
* mandatory `secret_material_recorded: false`.

Supported authentication modes include:

```text
api_key
oauth
managed_identity
service_account
mtls
local_socket
none
other
```

### Network Path model

Added route classes for:

```text
public_internet
private_network
local_loopback
air_gapped
hybrid
custom
unknown
```

Also added:

* gateway references,
* proxy references,
* encryption-in-transit state.

## Security

Explicitly established the rule:

> Secret material must never be embedded in protocol records.

The protocol records authentication method and configuration references, not credentials.

## Changed

* Expanded `scripts/validate_examples.py` to validate v0.1 and v0.2 records.
* Separated model identity from provider and endpoint path.

## Structural significance

v0.2 establishes that:

```text
Model Identity
≠
Provider
≠
Endpoint
≠
Execution Locality
≠
Trust Boundary
```

This separation is essential for BYOK, local models, enterprise endpoints, and self-hosted execution.

---

# [0.1.0-candidate] — Model Route Record

## Added

### Initial protocol structure

Created the initial repository structure:

```text
schemas/
examples/
scripts/
.github/workflows/
```

### Model Route Record

Added:

```text
schemas/model-route-record.schema.json
```

and:

```text
examples/model-route-record.example.yaml
```

The record captures a single execution route segment.

Core structure:

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

### Task record

Added:

* task ID,
* task type,
* task summary.

### Agent record

Added:

* agent ID,
* agent role,
* wing ID,
* handoff record reference.

### Model record

Added:

* model ID,
* model family,
* model version,
* model class.

Supported model classes include:

```text
small
medium
large
frontier
specialized
embedding
reranker
multimodal
other
```

### Provider record

Added:

* provider name,
* provider type,
* provider account reference.

### Execution record

Added:

* execution locality,
* environment class,
* region,
* compute node reference,
* compute placement receipt reference.

### Input lineage

Added:

* input reference,
* origin trace reference,
* source artifact references.

### Output lineage

Added:

* artifact reference,
* artifact type,
* Trace Relay reference.

### Timing and status

Added:

* execution start,
* execution completion,
* duration,
* execution status.

### Validation

Added:

```text
scripts/validate_examples.py
```

for JSON Schema and example validation.

Added GitHub Actions workflow:

```text
.github/workflows/validate.yml
```

for automatic validation on:

* push to `main`,
* pull requests,
* manual workflow dispatch.

## Structural significance

v0.1 establishes the minimum trace unit:

> **Who used which model through which provider, where execution occurred, what input lineage was used, and what artifact was produced?**

This became the base record for all later versions.

---

# First Arc Summary

The first arc evolved through five layers.

## v0.1 — Record

```text
What happened?
```

## v0.2 — Bind

```text
Which provider, endpoint, and trust boundary were involved?
```

## v0.3 — Decide

```text
Why was this route selected?
```

## v0.4 — Graph

```text
How did multiple agents, models, checks, and gates interact?
```

## v0.5 — Unify

```text
Is the complete origin-to-artifact lifecycle intact and ready for audit?
```

Together, the first arc establishes:

```text
Origin
   ↓
Decision
   ↓
Binding
   ↓
Placement
   ↓
Execution
   ↓
Graph
   ↓
Artifact
   ↓
Integrity
   ↓
Audit Readiness
   ↓
Royalty Readiness
```

The protocol has therefore evolved from a simple model execution log into a lifecycle-level trace architecture for multi-model, multi-provider, and multi-agent AI systems.
