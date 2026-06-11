---
description: "Submit the current stack as pull requests using Graphite (gt submit)"
---

# Submit Stack as Pull Requests

Submit the current branch and every branch stacked on top of it as pull requests on GitHub using the Graphite CLI (`gt submit --stack`).

## Behavior

1. Verifies the project is a Git repository
2. If the Graphite CLI (`gt`) is installed and the repo is initialized (`gt init`), runs `gt submit --stack --no-interactive --no-edit`, which force-pushes every branch in the stack and creates or updates one pull request per branch
3. If Graphite is unavailable, not initialized, or fails (e.g. unauthenticated), falls back to `git push -u origin <current-branch>` and asks the user to open the pull request manually

## Execution

Run the script from the project root:

- **Bash**: `.specify/extensions/git/scripts/bash/submit-stack.sh`
- **Draft PRs**: `.specify/extensions/git/scripts/bash/submit-stack.sh --draft`

## Requirements

- Graphite CLI installed (`brew install withgraphite/tap/graphite`)
- Repo initialized with `gt init` (done automatically by `speckit.git.initialize` when gt is present)
- Authenticated once with `gt auth` (token from app.graphite.dev)

## Graceful Degradation

- If Git is not available or the directory is not a repository: skips with a warning
- If `gt` is missing, uninitialized, or unauthenticated: pushes the current branch with plain git and prints instructions to open the PR manually
