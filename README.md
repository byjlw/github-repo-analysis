# github-repo-analysis
This Repo contains scripts and commands to better understand the development and health of a repository.

- Currently it only looks at external contributions


**External Contributors**
==========================

This script fetches external contributors to a GitHub repository and their monthly PR counts.

**Usage**
--------

```bash
python external_contributors.py --repo-owner <repo_owner> --repo-name <repo_name> --github-token <github_token> [--filter-organizations <filter_orgs>]
```

*   `repo_owner`: The owner of the GitHub repository.
*   `repo_name`: The name of the GitHub repository.
*   `github_token`: A valid GitHub token with read access to the repository.
*   `filter_orgs`: A list of organizations to filter out (optional).

You can also set the following environment variables:

*   `REPO_OWNER`
*   `REPO_NAME`
*   `GITHUB_TOKEN`
*   `FILTER_ORGS`

**Example**
--------

```bash
python external_contributors.py --repo-owner pytorch --repo-name torchchat --github-token ghp_g9lT43p6uQxXcK4yN8e7zRfOaM1wSbI --filter-organizations pytorch pytorch-labs
```

This will fetch external contributors to the `pytorch/torchchat` repository, excluding members of the `pytorch` and `pytorch-labs` organizations.

**Output**
------

The script outputs the external contributors and their monthly PR counts in JSON format by default. You can use the `--output-tsv` flag to output in TSV format instead.
