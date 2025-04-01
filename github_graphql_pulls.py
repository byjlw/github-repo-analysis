import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from github_graphql_item_details import fetch_pull_request_details

def fetch_pull_requests(
    api,
    repo_owner: str,
    repo_name: str,
    state: str = 'all',
    since: Optional[datetime] = None,
    use_cache: Optional[bool] = None,
    use_cache_only: Optional[bool] = None,
    include_details: bool = True
) -> List[Dict[str, Any]]:
    """Fetch pull requests for a repository with complete data.
    
    Args:
        api: GitHubGraphQLAPI instance
        repo_owner: Repository owner
        repo_name: Repository name
        state: PR state ('open', 'closed', 'all')
        since: Optional datetime to fetch PRs since
        use_cache: Override instance cache setting
        use_cache_only: Override instance cache_only setting
        include_details: Whether to fetch full PR details
        
    Returns:
        List of pull requests with complete data
    """
    use_cache = api.use_cache if use_cache is None else use_cache
    use_cache_only = api.use_cache_only if use_cache_only is None else use_cache_only
    repo = f"{repo_owner}/{repo_name}"
    
    # Get repository stats first
    repo_stats = api.get_repository_stats(repo_owner, repo_name) if not use_cache_only else {}
    
    endpoint = f"/repos/{repo}/pulls"
    params = {
        'state': state,
        'sort': 'created',
        'direction': 'desc'
    }
    
    cache_path = api.cache.get_cache_path(endpoint, params) if api.cache else None
    cached = None
    if use_cache or use_cache_only:
        cached = api.cache.load(cache_path, use_cache_only) if cache_path else None
        
    if cached:
        cached_data = cached['data']
        metadata = cached['metadata']
        
        # Verify cache completeness if not in cache-only mode
        if not use_cache_only and metadata.get('completeness'):
            total_expected = repo_stats.get('total_pull_requests', 0)
            if total_expected > 0 and metadata['completeness']['cached_count'] < total_expected:
                logging.info(f"Cache is incomplete ({metadata['completeness']['cached_count']}/{total_expected} items), will fetch fresh data")
                cached = None
        
        if cached:
            # If we have complete cache and no since filter, or since is within our cached range
            if not since or (metadata.get('date_range') and 
                           since >= datetime.fromisoformat(metadata['date_range']['start'])):
                logging.info(f"Using cached pull requests for {repo}")
                if since:
                    # Filter cached data by since date
                    filtered_prs = [
                        pr for pr in cached_data 
                        if datetime.fromisoformat(pr['created_at']) >= since
                    ]
                    return filtered_prs
                return cached_data
            elif use_cache_only:
                logging.warning(f"No cached data available for {repo} and cache-only mode is enabled")
                return []
    
    if use_cache_only:
        return []
        
    # Map REST API state to GraphQL states
    graphql_states = []
    if state == 'all':
        graphql_states = ["OPEN", "CLOSED", "MERGED"]
    elif state == 'open':
        graphql_states = ["OPEN"]
    elif state == 'closed':
        graphql_states = ["CLOSED", "MERGED"]
    
    # Construct GraphQL query for pull requests
    query = """
    query($owner: String!, $name: String!, $states: [PullRequestState!], $cursor: String) {
      repository(owner: $owner, name: $name) {
        pullRequests(first: 100, after: $cursor, states: $states, orderBy: {field: CREATED_AT, direction: DESC}) {
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
            mergedAt
            url
            author {
              login
              url
              avatarUrl
            }
            baseRefName
            headRefName
            labels(first: 100) {
              nodes {
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
        "states": graphql_states
    }
    
    prs = []
    
    # Fetch PRs with pagination
    for page in api.fetch_paginated_data(query, variables, ["repository", "pullRequests"]):
        if include_details:
            # Fetch full details for each PR
            detailed_prs = []
            for pr in page:
                details = fetch_pull_request_details(api, repo_owner, repo_name, pr['number'])
                if details:
                    detailed_prs.append(details)
            page = detailed_prs
        else:
            # Transform the basic PR data to match REST API format
            page = [
                {
                    "id": pr["id"],
                    "number": pr["number"],
                    "title": pr["title"],
                    "body": pr["body"],
                    "state": pr["state"].lower(),
                    "created_at": pr["createdAt"],
                    "updated_at": pr["updatedAt"],
                    "closed_at": pr["closedAt"],
                    "merged_at": pr["mergedAt"],
                    "html_url": pr["url"],
                    "user": {
                        "login": pr["author"]["login"] if pr["author"] else None,
                        "html_url": pr["author"]["url"] if pr["author"] else None,
                        "avatar_url": pr["author"]["avatarUrl"] if pr["author"] else None
                    },
                    "base": {
                        "ref": pr["baseRefName"]
                    },
                    "head": {
                        "ref": pr["headRefName"]
                    },
                    "labels": [
                        {
                            "name": label["name"],
                            "color": label["color"],
                            "description": label["description"]
                        }
                        for label in pr["labels"]["nodes"]
                    ]
                }
                for pr in page
            ]
        
        # Filter by since date if provided
        if since:
            page = [
                pr for pr in page
                if datetime.fromisoformat(pr['created_at']) >= since
            ]
            
        prs.extend(page)
    
    if use_cache:
        if cached and not since:
            # Merge new PRs with cached PRs
            all_prs = prs + cached['data']
            # Remove duplicates based on PR number
            seen = set()
            unique_prs = []
            for pr in all_prs:
                if pr['number'] not in seen:
                    seen.add(pr['number'])
                    unique_prs.append(pr)
            prs = unique_prs
        
        # Calculate date range and state counts
        if prs:
            date_range = {
                'start': min(pr['created_at'] for pr in prs),
                'end': max(pr.get('updated_at', pr['created_at']) for pr in prs)
            }
            
            state_counts = {}
            for pr in prs:
                pr_state = pr['state']
                state_counts[pr_state] = state_counts.get(pr_state, 0) + 1
        else:
            date_range = None
            state_counts = {}
        
        if api.cache:
            api.cache.save(
                cache_path,
                prs,
                metadata={
                    'date_range': date_range,
                    'state_counts': state_counts
                },
                repo_stats=repo_stats
            )
    
    return prs
