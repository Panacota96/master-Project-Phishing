---
name: architecture-docs-aws
description: Improve architecture docs and Mermaid diagrams with AWS-aware conventions.
---

# Architecture Docs AWS

Use this skill when updating architecture diagrams or repo documentation.

## Goal

- Keep Mermaid as the primary diagram format.
- Make AWS topology explicit without relying on unsupported logo embedding.
- Standardize legends, badges, and companion assets.

## Process

1. Update the textual architecture description first.
2. Keep Mermaid diagrams readable and GitHub-friendly.
3. Use a legend for AWS services and icon conventions.
4. Add badge or SVG companions when a richer visual is needed.
5. Align README, architecture docs, and runbooks to the same terms.

## Diagram Rules

- Prefer labeled service nodes over decorative complexity.
- Do not depend on native AWS logos inside Mermaid nodes.
- Use consistent service names and environment labels.
- Keep generated assets alongside Mermaid, not instead of it.

## Output Format

- Doc section or file to update
- Diagram or legend change
- AWS service naming convention
- Companion asset requirement
