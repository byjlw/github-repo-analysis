"""
Compatibility layer for the GitHub API.

This module provides the same interface as the original github_api.py but uses
the new GraphQL API internally. This allows existing code to use the new API
without any changes.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Generator
from github_graphql_api import GitHubGraphQLAPI

class GitHubAPI:
    """Centralized GitHub API client for repository analysis."""
    
    BASE_URL = "https://api.github.com"
    
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
        self.graphql_api = GitHubGraphQLAPI(token, use_cache, use_cache_only)
    
    def _get_repository_stats(self, repo: str) -> Dict[str, Any]:
        """Get repository statistics including issue and PR counts.
        
        Args:
            repo: Repository in format 'owner/name'
            
        Returns:
            Repository statistics
        """
        repo_parts = repo.split('/')
        if len(repo_parts) != 2:
            logging.error(f"Invalid repository format: {repo}. Expected format: owner/name")
            return {}
            
        repo_owner, repo_name = repo_parts
        return self.graphql_api.get_repository_stats(repo_owner, repo_name)
    
    def _fetch_item_details(self, repo: str, item_type: str, number: int) -> Optional[Dict[str, Any]]:
        """Fetch full details for an issue or PR including comments and events.
        
        Args:
            repo: Repository in format 'owner/name'
            item_type: Type of item ('issues' or 'pulls')
            number: Item number
            
        Returns:
            Item details including comments and events, or None if fetch fails
        """
        repo_parts = repo.split('/')
        if len(repo_parts) != 2:
            logging.error(f"Invalid repository format: {repo}. Expected format: owner/name")
            return None
            
        repo_owner, repo_name = repo_parts
        return self.graphql_api.fetch_item_details(repo_owner, repo_name, item_type, number)
    
    def _make_paginated_request(self, url: str, params: Optional[Dict] = None) -> Generator[List[Dict], None, None]:
        """Make a paginated request to the GitHub API.
        
        This is a compatibility method that is not used by the GraphQL implementation.
        It's included for API compatibility only.
        
        Args:
            url: The API endpoint URL
            params: Optional query parameters
            
        Yields:
            List of items from each page
        """
        logging.warning("_make_paginated_request is not used in the GraphQL implementation")
        yield []
    
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
        return self.graphql_api.fetch_issues(
            repo, limit, use_cache, use_cache_only, since, include_details
        )
    
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
        return self.graphql_api.fetch_contributors(
            repo_owner, repo_name, since, use_cache, use_cache_only, include_details
        )
    
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
        return self.graphql_api.fetch_org_members(
            org, use_cache, use_cache_only, include_details
        )
    
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
        return self.graphql_api.fetch_pull_requests(
            repo_owner, repo_name, state, since, use_cache, use_cache_only, include_details
        )
