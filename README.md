# github-repo-analysis
This Repo contains scripts and commands to better understand the development and health of a repository.

## Install
```bash
git clone https://github.com/byjlw/github-repo-analysis.git
cd github-repo-analysis
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Scripts

### Contributor Analysis

This script fetches and analyzes contributors to a GitHub repository, tracking their monthly PR counts and distinguishing between internal and external contributors.

#### Usage

```bash
python external_contributors.py --repo-owner <repo_owner> --repo-name <repo_name> --github-token <github_token> [--filter-organizations <filter_orgs>] [--internal-contributors <internal_list>] [--external-contributors <external_list>] [--show-internal] [--show-external] [--show-unknown] [--since <since_date>] [--output-tsv] [--start-date <start_date>] [--end-date <end_date>]
```

*   `repo_owner`: The owner of the GitHub repository.
*   `repo_name`: The name of the GitHub repository.
*   `github_token`: A valid GitHub token with read access to the repository.
*   `filter_organizations`: A list of organizations whose members are considered internal contributors (optional).
*   `internal_contributors`: A list of contributors to explicitly mark as internal (optional).
*   `external_contributors`: A list of contributors to explicitly mark as external (optional).
*   `show_internal`: Flag to show internal contributors in output and charts (default: False).
*   `show_external`: Flag to show external contributors in output and charts (default: True).
*   `show_unknown`: Flag to show unknown contributors in output and charts (default: True).
*   `since_date`: The date to start fetching data from (YYYY-MM-DD) (optional).
*   `--output-tsv`: Output in TSV format instead of JSON (optional).
*   `start_date`: The date to start displaying in charts (YYYY-MM-DD) (optional).
*   `end_date`: The date to end displaying in charts (YYYY-MM-DD) (optional).
*   `exclude_contributors`: [DEPRECATED] Use `--internal-contributors` instead.

#### Environment Variables

You can also set the following environment variables:

*   `REPO_OWNER`
*   `REPO_NAME`
*   `GITHUB_TOKEN`
*   `FILTER_ORGS`
*   `INTERNAL_CONTRIBUTORS`
*   `EXTERNAL_CONTRIBUTORS`

#### Example

```bash
# Original functionality (external contributors only)
python external_contributors.py --repo-owner pytorch --repo-name torchchat --github-token ghp_g9lT43p6uQxXcK4yN8e7zRfOaM1wSbv --filter-organizations pytorch pytorch-labs

# Show both internal and external contributors
python external_contributors.py --repo-owner pytorch --repo-name torchchat --github-token ghp_g9lT43p6uQxXcK4yN8e7zRfOaM1wSbv --filter-organizations pytorch pytorch-labs --show-internal

# Explicitly mark some contributors as internal regardless of organization
python external_contributors.py --repo-owner pytorch --repo-name torchchat --github-token ghp_g9lT43p6uQxXcK4yN8e7zRfOaM1wSbv --filter-organizations pytorch --internal-contributors user1 user2

# Explicitly mark some contributors as external regardless of organization
python external_contributors.py --repo-owner pytorch --repo-name torchchat --github-token ghp_g9lT43p6uQxXcK4yN8e7zRfOaM1wSbv --filter-organizations pytorch --external-contributors user3 user4

# Combine explicit internal and external lists with date filtering
python external_contributors.py --repo-owner pytorch --repo-name torchchat --github-token ghp_g9lT43p6uQxXcK4yN8e7zRfOaM1wSbv --filter-organizations pytorch --internal-contributors user1 user2 --external-contributors user3 user4 --start-date 2023-01-01 --end-date 2023-12-31

# Show only unknown contributors (those not in either internal or external lists when both are provided)
python external_contributors.py --repo-owner pytorch --repo-name torchchat --github-token ghp_g9lT43p6uQxXcK4yN8e7zRfOaM1wSbv --internal-contributors user1 user2 --external-contributors user3 user4 --show-internal=False --show-external=False --show-unknown
```

#### Contributor Classification Logic

Contributors are classified using the following precedence order:
1. Explicitly listed in `--external-contributors` → classified as "external" (highest priority)
2. Explicitly listed in `--internal-contributors` → classified as "internal"
3. Member of an organization in `--filter-organizations` → classified as "internal"
4. If both `--internal-contributors` and `--external-contributors` are provided → classified as "unknown"
5. Otherwise → classified as "external" (default)

#### Output

The script outputs the contributors and their monthly PR counts in JSON format by default:

```json
{
  "user1": {
    "type": "internal",
    "prs": 5,
    "months": {
      "2022-01": 2,
      "2022-02": 3
    }
  },
  "user2": {
    "type": "external",
    "prs": 3,
    "months": {
      "2022-01": 1,
      "2022-03": 2
    }
  },
  "user3": {
    "type": "unknown",
    "prs": 4,
    "months": {
      "2022-02": 1,
      "2022-03": 3
    }
  }
}
```

You can use the `--output-tsv` flag to output in TSV format instead:
```
Contributor  Type      Total PRs  Total Contributions  Month    PRs
user1        internal  5          10                   2022-01  2
user1        internal  5          10                   2022-02  3
user2        external  3          5                    2022-01  1
user2        external  3          5                    2022-03  2
user3        unknown   4          7                    2022-02  1
user3        unknown   4          7                    2022-03  3
```

#### Visualizations

The script generates charts to help understand contribution patterns:

1. **Contributor Activity** (contributor_trends.png):
   - Shows monthly contributions and unique contributors
   - Can display internal contributors (green lines), external contributors (blue/red lines), and unknown contributors (orange lines)
   - Solid lines for external contributors, dashed lines for internal contributors, dotted lines for unknown contributors
   - Can be filtered by date range using --start-date and --end-date

   ![Contributor Trends](docs/contributor_trends.png)

2. **Open Pull Requests** (open_prs_trend.png):
   - Shows the number of open PRs over time by contributor type
   - Green line: Open PRs from internal contributors (when --show-internal is used)
   - Purple line: Open PRs from external contributors
   - Orange line: Open PRs from unknown contributors (when both internal and external lists are provided)
   - Can be filtered by date range using --start-date and --end-date

   ![Open PRs Trend](docs/open_prs_trend.png)

### Issue Statistics

This script analyzes and visualizes issue trends for a GitHub repository, showing the number of open issues over time and issues closed per day.

#### Usage

```bash
python issue_stats.py <github-repo> <personal-access-token> [fetch-limit] [--use-cache-only] [--start-date <start_date>] [--end-date <end_date>]
```

*   `github-repo`: The repository in format 'owner/name' (e.g., 'pytorch/pytorch')
*   `personal-access-token`: A valid GitHub token with read access to the repository
*   `fetch-limit`: Maximum number of issues to fetch (optional, default: 1000)
*   `--use-cache-only`: Use only cached data, don't make API calls (optional)
*   `start_date`: The date to start displaying in charts (YYYY-MM-DD) (optional)
*   `end_date`: The date to end displaying in charts (YYYY-MM-DD) (optional)

#### Example

```bash
# Fetch 2000 issues
python issue_stats.py pytorch/pytorch ghp_g9lT43p6uQxXcK4yN8e7zRfOaM1wSbv 2000

# Fetch issues and display charts for 2023 only
python issue_stats.py pytorch/pytorch ghp_g9lT43p6uQxXcK4yN8e7zRfOaM1wSbv --start-date 2023-01-01 --end-date 2023-12-31
```

This will analyze issues from the pytorch/pytorch repository. The fetch-limit controls how many issues to retrieve, while --start-date and --end-date control what time period to display in the charts.

#### Output

The script generates two charts in the output directory:

1. **Overall Issue Trends** (issue_trends.png):
   - Number of open issues over time (red line)
   - Number of issues closed per day (blue line)
   - Can be filtered by date range using --start-date and --end-date

   ![Issue Trends](docs/issue_trends.png)

2. **Issues by Label** (issue_trends_by_label.png):
   - Shows trends for the top 14 most-used labels
   - Includes a line for unlabeled issues
   - Uses logarithmic scale for better visualization
   - Legend shows current count for each label
   - Labels sorted by current count for easy reference
   - Can be filtered by date range using --start-date and --end-date

   ![Issues by Label](docs/issue_trends_by_label.png)

Both charts provide complementary views of the repository's issue activity - one showing overall trends and the other breaking down issues by their labels.

## Core Components

### GitHub API Client

The repository includes a centralized GitHub API client (`github_api.py`) that handles all interactions with the GitHub API. Key features include:

- Fetching issues, pull requests, and contributors
- Detailed data retrieval including comments and events
- Rate limit handling and error management
- Built-in caching system

### Caching System

The caching system (`github_cache.py`) provides efficient data storage and retrieval:

#### Features

- Automatic caching of API responses
- Configurable staleness checks (1 hour for basic data, 15 minutes for state coverage)
- Cache-only mode for offline operation
- Comprehensive metadata including:
  - Date ranges
  - Completeness tracking
  - State coverage
  - Update history

#### Cache Modes

The caching system supports three modes:

1. **Normal Mode** (`use_cache=True`):
   - Uses cached data if fresh
   - Fetches new data if cache is stale
   - Merges new data with existing cache

2. **No Cache** (`use_cache=False`):
   - Always fetches fresh data
   - No data is cached

3. **Cache Only** (`use_cache_only=True`):
   - Uses cached data regardless of staleness
   - Never makes API calls
   - Returns empty results if no cache exists

#### Cache Location

Cache files are stored in the `.cache` directory, with filenames based on the endpoint and parameters to ensure uniqueness.
