---
name: deep-scan-triage
description: Triage repo scans into concrete bugs, features, and validation tasks.
---

# Deep Scan Triage

Use this skill when running an iterative audit of the repository.

## Goal

- Split a large scan into domain-sized passes.
- Separate confirmed bugs from feature ideas and docs gaps.
- Produce issue-ready findings with direct evidence.

## Process

1. Start with repo state, open issues, open PRs, and current workflows.
2. Scan app, infra, docs, and CI/CD in parallel when possible.
3. Deduplicate against existing issues and PRs before opening new ones.
4. Record only evidence-backed findings.
5. Assign each finding to a milestone or a bug issue.

## Triage Rules

- Bug: current behavior is broken, unsafe, or inconsistent with documented runtime behavior.
- Feature: capability is missing but the current system still works.
- Docs issue: the code works, but the guidance or references are stale or contradictory.
- Dedupe: do not reopen an issue already tracked in an open issue or PR.

## Output Format

- Finding title
- File or service evidence
- Impact
- Suggested issue or milestone target
- Validation status
