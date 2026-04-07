---
name: github-governance-sync
description: Create and synchronize GitHub issues, milestones, branches, and solo-safe policy.
---

# GitHub Governance Sync

Use this skill when the work involves backlog management or repo policy.

## Goal

- Keep issues, milestones, branches, and docs aligned.
- Enforce a solo-safe branch and protection model.
- Make the workboard the live source of truth.

## Process

1. Create or update a milestone for each feature initiative.
2. Open a parent issue for the initiative.
3. Add sub-issues for implementation, docs, and validation slices.
4. Link related bugs and mark duplicates instead of recreating them.
5. Sync the workboard and changelog references after each batch.
6. Apply branch protection and workflow permissions after the backlog is stable.

## Policy Defaults

- Main branch is protected.
- Feature work uses short-lived branches.
- Required checks cover lint, test, build, docs, and Terraform validation where applicable.
- Do not require reviewer counts that block a solo maintainer.

## Output Format

- Milestone name
- Parent issue
- Sub-issues
- Branch name
- Policy action
- Documentation update
