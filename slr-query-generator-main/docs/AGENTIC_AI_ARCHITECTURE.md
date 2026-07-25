# Autonomous Research Workflow Architecture

The existing SLR query generator remains the legacy capability layer. The autonomous workflow is additive and is exposed under `/api/v1`; legacy FastAPI endpoints and UI behavior are unchanged.

## Registry-driven execution

```mermaid
flowchart LR
    P[Planner Agent] --> AR[Agent Registry]
    AR --> LG[LangGraph dispatcher]
    LG --> Q[Query Generation Agent]
    LG --> S[Paper Search Agent]
    LG --> V[Validator Agent]
    Q --> TR[Tool Registry]
    S --> TR
    V --> TR
    TR --> O[OpenAlex]
    TR --> SS[Semantic Scholar]
    TR --> CR[Crossref]
    TR --> AX[arXiv]
```

The workflow imports only the `AgentRegistry`; it does not import concrete agent classes. Each agent resolves its capabilities from the `ToolRegistry`, which keeps external-provider clients out of agent code.

## Phase 1 graph

```mermaid
stateDiagram-v2
    [*] --> planner
    planner --> query_generation
    query_generation --> paper_search
    paper_search --> validator
    validator --> [*]
```

The Planner writes `execution_plan` using registered agent IDs. The graph then routes dynamically to the first incomplete registered agent. A later phase can add an agent to the registry without modifying the dispatcher.

## Durable state and memory

`ResearchWorkflowState` is serialized after every node to Supabase through `SharedWorkflowMemory`. The lifecycle is explicit:

`CREATED → PLANNING → QUERY_GENERATION → SEARCHING → SCREENING → DATA_EXTRACTION → QUALITY_ASSESSMENT → SYNTHESIS → REPORT_GENERATION → COMPLETED`

Failure and pause transitions are `FAILED` and `PAUSED`. Phase 1 reaches `COMPLETED` after query validation; later phases extend the plan with the remaining registered agents.

Use [001_research_workflow.sql](../migrations/001_research_workflow.sql) in Supabase before invoking the new API. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in the backend environment. The service-role key must never be sent to a browser.
