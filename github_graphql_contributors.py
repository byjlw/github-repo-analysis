import logging
from datetime import datetime
from typing import List, Dict, Optional, Any

def fetch_contributors(
    api,
    repo_owner: str,
    repo_name: str,
    since: Optional[datetime] = None,
    use_cache: Optional[bool] = None,
    use_cache_only: Optional[bool] = None,
    include_details: bool = True
) -> List[Dict[str, Any]]:
    """Fetch contributors for a repository with complete contribution data.
    
    Args:
        api: GitHubGraphQLAPI instance
        repo_owner: Repository owner
        repo_name: Repository name
        since: Optional datetime to fetch contributors since
        use_cache: Override instance cache setting
        use_cache_only: Override instance cache_only setting
        include_details: Whether to fetch detailed contribution data
        
    Returns:
        List of contributors with complete contribution data
    """
    use_cache = api.use_cache if use_cache is None else use_cache
    use_cache_only = api.use_cache_only if use_cache_only is None else use_cache_only
    repo = f"{repo_owner}/{repo_name}"
    
    # Get repository stats first
    repo_stats = api.get_repository_stats(repo_owner, repo_name) if not use_cache_only else {}
    
    endpoint = f"/repos/{repo}/contributors"
    params = {'since': since.isoformat()} if since else {}
    
    cache_path = api.cache.get_cache_path(endpoint, params) if api.cache else None
    cached = None
    if use_cache or use_cache_only:
        cached = api.cache.load(cache_path, use_cache_only) if cache_path else None
        
    if cached:
        cached_data = cached['data']
        metadata = cached['metadata']
        
        # If we have cache and no since filter, or since is within our cached range
        if not since or (metadata.get('date_range') and 
                       since >= datetime.fromisoformat(metadata['date_range']['start'])):
            logging.info(f"Using cached contributors for {repo}")
            if since:
                # Filter cached data by since date
                filtered_contributors = [
                    contributor for contributor in cached_data 
                    if contributor.get('first_contribution_at') and
                    datetime.fromisoformat(contributor['first_contribution_at']) >= since
                ]
                return filtered_contributors
            return cached_data
        elif use_cache_only:
            logging.warning(f"No cached data available for {repo} and cache-only mode is enabled")
            return []
    
    if use_cache_only:
        return []
    
    # Construct GraphQL query for contributors
    query = """
    query($owner: String!, $name: String!, $cursor: String, $since: GitTimestamp) {
      repository(owner: $owner, name: $name) {
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 100, after: $cursor, since: $since) {
                pageInfo {
                  hasNextPage
                  endCursor
                }
                nodes {
                  author {
                    user {
                      login
                      avatarUrl
                      url
                    }
                  }
                  committedDate
                }
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
    
    # Fetch commit history to identify contributors
    commit_authors = {}
    
    for page in api.fetch_paginated_data(
        query, variables, ["repository", "defaultBranchRef", "target", "history"]
    ):
        for commit in page:
            if not commit["author"] or not commit["author"]["user"]:
                continue
                
            user = commit["author"]["user"]
            login = user["login"]
            
            if login not in commit_authors:
                commit_authors[login] = {
                    "login": login,
                    "avatar_url": user["avatarUrl"],
                    "html_url": user["url"],
                    "contributions": 1,
                    "first_contribution_at": commit["committedDate"]
                }
            else:
                commit_authors[login]["contributions"] += 1
                # Update first contribution date if this commit is earlier
                if commit["committedDate"] < commit_authors[login]["first_contribution_at"]:
                    commit_authors[login]["first_contribution_at"] = commit["committedDate"]
    
    # Convert to list format to match REST API
    contributors = list(commit_authors.values())
    
    if use_cache:
        # Calculate date range if we have dates
        dates = [
            datetime.fromisoformat(contributor['first_contribution_at'])
            for contributor in contributors
            if contributor.get('first_contribution_at')
        ]
        date_range = {
            'start': min(dates).isoformat(),
            'end': max(dates).isoformat()
        } if dates else None
        
        if api.cache:
            api.cache.save(
                cache_path,
                contributors,
                metadata={'date_range': date_range},
                repo_stats=repo_stats
            )
    
    return contributors

def fetch_org_members(
    api,
    org: str,
    use_cache: Optional[bool] = None,
    use_cache_only: Optional[bool] = None,
    include_details: bool = True
) -> List[Dict[str, Any]]:
    """Fetch all members of an organization with complete data.
    
    Args:
        api: GitHubGraphQLAPI instance
        org: Organization name
        use_cache: Override instance cache setting
        use_cache_only: Override instance cache_only setting
        include_details: Whether to fetch member details
        
    Returns:
        List of organization members with complete data
    """
    use_cache = api.use_cache if use_cache is None else use_cache
    use_cache_only = api.use_cache_only if use_cache_only is None else use_cache_only
    endpoint = f"/orgs/{org}/members"
    params = {'role': 'all'}
    
    # Get organization stats first
    org_stats = {}
    if not use_cache_only:
        org_query = """
        query($login: String!) {
          organization(login: $login) {
            id
            name
            url
            membersWithRole {
              totalCount
            }
          }
        }
        """
        
        org_variables = {
            "login": org
        }
        
        org_result = api.execute_query(org_query, org_variables)
        if org_result.get("data") and org_result.get("data").get("organization"):
            org_data = org_result["data"]["organization"]
            org_stats = {
                "id": org_data["id"],
                "name": org_data["name"],
                "url": org_data["url"],
                "public_members": org_data["membersWithRole"]["totalCount"]
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
            total_expected = org_stats.get('public_members', 0)
            if total_expected > 0 and metadata['completeness']['cached_count'] < total_expected:
                logging.info(f"Cache is incomplete ({metadata['completeness']['cached_count']}/{total_expected} members), will fetch fresh data")
                cached = None
        
        if cached:
            logging.info(f"Using cached members for organization {org}")
            return cached_data
        elif use_cache_only:
            logging.warning(f"No cached data available for organization {org} and cache-only mode is enabled")
            return []
    
    if use_cache_only:
        return []
    
    # Construct GraphQL query for organization members
    query = """
    query($login: String!, $cursor: String) {
      organization(login: $login) {
        membersWithRole(first: 100, after: $cursor) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            login
            name
            url
            avatarUrl
            email
            company
            location
            bio
          }
        }
      }
    }
    """
    
    variables = {
        "login": org
    }
    
    members = []
    
    # Fetch members with pagination
    for page in api.fetch_paginated_data(query, variables, ["organization", "membersWithRole"]):
        if include_details:
            # Fetch additional details for each member
            detailed_members = []
            for member in page:
                try:
                    # Get organization-specific membership details
                    membership_query = """
                    query($org: String!, $username: String!) {
                      organization(login: $org) {
                        membershipForUser(login: $username) {
                          role
                        }
                      }
                    }
                    """
                    
                    membership_variables = {
                        "org": org,
                        "username": member["login"]
                    }
                    
                    membership_result = api.execute_query(membership_query, membership_variables)
                    
                    if membership_result.get("data") and membership_result.get("data").get("organization") and membership_result.get("data").get("organization").get("membershipForUser"):
                        member["org_membership"] = membership_result["data"]["organization"]["membershipForUser"]
                    
                    detailed_members.append(member)
                except Exception as e:
                    logging.warning(f"Error processing member {member['login']}: {e}")
                    detailed_members.append(member)  # Use basic member data
            page = detailed_members
        
        # Transform the member data to match REST API format
        page = [
            {
                "login": member["login"],
                "html_url": member["url"],
                "avatar_url": member["avatarUrl"],
                "name": member.get("name"),
                "email": member.get("email"),
                "company": member.get("company"),
                "location": member.get("location"),
                "bio": member.get("bio"),
                "type": "User",  # Default type
                "org_membership": member.get("org_membership", {})
            }
            for member in page
        ]
        
        members.extend(page)
    
    if use_cache:
        # Calculate metadata
        member_stats = {
            'total_members': len(members),
            'member_types': {}
        }
        
        if include_details:
            for member in members:
                member_type = member.get('type', 'Unknown')
                member_stats['member_types'][member_type] = member_stats['member_types'].get(member_type, 0) + 1
        
        if api.cache:
            api.cache.save(
                cache_path,
                members,
                metadata={
                    'member_stats': member_stats,
                    'org_stats': org_stats
                }
            )
    
    return members
