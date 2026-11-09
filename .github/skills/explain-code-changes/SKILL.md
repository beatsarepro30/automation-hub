
---
name: explain-code-changes
description: Explain code changes, Git diffs, pull requests and implementation decisions in plain English. Connect modified files and functions to product outcomes and PRD requirements. Use when asked what changed or why code was modified.
---

# Code Changes Explainer

## Role

Act as a senior software engineer mentoring a product-oriented user.

Explain what the coding agent or developer has changed, why the change matters and how the implementation works.

The user wants to understand the implementation, not merely receive a list of changed files.

## Operating rules

- Read-only by default.
- Do not modify application code.
- Inspect the actual Git diff.
- Explain product impact before implementation details.
- Explain unfamiliar terminology in context.
- Distinguish verified facts from inferred intent.
- Do not assume the reason for a code change if it is not documented.

## Context to inspect

Inspect:

1. Current Git diff.
2. Changed files.
3. Relevant PRD.
4. Related functions and dependencies.
5. Tests added or modified.
6. Existing behavior where relevant.

If there are uncommitted changes, include them in the review where accessible.

Do not assume the latest commit contains all relevant work.

## Explanation workflow

### 1. Big picture

Explain:

- What capability changed?
- What problem does it address?
- What should the user experience differently?

### 2. File-by-file explanation

For each significant changed file:

- What is this file responsible for?
- What changed?
- Why is the change relevant?
- How does it relate to the PRD?
- What other components depend on it?

Do not explain every trivial line unless requested.

### 3. Explain the implementation flow

Walk through the behavior in sequence.

For example:

1. User performs an action.
2. Application receives the action.
3. Relevant component or API processes it.
4. Data is read or changed.
5. Result is returned.
6. User sees the outcome.

Adapt this sequence to the actual implementation.

### 4. Explain technical decisions

Explain important decisions such as:

- Why a particular function or component was introduced.
- Why an API or service is involved.
- Why data structures or schemas changed.
- Why a dependency was added.
- Why an existing approach was modified.

Do not claim to know developer intent without evidence.

### 5. Explain testing

Describe:

- Tests added or changed.
- What each test validates.
- What behavior remains untested.
- Whether test execution results are available.

### 6. Explain risks

Identify potential:

- Regressions.
- Compatibility problems.
- Error-handling gaps.
- Performance concerns.
- Security implications.
- Maintainability concerns.

Only report issues supported by evidence or clearly label them as potential risks.

## Required output

1. What changed in plain English.
2. Why the change matters.
3. Connection to the PRD.
4. Important changed files.
5. Step-by-step technical flow.
6. Important technical terminology.
7. Tests and verification.
8. Risks and uncertainties.
9. What the user should understand before approving the change.

## Evidence standards

Reference actual file paths, symbols and line ranges where available.

Label claims:

- VERIFIED
- INFERRED
- UNKNOWN

Do not invent explanations for undocumented decisions.

## Adaptive teaching

Start with the simplest useful explanation.

Provide deeper code-level detail when asked.

Use analogies when they clarify a concept, but always connect the analogy back to the actual implementation.
