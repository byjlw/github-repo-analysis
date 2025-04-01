import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from github_graphql_item_details import fetch_item_details

def fetch_issues(
    api,
    repo: str,
    limit: Optional[int] = None,
    use_cache: Optional[bool] = None,
    use_cache_only: Optional[bool] = None,
    since: Optional[datetime] = None,
    include_details: bool = True
) -> List[Dict[str, Any]]:
    """Fetch issues (excluding PRs) for a repository.
    
    Args:
        api: GitHubGraphQLAPI instance
        repo: Repository in format 'owner/name'
        limit: Optional maximum number of issues to fetch
        use_cache: Override instance cache setting
        use_cache_only: Override instance cache_only setting
        since: Optional datetime to fetch issues since
        include_details: Whether to fetch full issue details
        
    Returns:
        List of issues with complete data
    """
    use_cache = api.use_cache if use_cache is None else use_cache
    use_cache_only = api.use_cache_only if use_cache_only is None else use_cache_only
    
    repo_parts = repo.split('/')
    if len(repo_parts) != 2:
        logging.error(f"Invalid repository format: {repo}. Expected format: owner/name")
        return []
        
    repo_owner, repo_name = repo_parts
    
    # Get repository stats first
    repo_stats = api.get_repository_stats(repo_owner, repo_name) if not use_cache_only else {}
    
    endpoint = f"/repos/{repo}/issues"
    cache_path = api.cache.get_cache_path(endpoint, {"state": "all"}) if api.cache else None
    cached = None
    
    if use_cache or use_cache_only:
        cached = api.cache.load(cache_path, use_cache_only) if cache_path else None
        
    if cached:
        cached_data = cached['data']
        metadata = cached['metadata']
        
        # Verify cache completeness if not in cache-only mode
        if not use_cache_only and metadata.get('completeness'):
            total_expected = repo_stats.get('open_issues_count', 0) + repo_stats.get('closed_issues_count', 0)
            if total_expected > 0 and metadata['completeness']['cached_count'] < total_expected:
                logging.info(f"Cache is incomplete ({metadata['completeness']['cached_count']}/{total_expected} items), will fetch fresh data")
                cached = None
        
        if cached:
            # If we have complete cache and no since filter, or since is within our cached range
            if not since or (metadata.get('date_range') and 
                           since >= datetime.fromisoformat(metadata['date_range']['start'])):
                logging.info(f"Using cached issues for {repo}")
                if since:
                    # Filter cached data by since date
                    filtered_issues = [
                        issue for issue in cached_data 
                        if datetime.fromisoformat(issue['created_at']) >= since
                    ]
                    return filtered_issues[:limit] if limit else filtered_issues
                return cached_data[:limit] if limit else cached_data
            elif use_cache_only:
                logging.warning(f"No cached data available for {repo} and cache-only mode is enabled")
                return []
    
    if use_cache_only:
        return []
    
    # Construct GraphQL query for issues
    query = """
    query($owner: String!, $name: String!, $cursor: String, $since: DateTime) {
      repository(owner: $owner, name: $name) {
        issues(first: 100, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}, filterBy: {since: $since}) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            id
            number
            title
            body
            state
            createdAt
            updatedAt
            closedAt
            url
            author {
              login
              url
              avatarUrl
            }
            issueType {
              name
              id
            }
            labels(first: 100) {
              totalCount
              nodes {
                id
                name
                color
                description
              }
            }
          }
        }
      }
    }
    """
    
    variables = {
        "owner": repo_owner,
        "name": repo_name,
        "since": since.isoformat() if since else None
    }
    
    issues = []
    
    # Fetch issues with pagination
    for page in api.fetch_paginated_data(query, variables, ["repository", "issues"], use_issue_types=True):
        # Filter out pull requests (GraphQL already does this by using the issues field)
        
        if include_details:
            # Fetch full details for each issue
            detailed_issues = []
            for issue in page:
                details = fetch_item_details(api, repo_owner, repo_name, 'issues', issue['number'])
                if details:
                    detailed_issues.append(details)
            page = detailed_issues
        else:
            # Transform the basic issue data to match REST API format
            page = [
                {
                    "id": issue["id"],
                    "number": issue["number"],
                    "title": issue["title"],
                    "body": issue["body"],
                    "state": issue["state"].lower(),
                    "created_at": issue["createdAt"],
                    "updated_at": issue["updatedAt"],
                    "closed_at": issue["closedAt"],
                    "html_url": issue["url"],
                    "user": {
                        "login": issue["author"]["login"] if issue["author"] else None,
                        "html_url": issue["author"]["url"] if issue["author"] else None,
                        "avatar_url": issue["author"]["avatarUrl"] if issue["author"] else None
                    },
                    "labels": [
                        {
                            "name": label["name"],
                            "color": label["color"],
                            "description": label["description"]
                        }
                        for label in issue["labels"]["nodes"]
                    ],
                    "issue_type": issue["issueType"]["name"] if issue.get("issueType") else None
                }
                for issue in page
            ]
        
        issues.extend(page)
        
        if limit and len(issues) >= limit:
            logging.warning(f"Fetched maximum number of issues ({limit}). Results may be incomplete.")
            issues = issues[:limit]
            break
    
    if use_cache:
        if cached and not since:
            # Merge new issues with cached issues
            all_issues = issues + cached['data']
            # Remove duplicates based on issue ID
            seen = set()
            unique_issues = []
            for issue in all_issues:
                if issue['id'] not in seen:
                    seen.add(issue['id'])
                    unique_issues.append(issue)
            issues = unique_issues
        
        if api.cache:
            api.cache.save(cache_path, issues, repo_stats=repo_stats)
        
    return issues
