import requests
import logging
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Generator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GitHubAPI:
    """Centralized GitHub API client for repository analysis."""
    
    BASE_URL = "https://api.github.com"
    CACHE_DIR = ".cache"
    
    def __init__(self, token: str, use_cache: bool = True, use_cache_only: bool = False):
        """Initialize GitHub API client with authentication token.
        
        Args:
            token: GitHub API token
            use_cache: Whether to use caching for API requests
            use_cache_only: If True, only return cached data and never make API calls
        """
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {token}',
            'Content-Type': 'application/json'
        }
        self.use_cache = use_cache
        self.use_cache_only = use_cache_only
        
        # Create cache directory if it doesn't exist
        if self.use_cache and not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)
    
    def _get_cache_path(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate a cache file path for an API endpoint.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            
        Returns:
            Cache file path
        """
        # Create a unique cache key based on the endpoint and params
        cache_key = endpoint.replace('/', '_')
        if params:
            # Sort params to ensure consistent cache keys
            param_str = '_'.join(f"{k}_{v}" for k, v in sorted(params.items()))
            cache_key = f"{cache_key}_{param_str}"
        return os.path.join(self.CACHE_DIR, f"{cache_key}.json")
    
    def _get_repository_stats(self, repo: str) -> Dict[str, Any]:
        """Get repository statistics including issue and PR counts.
        
        Args:
            repo: Repository in format 'owner/name'
            
        Returns:
            Repository statistics
        """
        url = f"{self.BASE_URL}/repos/{repo}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            logging.error(f"Failed to fetch repository stats: {response.json().get('message', 'No error message')}")
            return {}
        return response.json()
    
    def _fetch_item_details(self, repo: str, item_type: str, number: int) -> Optional[Dict[str, Any]]:
        """Fetch full details for an issue or PR including comments and events.
        
        Args:
            repo: Repository in format 'owner/name'
            item_type: Type of item ('issues' or 'pulls')
            number: Item number
            
        Returns:
            Item details including comments and events, or None if fetch fails
        """
        try:
            # Get main item details
            url = f"{self.BASE_URL}/repos/{repo}/{item_type}/{number}"
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                logging.warning(f"Failed to fetch {item_type} {number}: {response.status_code}")
                return None
            
            item = response.json()
            
            try:
                # Get comments
                comments_url = f"{url}/comments"
                comments = []
                for page in self._make_paginated_request(comments_url):
                    comments.extend(page)
                item['comments_data'] = comments
            except Exception as e:
                logging.warning(f"Failed to fetch comments for {item_type} {number}: {e}")
                item['comments_data'] = []
            
            try:
                # Get events
                events_url = f"{url}/events"
                events = []
                for page in self._make_paginated_request(events_url):
                    events.extend(page)
                item['events_data'] = events
            except Exception as e:
                logging.warning(f"Failed to fetch events for {item_type} {number}: {e}")
                item['events_data'] = []
            
            return item
            
        except Exception as e:
            logging.warning(f"Error fetching details for {item_type} {number}: {e}")
            return None
    
    def _save_cache(self, path: str, data: Any, metadata: Optional[Dict] = None, repo_stats: Optional[Dict] = None) -> None:
        """Save data to cache file with comprehensive metadata.
        
        Args:
            path: Cache file path
            data: Data to cache
            metadata: Optional metadata about the cached data
            repo_stats: Optional repository statistics
        """
        # Calculate item counts and ranges based on data type
        if data:
            # Determine data type based on fields present
            sample_item = data[0] if isinstance(data, list) and data else {}
            
            # Issues and PRs have created_at and state
            if 'created_at' in sample_item:
                date_range = {
                    'start': min(item['created_at'] for item in data),
                    'end': max(item.get('updated_at', item['created_at']) for item in data)
                }
                state_counts = {}
                for item in data:
                    if 'state' in item:
                        state = item['state']
                        state_counts[state] = state_counts.get(state, 0) + 1
            
            # Contributors have contributions and first_contribution_at
            elif 'contributions' in sample_item:
                date_range = None
                if any('first_contribution_at' in item for item in data):
                    dates = [
                        item['first_contribution_at']
                        for item in data
                        if 'first_contribution_at' in item
                    ]
                    if dates:
                        date_range = {
                            'start': min(dates),
                            'end': max(dates)
                        }
                state_counts = {
                    'total_contributions': sum(item['contributions'] for item in data)
                }
            
            # Organization members have type and login
            elif 'type' in sample_item:
                date_range = None
                state_counts = {}
                for item in data:
                    member_type = item.get('type', 'Unknown')
                    state_counts[member_type] = state_counts.get(member_type, 0) + 1
            
            # Simple list of strings (e.g., member logins)
            elif all(isinstance(item, str) for item in data):
                date_range = None
                state_counts = {'total_count': len(data)}
            
            else:
                date_range = None
                state_counts = {'total_count': len(data)}
        else:
            date_range = None
            state_counts = {}
        
        # Build comprehensive metadata
        completeness = {
            'cached_count': len(data)
        }
        
        # Add total count from repo stats if available
        if repo_stats:
            if 'open_issues_count' in repo_stats:
                completeness['total_count'] = repo_stats.get('open_issues_count', 0) + repo_stats.get('closed_issues_count', 0)
            elif 'public_members' in repo_stats:
                completeness['total_count'] = repo_stats.get('public_members', 0)
        else:
            completeness['total_count'] = len(data)
        
        # Add last item number if items have numbers
        sample_item = data[0] if isinstance(data, list) and data else {}
        if 'number' in sample_item:
            completeness['last_item_number'] = max(item['number'] for item in data) if data else 0
        
        full_metadata = {
            'date_range': date_range,
            'completeness': completeness,
            'state_coverage': {
                **state_counts,
                'last_state_check': datetime.utcnow().isoformat()
            },
            **(metadata or {})
        }
        
        # Add this update to history
        update_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'items_count': len(data),
            'state_counts': state_counts
        }
        
        cache_content = {
            'data': data,
            'metadata': full_metadata,
            'last_updated': datetime.utcnow().isoformat(),
            'update_history': [update_record]
        }
        
        # Merge with existing cache history if it exists
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    existing_cache = json.load(f)
                    if 'update_history' in existing_cache:
                        cache_content['update_history'] = existing_cache['update_history'] + [update_record]
            except Exception as e:
                logging.warning(f"Failed to merge cache history: {e}")
        
        with open(path, 'w') as f:
            json.dump(cache_content, f, indent=4)
    
    def _load_cache(self, path: str) -> Optional[Dict]:
        """Load data from cache file if it exists and is not stale.
        
        Args:
            path: Cache file path
            
        Returns:
            Cache data if available and not stale, None otherwise
        """
        if not os.path.exists(path):
            return None
            
        with open(path, 'r') as f:
            cache = json.load(f)
        
        # Check basic staleness (1 hour)
        last_updated = datetime.fromisoformat(cache['last_updated'])
        if datetime.utcnow() - last_updated > timedelta(hours=1):
            logging.info("Cache is stale (older than 1 hour), will fetch fresh data")
            return None
            
        # Check state coverage staleness (15 minutes)
        if 'metadata' in cache and 'state_coverage' in cache['metadata']:
            last_state_check = datetime.fromisoformat(cache['metadata']['state_coverage']['last_state_check'])
            if datetime.utcnow() - last_state_check > timedelta(minutes=15):
                logging.info("State coverage is stale (older than 15 minutes), will fetch fresh data")
                return None
        
        return cache
    
    def _make_paginated_request(self, url: str, params: Optional[Dict] = None) -> Generator[List[Dict], None, None]:
        """Make a paginated request to the GitHub API.
        
        Args:
            url: The API endpoint URL
            params: Optional query parameters
            
        Yields:
            List of items from each page
        """
        if params is None:
            params = {}
        
        while url:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200:
                logging.error(f"API request failed: {response.json().get('message', 'No error message')}")
                break
                
            data = response.json()
            if not data:  # No more items to fetch
                break
                
            yield data
            
            # Get next page URL from Link header
            url = response.links.get('next', {}).get('url')
            params = {}  # Reset params for next page as they're included in the URL
    
    def fetch_issues(
        self,
        repo: str,
        limit: Optional[int] = None,
        use_cache: Optional[bool] = None,
        use_cache_only: Optional[bool] = None,
        since: Optional[datetime] = None,
        include_details: bool = True
    ) -> List[Dict[str, Any]]:
        """Fetch issues (excluding PRs) for a repository.
        
        Args:
            repo: Repository in format 'owner/name'
            limit: Optional maximum number of issues to fetch
            use_cache: Override instance cache setting
            use_cache_only: Override instance cache_only setting
            since: Optional datetime to fetch issues since
            include_details: Whether to fetch full issue details
            
        Returns:
            List of issues with complete data
        """
        use_cache = self.use_cache if use_cache is None else use_cache
        use_cache_only = self.use_cache_only if use_cache_only is None else use_cache_only
        endpoint = f"/repos/{repo}/issues"
        url = f"{self.BASE_URL}{endpoint}"
        
        # Get repository stats first
        repo_stats = self._get_repository_stats(repo) if not use_cache_only else {}
        
        params = {
            'state': 'all',
            'per_page': 100,
            'direction': 'desc'
        }
        
        cache_path = self._get_cache_path(endpoint, params)
        cached = None
        if use_cache or use_cache_only:
            cached = self._load_cache(cache_path)
            
        if cached:
            cached_data = cached['data']
            metadata = cached['metadata']
            
            # Verify cache completeness
            if metadata.get('completeness'):
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
            
        # Determine date range for API request
        params['since'] = since.isoformat() if since else None
        if cached and not since:
            # If we have cache but need newer data, start from last cached issue
            newest_date = max(
                datetime.fromisoformat(issue['created_at']) 
                for issue in cached['data']
            )
            params['since'] = newest_date.isoformat()
        
        issues = []
        for page in self._make_paginated_request(url, params):
            # Filter out pull requests
            actual_issues = [issue for issue in page if not issue.get('pull_request')]
            
            if include_details:
                # Fetch full details for each issue
                detailed_issues = []
                for issue in actual_issues:
                    details = self._fetch_item_details(repo, 'issues', issue['number'])
                    if details:
                        detailed_issues.append(details)
                actual_issues = detailed_issues
            
            issues.extend(actual_issues)
            
            if limit and len(issues) >= limit:
                logging.warning(f"Fetched maximum number of issues ({limit}). Results may be incomplete.")
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
            
            self._save_cache(cache_path, issues, repo_stats=repo_stats)
            
        return issues[:limit] if limit else issues
    
    def fetch_contributors(
        self,
        repo_owner: str,
        repo_name: str,
        since: Optional[datetime] = None,
        use_cache: Optional[bool] = None,
        use_cache_only: Optional[bool] = None,
        include_details: bool = True
    ) -> List[Dict[str, Any]]:
        """Fetch contributors for a repository with complete contribution data.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            since: Optional datetime to fetch contributors since
            use_cache: Override instance cache setting
            use_cache_only: Override instance cache_only setting
            include_details: Whether to fetch detailed contribution data
            
        Returns:
            List of contributors with complete contribution data
        """
        use_cache = self.use_cache if use_cache is None else use_cache
        use_cache_only = self.use_cache_only if use_cache_only is None else use_cache_only
        repo = f"{repo_owner}/{repo_name}"
        
        # Get repository stats first
        repo_stats = self._get_repository_stats(repo) if not use_cache_only else {}
        
        endpoint = f"/repos/{repo}/contributors"
        url = f"{self.BASE_URL}{endpoint}"
        params = {'since': since.isoformat()} if since else {}
        
        cache_path = self._get_cache_path(endpoint, params)
        cached = None
        if use_cache or use_cache_only:
            cached = self._load_cache(cache_path)
            
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
        
        contributors = []
        for page in self._make_paginated_request(url, params):
            contributors.extend(page)
            
            if include_details:
                # Fetch additional contribution data for each contributor
                for contributor in contributors:
                    try:
                        # Get first contribution date
                        commits_url = f"{self.BASE_URL}/repos/{repo}/commits"
                        params = {
                            'author': contributor['login'],
                            'per_page': 1,
                            'sort': 'created',
                            'order': 'asc'
                        }
                        response = requests.get(commits_url, headers=self.headers, params=params)
                        if response.status_code == 200 and response.json():
                            first_commit = response.json()[0]
                            contributor['first_contribution_at'] = first_commit['commit']['author']['date']
                        else:
                            logging.warning(f"Failed to fetch first commit for {contributor['login']}: {response.status_code}")
                    except Exception as e:
                        logging.warning(f"Error fetching first commit for {contributor['login']}: {e}")
                    
                    try:
                        # Get contribution stats
                        stats_url = f"{self.BASE_URL}/repos/{repo}/stats/contributors"
                        response = requests.get(stats_url, headers=self.headers)
                        if response.status_code == 200:
                            stats = response.json()
                            for stat in stats:
                                if stat['author']['login'] == contributor['login']:
                                    contributor['contribution_stats'] = stat
                                    break
                        else:
                            logging.warning(f"Failed to fetch contribution stats: {response.status_code}")
                    except Exception as e:
                        logging.warning(f"Error fetching contribution stats: {e}")
        
        if use_cache:
            if cached and not since:
                # Merge new contributors with cached contributors
                all_contributors = contributors + cached['data']
                # Remove duplicates based on login
                seen = set()
                unique_contributors = []
                for contributor in all_contributors:
                    if contributor['login'] not in seen:
                        seen.add(contributor['login'])
                        unique_contributors.append(contributor)
                contributors = unique_contributors
            
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
            
            self._save_cache(
                cache_path,
                contributors,
                metadata={'date_range': date_range},
                repo_stats=repo_stats
            )
        
        return contributors
    
    def fetch_org_members(
        self,
        org: str,
        use_cache: Optional[bool] = None,
        use_cache_only: Optional[bool] = None,
        include_details: bool = True
    ) -> List[Dict[str, Any]]:
        """Fetch all members of an organization with complete data.
        
        Args:
            org: Organization name
            use_cache: Override instance cache setting
            use_cache_only: Override instance cache_only setting
            include_details: Whether to fetch member details
            
        Returns:
            List of organization members with complete data
        """
        use_cache = self.use_cache if use_cache is None else use_cache
        use_cache_only = self.use_cache_only if use_cache_only is None else use_cache_only
        endpoint = f"/orgs/{org}/members"
        url = f"{self.BASE_URL}{endpoint}"
        params = {'role': 'all'}
        
        # Get organization stats first
        org_stats_url = f"{self.BASE_URL}/orgs/{org}"
        org_stats = {}
        if not use_cache_only:
            response = requests.get(org_stats_url, headers=self.headers)
            if response.status_code == 200:
                org_stats = response.json()
        
        cache_path = self._get_cache_path(endpoint, params)
        cached = None
        if use_cache or use_cache_only:
            cached = self._load_cache(cache_path)
            
        if cached:
            cached_data = cached['data']
            metadata = cached['metadata']
            
            # Verify cache completeness
            if metadata.get('completeness'):
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
        
        members = []
        for page in self._make_paginated_request(url, params):
            if include_details:
                # Fetch additional details for each member
                detailed_members = []
                for member in page:
                    try:
                        # Get user details
                        user_url = f"{self.BASE_URL}/users/{member['login']}"
                        response = requests.get(user_url, headers=self.headers)
                        if response.status_code == 200:
                            user_details = response.json()
                            try:
                                # Get organization-specific membership details
                                membership_url = f"{self.BASE_URL}/orgs/{org}/memberships/{member['login']}"
                                membership_response = requests.get(membership_url, headers=self.headers)
                                if membership_response.status_code == 200:
                                    user_details['org_membership'] = membership_response.json()
                                else:
                                    logging.warning(f"Failed to fetch org membership for {member['login']}: {membership_response.status_code}")
                            except Exception as e:
                                logging.warning(f"Error fetching org membership for {member['login']}: {e}")
                            detailed_members.append(user_details)
                        else:
                            logging.warning(f"Failed to fetch user details for {member['login']}: {response.status_code}")
                            detailed_members.append(member)  # Use basic member data
                    except Exception as e:
                        logging.warning(f"Error processing member {member['login']}: {e}")
                        detailed_members.append(member)  # Use basic member data
                page = detailed_members
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
            
            self._save_cache(
                cache_path,
                members,
                metadata={
                    'member_stats': member_stats,
                    'org_stats': org_stats
                }
            )
        
        return members
    
    def fetch_pull_requests(
        self,
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
        use_cache = self.use_cache if use_cache is None else use_cache
        use_cache_only = self.use_cache_only if use_cache_only is None else use_cache_only
        repo = f"{repo_owner}/{repo_name}"
        
        # Get repository stats first
        repo_stats = self._get_repository_stats(repo) if not use_cache_only else {}
        
        endpoint = f"/repos/{repo}/pulls"
        url = f"{self.BASE_URL}{endpoint}"
        params = {
            'state': state,
            'sort': 'created',
            'direction': 'desc'
        }
        
        cache_path = self._get_cache_path(endpoint, params)
        cached = None
        if use_cache or use_cache_only:
            cached = self._load_cache(cache_path)
            
        if cached:
            cached_data = cached['data']
            metadata = cached['metadata']
            
            # Verify cache completeness
            if metadata.get('completeness'):
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
            
        # Determine date range for API request
        if since:
            params['since'] = since.isoformat()
        elif cached:
            # If we have cache but need newer data, start from last cached PR
            newest_date = max(
                datetime.fromisoformat(pr['created_at']) 
                for pr in cached['data']
            )
            params['since'] = newest_date.isoformat()
        
        prs = []
        for page in self._make_paginated_request(url, params):
            if include_details:
                # Fetch full details for each PR
                detailed_prs = []
                for pr in page:
                    try:
                        details = self._fetch_item_details(repo, 'pulls', pr['number'])
                        if details:
                            try:
                                # Also fetch review data
                                reviews_url = f"{url}/{pr['number']}/reviews"
                                reviews = []
                                for review_page in self._make_paginated_request(reviews_url):
                                    reviews.extend(review_page)
                                details['reviews'] = reviews
                            except Exception as e:
                                logging.warning(f"Failed to fetch reviews for PR {pr['number']}: {e}")
                                details['reviews'] = []
                            detailed_prs.append(details)
                        else:
                            # If details fetch failed, use basic PR data
                            detailed_prs.append(pr)
                    except Exception as e:
                        logging.warning(f"Error processing PR {pr['number']}: {e}")
                        detailed_prs.append(pr)
                page = detailed_prs
            
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
                    state = pr['state']
                    state_counts[state] = state_counts.get(state, 0) + 1
            else:
                date_range = None
                state_counts = {}
            
            self._save_cache(
                cache_path,
                prs,
                metadata={
                    'date_range': date_range,
                    'state_counts': state_counts
                },
                repo_stats=repo_stats
            )
        
        return prs
