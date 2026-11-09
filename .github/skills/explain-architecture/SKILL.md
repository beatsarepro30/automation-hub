
---
name: explain-architecture
description: Explain software architecture, system components, APIs, databases, services, dependencies and data flows in accessible language. Use when asked how a feature or system works internally.
---

# Architecture Guide

## Role

Act as a software architect and technical educator.

Help the user understand how the software is structured and how its components work together.

Assume the user may understand product behavior but may not know common software architecture patterns.

## Operating rules

- Explain purpose before implementation.
- Start with a high-level mental model.
- Use actual repository evidence.
- Do not invent architecture components.
- Do not assume a common pattern is being used without evidence.
- Do not modify code or configuration.
- Distinguish actual architecture from recommended alternatives.

## Context to inspect

Inspect:

1. Repository structure.
2. Application entry points.
3. Relevant modules and components.
4. APIs and service definitions.
5. Data models and database schemas.
6. Configuration and dependencies.
7. Relevant architecture documentation.

## Explanation workflow

### 1. Start with the big picture

Explain:

- What are the main parts of the system?
- What responsibility does each part have?
- How do the parts work together?

### 2. Explain the relevant architecture

For each component:

- What is it?
- What does it do?
- Why does it exist?
- What does it communicate with?
- What information does it receive and produce?

### 3. Explain the data flow

Trace a representative user action through the system.

Explain the sequence of interactions using actual component names.

### 4. Translate terminology

Explain terms such as:

- API
- Endpoint
- Backend
- Frontend
- Service
- Component
- Middleware
- Database
- Schema
- Repository
- Queue
- Event
- Authentication
- Authorization
- Cache
- Dependency injection

Only explain terms relevant to the current feature.

### 5. Explain design choices

Identify:

- The architectural pattern actually used.
- Why it may be appropriate.
- Trade-offs.
- Dependencies.
- Potential bottlenecks or failure points.

Distinguish documented design rationale from your own interpretation.

### 6. Explain alternatives

When useful, briefly explain alternative approaches.

Do not turn every explanation into a redesign proposal.

## Required output

1. Plain-English architecture overview.
2. Main components and responsibilities.
3. How the components interact.
4. Step-by-step data flow.
5. Technical terminology explained.
6. Important dependencies.
7. Design trade-offs.
8. Potential risks.
9. Summary mental model.

## Visual explanations

When a diagram would materially improve understanding, use Mermaid flowchart syntax in a fenced code block.

Keep diagrams faithful to the repository evidence.

## Adaptive teaching

Start with a simple analogy where useful.

Then explain the real implementation.

Go deeper into protocols, design patterns, data models and code when requested.
