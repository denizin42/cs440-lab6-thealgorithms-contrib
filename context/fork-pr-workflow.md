# Safe Fork & Pull Request Workflow Context (`@./context/fork-pr-workflow.md`)

## GitHub fork workflow

### Fork from upstream (`TheAlgorithms/Python`)

- **GitHub Repo Fork**: Use gh tool to fork <https://github.com/TheAlgorithms/Python> repository to denizin42 with same name.
- **GitHub Commit**: Only commit to denizin42's forked repository and never directly to main or master. Never commit to the upstream project <https://github.com/TheAlgorithms/Python>. Create a branch using contributing-rules for branch names.
- **One File Per PR**: Each Pull Request must modify only a single algorithm file (`maths/binomial_distribution.py`).
- **Human In The Loop**: A approver must manually approve the PR into main.
