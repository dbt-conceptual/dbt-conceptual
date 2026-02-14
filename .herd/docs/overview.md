# The Herd -- System Overview

## What This Is

The Herd is a multi-agent AI development team. Six specialized agents -- each with a defined role, craft standards, and operational constraints -- build software under the direction of a human Architect.

This is not a framework. It is not a prompt library. It is a working team that ships production code.

The codebase it builds -- dbt-conceptual -- is 100% AI-generated. Every line of code, every test, every configuration file was produced by an agent. The Architect designs, decides, and reviews. The agents implement.

That distinction matters. The value in this arrangement is not that AI writes code faster. The value is that the Architect operates at the architectural layer -- design, governance, quality judgment -- while the agents provide consistent execution against governed standards. The Architect reviews for drift, not syntax.

## The Principle Hierarchy

Four levels govern every decision in The Herd, in strict order of precedence:

**Principles** come first. Why we build something matters more than how. A principle like "bidirectional by default" or "fail fast, fail clearly" overrides any implementation convenience.

**Capabilities** come second. What the system can do flows from the principles, not from what's technically easy.

**Implementation** is third. How we build it -- the code patterns, the testing strategy, the data model -- serves the capabilities.

**Technology** is last. The specific tools (Python, DuckDB, Evidence.dev, dbt) are choices of convenience. They are replaceable. The principles are not.

This hierarchy is explicit because AI agents are eager to jump to implementation. The hierarchy forces the question: does this serve a principle, or does it just feel productive?

## The Architect

Faust is the sole decision-maker. Not a committee. Not a consensus process. One person who designs, prioritizes, reviews, and merges.

The Architect does not write code. The Architect writes decisions. Those decisions are captured as Herd Decision Records (HDRs) -- lightweight architectural records that document what was decided, why, and what principle governed the choice.

The Architect's review posture is fundamentally different from traditional code review. The question is not "is this syntactically correct?" -- that is the test suite's job. The question is "does this align with the architecture?" Structural drift is the failure mode, not bugs.

## Mini-Mao

Mini-Mao is the coordinator. Scrum master, not architect. Mini-Mao tracks state, drafts tickets, spawns agents, captures decisions, and reports status.

Mini-Mao never codes. Mini-Mao never decides. When the temptation arises to "just fix it" -- and it does, especially after three failed agent spawns -- Mini-Mao spawns a fourth with corrected context. The coordination role is the role.

This constraint exists because coordination and implementation are different cognitive modes. Mixing them degrades both.

## How Work Flows

The lifecycle is: Linear ticket, agent assignment, feature branch, implementation, PR, QA review by Wardenstein, Architect merge.

Every PR goes through QA. No exceptions. Every agent works on a feature branch. No agent pushes to main. The Architect is the sole merge authority.

This is not ceremony for ceremony's sake. These constraints exist because agents are fast, confident, and sometimes wrong. The gates catch what speed misses.

---

## Project Structure

The `.herd/` directory contains all Herd infrastructure. The source code lives in `src/`. These are the key locations.

### Repository Layout

```
dbt-conceptual/
  src/dbt_conceptual/       # Python source code (CLI, parser, validator, exporter)
  tests/                    # pytest test suite
  frontend/                 # React frontend (Pikasso's domain)
  docs/                     # User-facing documentation
  .herd/                    # Herd agent infrastructure
    STATUS.md               # Current state of all work
    craft.md                # Quality standards by role
    roles/                  # Agent role definitions
      mini-mao.md
      grunt.md
      pikasso.md
      wardenstein.md
      shakesquill.md
      gauss.md
    decisions/              # Herd Decision Records (HDRs)
    templates/              # Standardized templates for handoffs, reviews, etc.
    handoffs/               # Active work handoff files
    sessions/               # Session logs and intro markers
    dbt/                    # Herd MCP dbt project (Data Vault analytics)
    mcp/                    # MCP server (Python, DuckDB backend)
    evidence/               # Evidence.dev dashboards
    specs/                  # Technical specifications
  CLAUDE.md                 # Project guidelines for Claude Code
```

### Key Files

| File | Purpose |
|------|---------|
| `.herd/STATUS.md` | Current state of all active work, blocks, and backlogs |
| `.herd/craft.md` | Craft standards for each agent role |
| `CLAUDE.md` | Project conventions, pre-commit checklist, design decisions |
| `.herd/decisions/*.md` | Captured architectural decisions (HDRs 0001-0014) |

### Herd MCP Server

The Herd MCP Server is a DuckDB-backed analytics system that tracks agent activity, ticket lifecycle, and operational metrics. It uses Data Vault 2.0 modeling (HDR-0007) with a medallion architecture:

- **Bronze**: Source extraction and staging
- **Silver**: Data Vault (hubs, satellites, links) for temporal history
- **Gold**: Dimensional model (dimensions and facts) for querying

Evidence.dev dashboards (HDR-0008) sit on top, providing operational visibility to the Architect.

### Agent Roster

| Agent | Role | Model | Status |
|-------|------|-------|--------|
| Mini-Mao | Coordinator / Scrum Master | Opus | Active |
| Grunt | Backend Developer | Sonnet | Active |
| Pikasso | Frontend Developer | Sonnet | Active |
| Wardenstein | QA Engineer | Opus | Active |
| Shakesquill | Documentation Writer | Opus | Active |
| Gauss | Data Visualization & Analytics | Sonnet | Active |

Model assignment follows HDR-0004: Opus for agents that interpret, judge, or synthesize. Sonnet for agents that execute against governed standards.
