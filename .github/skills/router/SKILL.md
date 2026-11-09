
---
name: router
description: Discovers available skills dynamically and invokes the most appropriate skill based on the user's prompt. Use as the entry point when routing a request to a specialist skill.
---

# Router

## Purpose

Your only responsibility is to identify and invoke the appropriate skill for the user's prompt.

## Instructions

1. Discover all skills available in the current environment.
2. Include skills from all accessible and supported locations, including:
   - Personal / global skills.
   - Project / workspace skills.
   - Organization / enterprise skills.
   - Plugin-provided skills.
   - Other configured skill locations.
3. Use the active platform's native skill discovery mechanism and respect its discovery and precedence rules.
4. Read each discovered skill's `name` and `description` from its `SKILL.md` frontmatter.
5. Compare the user's prompt with the discovered skill descriptions.
6. Select the most appropriate skill or skills.
7. Read and invoke the selected skill using the platform's supported invocation mechanism.
8. If multiple skills are needed, invoke the relevant skills.
9. If no suitable skill exists, do not invent one.

## Constraints

- Never hardcode skill names, descriptions, or paths.
- Never assume that only project-level skills are available.
- Refresh skill discovery for each new routing request.
- Do not perform the specialist skill's work yourself when an appropriate skill is available.
- Do not add instructions or constraints to the selected skill.
- Do not dictate the selected skill's role, workflow, or response format.
- Let each selected skill operate according to its own `SKILL.md`.
- Do not tell the user to select or invoke a skill manually.
- Do not claim to have invoked a skill if it was not successfully invoked.

## Final rule

Discover → Match → Invoke.

Nothing more.
