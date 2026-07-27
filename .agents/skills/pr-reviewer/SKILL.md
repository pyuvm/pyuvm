---
name: pr-reviewer
description: >-
  Evaluates GitHub Pull Requests against a Test Sufficiency Matrix and Intent Realization Alignment, or provides a high-level summary of all open PRs in the repository.
---

# PR Reviewer

## Overview
This skill allows AI agents to perform detailed reviews of GitHub Pull Requests or generate high-level summaries of all open PRs in the repository. It analyzes code diffs against strict criteria to ensure test coverage and alignment with the PR's stated goals. Because this skill uses the agent's own capabilities and the GitHub CLI (`gh`), it requires no custom scripts or API keys other than what the agent is already using.

## Dependencies
- GitHub CLI (`gh`): Must be installed and authenticated on the system where the agent is running.

## Quick Start
To use this skill, ask your agent:
- "Run the pr-reviewer skill on PR 412"
- "Use the pr-reviewer skill to summarize all open PRs"

## Workflow

### 1. Determine Mode
- Check the user's prompt to determine if they want to review a specific PR (e.g., "review PR 412") or summarize all open PRs.

### 2. Context Gathering
- Read the `README.md` in the root of the repository to understand the project's high-level goals.
- If a `CONTRIBUTING.md` exists, read it as well to capture any specific coding guidelines.

### 3. Review a Single PR
If the user requested a specific PR review, perform the following steps:
- Run `gh pr view <PR> --json title,body` to fetch the PR's metadata.
- Run `gh pr diff <PR>` to fetch the PR's code diff.
- **Size Check:** Check the length (line count) of the diff output. If the diff exceeds **1000 lines**, stop immediately. Fail loudly and inform the user that the PR is too large to review and must be broken down into smaller pieces.
- **Analysis:** If the diff is under the limit, analyze the code changes against the following rubric:
  - *Test Sufficiency Matrix:* Do conditional branches, edge cases, and new logic paths have corresponding test coverage in the diff?
  - *Intent Realization Alignment:* Does the code actually implement the logic and goals promised in the PR title and description?
- **Output:** Generate a clear, markdown-formatted summary report addressing both points in the rubric, and conclude with a Pass/Fail recommendation.

### 4. Summarize All Open PRs
If the user requested a repo-wide summary, perform the following steps:
- Run `gh pr list` to fetch the list of all open PRs.
- For each relevant PR in the list, you may optionally run `gh pr view <PR> --json title,body` to gather more context.
- **Output:** Generate a high-level summary report of pending work across the repository, grouping or highlighting PRs based on the project's goals (from `README.md`).

## Rate Limiting
The `gh` CLI handles its own API rate limiting against GitHub. If the CLI returns a rate limit error, inform the user. The agent's LLM calls are bound by the user's existing agent session limits.

## Common Mistakes
- **Assuming large PRs can be summarized:** Do not attempt to summarize a PR with a diff > 1000 lines. The instructions require you to fail loudly.
- **Forgetting context:** Always read the `README.md` before generating the final report to ensure your feedback aligns with project goals.
