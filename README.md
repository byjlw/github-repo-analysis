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

### External Contributors

This script fetches external contributors to a GitHub repository and their monthly PR counts.

#### Usage

```bash
python external_contributors.py --repo-owner <repo_owner> --repo-name <repo_name> --github-token <github_token> [--filter-organizations <filter_orgs>] [--exclude-contributors <exclude_contributors>] [--since <since_date>] [--output-tsv] [--start-date <start_date>] [--end-date <end_date>]
```

*   `repo_owner`: The owner of the GitHub repository.
*   `repo_name`: The name of the GitHub repository.
*   `github_token`: A valid GitHub token with read access to the repository.
*   `filter_orgs`: A list of organizations to filter out (optional).
*   `exclude_contributors`: A list of contributors to exclude (optional).
*   `since_date`: The date to start fetching data from (YYYY-MM-DD) (optional).
*   `--output-tsv`: Output in TSV format instead of JSON (optional).
*   `start_date`: The date to start displaying in charts (YYYY-MM-DD) (optional).
*   `end_date`: The date to end displaying in charts (YYYY-MM-DD) (optional).

#### Environment Variables

You can also set the following environment variables:

*   `REPO_OWNER`
*   `REPO_NAME`
*   `GITHUB_TOKEN`
*   `FILTER_ORGS`
*   `EXCLUDE_CONTRIBUTORS`

#### Example

```bash
# Fetch all data since 2022
python external_contributors.py --repo-owner pytorch --repo-name torchchat --github-token ghp_g9lT43p6uQxXcK4yN8e7zRfOaM1wSbv --filter-organizations pytorch pytorch-labs --exclude-contributors user1 user2 --since 2022-01-01

# Fetch all data but display charts for 2023 only
python external_contributors.py --repo-owner pytorch --repo-name torchchat --github-token ghp_g9lT43p6uQxXcK4yN8e7zRfOaM1wSbv --filter-organizations pytorch pytorch-labs --start-date 2023-01-01 --end-date 2023-12-31
```

This will fetch external contributors to the `pytorch/torchchat` repository, excluding members of the `pytorch` and `pytorch-labs` organizations, and excluding the contributors `user1` and `user2`. The `--since` parameter determines what data to fetch, while `--start-date` and `--end-date` control what time period to display in the charts.

#### Output

The script outputs the external contributors and their monthly PR counts in JSON format by default:

```json
{
  "user1": {
    "prs": 5,
    "months": {
      "2022-01": 2,
      "2022-02": 3
    }
  },
  "user2": {
    "prs": 3,
    "months": {
      "2022-01": 1,
      "2022-03": 2
    }
  }
}
```

You can use the `--output-tsv` flag to output in TSV format instead:
```
Contributor  Total PRs  Month  PRs
user1        5         2022-01  2
user1        5         2022-02  3
user2        3         2022-01  1
user2        3         2022-03  2
```

#### Visualizations

The script generates charts to help understand contribution patterns:

1. **Contributor Activity** (contributor_trends.png):
   - Shows monthly contributions and unique contributors
   - Blue line: Number of contributions per month
   - Red line: Number of unique contributors per month
   - Can be filtered by date range using --start-date and --end-date

   ![Contributor Trends](docs/contributor_trends.png)

2. **Open Pull Requests** (open_prs_trend.png):
   - Shows the number of open PRs over time
   - Helps track PR review and merge velocity
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
