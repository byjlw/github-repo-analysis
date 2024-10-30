# github-repo-analysis
This Repo contains scripts and commands to better understand the development and health of a repository.

- Currently it only looks at external contributions


Here is an updated README.md file:

**External Contributors**
==========================

This script fetches external contributors to a GitHub repository and their monthly PR counts.

**Usage**
--------

```bash
python external_contributors.py --repo-owner <repo_owner> --repo-name <repo_name> --github-token <github_token> [--filter-organizations <filter_orgs>] [--exclude-contributors <exclude_contributors>] [--since <since_date>] [--output-tsv]
```

*   `repo_owner`: The owner of the GitHub repository.
*   `repo_name`: The name of the GitHub repository.
*   `github_token`: A valid GitHub token with read access to the repository.
*   `filter_orgs`: A list of organizations to filter out (optional).
*   `exclude_contributors`: A list of contributors to exclude (optional).
*   `since_date`: The date to start from (YYYY-MM-DD) (optional).
*   `--output-tsv`: Output in TSV format instead of JSON (optional).

**Environment Variables**
-------------------------

You can also set the following environment variables:

*   `REPO_OWNER`
*   `REPO_NAME`
*   `GITHUB_TOKEN`
*   `FILTER_ORGS`
*   `EXCLUDE_CONTRIBUTORS`

**Example**
--------

```bash
python external_contributors.py --repo-owner pytorch --repo-name torchchat --github-token ghp_g9lT43p6uQxXcK4yN8e7zRfOaM1wSbI --filter-organizations pytorch pytorch-labs --exclude-contributors user1 user2 --since 2022-01-01
```

This will fetch external contributors to the `pytorch/torchchat` repository, excluding members of the `pytorch` and `pytorch-labs` organizations, and excluding the contributors `user1` and `user2`. It will only include contributors who have made contributions since January 1, 2022.

**Output**
------

The script outputs the external contributors and their monthly PR counts in JSON format by default. You can use the `--output-tsv` flag to output in TSV format instead.
