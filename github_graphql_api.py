import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Generator
from github_cache import GitHubCache
from github_graphql_utils import extract_data_from_path
from github_graphql_issues import fetch_issues
from github_graphql_contributors import fetch_contributors, fetch_org_members
from github_graphql_pulls import fetch_pull_requests
from github_graphql_item_details import fetch_item_details

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GitHubGraphQLAPI:
    """Centralized GitHub GraphQL API client for repository analysis."""
    
    GRAPHQL_URL = "https://api.github.com/graphql"
    
    def __init__(self, token: str, use_cache: bool = True, use_cache_only: bool = False):
        """Initialize GitHub GraphQL API client with authentication token.
        
        Args:
            token: GitHub API token
            use_cache: Whether to use caching for API requests
            use_cache_only: If True, only return cached data and never make API calls
        """
        self.headers = {
            'Authorization': f'bearer {token}',
            'Content-Type': 'application/json'
        }
        self.use_cache = use_cache
        self.use_cache_only = use_cache_only
        self.cache = GitHubCache() if use_cache else None
    
    def execute_query(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a GraphQL query against the GitHub API.
        
        Args:
            query: GraphQL query string
            variables: Variables for the GraphQL query
            
        Returns:
            Response data from the GraphQL API
        """
        if self.use_cache_only:
            logging.warning("Cache-only mode enabled, but no cache found for this query")
            return {"data": None}
            
        payload = {
            "query": query,
            "variables": variables
        }
        
        response = requests.post(self.GRAPHQL_URL, json=payload, headers=self.headers)
        
        if response.status_code != 200:
            logging.error(f"GraphQL request failed: {response.status_code} - {response.text}")
            return {"data": None, "errors": [{"message": f"Request failed with status code {response.status_code}"}]}
            
        result = response.json()
        
        if "errors" in result:
            logging.error(f"GraphQL query returned errors: {result['errors']}")
            
        return result
    
    def get_repository_stats(self, repo_owner: str, repo_name: str) -> Dict[str, Any]:
        """Get repository statistics including issue and PR counts.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            
        Returns:
            Repository statistics
        """
        query = """
        query($owner: String!, $name: String!) {
          repository(owner: $owner, name: $name) {
            id
            name
            description
            url
            createdAt
            updatedAt
            openIssues: issues(states: OPEN) {
              totalCount
            }
            closedIssues: issues(states: CLOSED) {
              totalCount
            }
            openPullRequests: pullRequests(states: OPEN) {
              totalCount
            }
            closedPullRequests: pullRequests(states: CLOSED, first: 0) {
              totalCount
            }
            mergedPullRequests: pullRequests(states: MERGED, first: 0) {
              totalCount
            }
            stargazerCount
            forkCount
            watchers {
              totalCount
            }
          }
        }
        """
        
        variables = {
            "owner": repo_owner,
            "name": repo_name
        }
        
        result = self.execute_query(query, variables)
        
        if not result.get("data") or not result.get("data").get("repository"):
            logging.error(f"Failed to fetch repository stats for {repo_owner}/{repo_name}")
            return {}
            
        repo_data = result["data"]["repository"]
        
        # Transform the GraphQL response to match the REST API format
        return {
            "id": repo_data["id"],
            "name": repo_data["name"],
            "description": repo_data["description"],
            "html_url": repo_data["url"],
            "created_at": repo_data["createdAt"],
            "updated_at": repo_data["updatedAt"],
            "open_issues_count": repo_data["openIssues"]["totalCount"],
            "closed_issues_count": repo_data["closedIssues"]["totalCount"],
            "open_pull_requests_count": repo_data["openPullRequests"]["totalCount"],
            "closed_pull_requests_count": repo_data["closedPullRequests"]["totalCount"],
            "merged_pull_requests_count": repo_data["mergedPullRequests"]["totalCount"],
            "total_pull_requests": (
                repo_data["openPullRequests"]["totalCount"] + 
                repo_data["closedPullRequests"]["totalCount"] + 
                repo_data["mergedPullRequests"]["totalCount"]
            ),
            "stargazers_count": repo_data["stargazerCount"],
            "forks_count": repo_data["forkCount"],
            "watchers_count": repo_data["watchers"]["totalCount"]
        }
    
    def fetch_paginated_data(self, query: str, variables: Dict[str, Any], extract_path: List[str]) -> Generator[List[Dict], None, None]:
        """Fetch paginated data from the GraphQL API.
        
        Args:
            query: GraphQL query string with pagination
            variables: Variables for the GraphQL query
            extract_path: Path to the nodes in the response (e.g., ["repository", "issues"])
            
        Yields:
            List of items from each page
        """
        has_next_page = True
        cursor = None
        
        while has_next_page:
            # Update cursor for pagination
            if cursor:
                variables["cursor"] = cursor
                
            result = self.execute_query(query, variables)
            
            if not result.get("data"):
                logging.error("Failed to fetch paginated data")
                break
                
            # Navigate to the data using the extract_path
            data = extract_data_from_path(result["data"], extract_path)
            
            if not data:
                break
                
            # Extract page info and nodes
            page_info = data["pageInfo"]
            nodes = data["nodes"]
            
            if not nodes:
                break
                
            yield nodes
            
            # Check if there are more pages
            has_next_page = page_info["hasNextPage"]
            if has_next_page:
                cursor = page_info["endCursor"]
            else:
                break
    
    # Public API methods that delegate to specialized modules
    def fetch_issues(self, repo: str, limit: Optional[int] = None, use_cache: Optional[bool] = None, 
                    use_cache_only: Optional[bool] = None, since: Optional[datetime] = None, 
                    include_details: bool = True) -> List[Dict[str, Any]]:
        """Fetch issues (excluding PRs) for a repository."""
        return fetch_issues(self, repo, limit, use_cache, use_cache_only, since, include_details)
    
    def fetch_contributors(self, repo_owner: str, repo_name: str, since: Optional[datetime] = None,
                          use_cache: Optional[bool] = None, use_cache_only: Optional[bool] = None,
                          include_details: bool = True) -> List[Dict[str, Any]]:
        """Fetch contributors for a repository with complete contribution data."""
        return fetch_contributors(self, repo_owner, repo_name, since, use_cache, use_cache_only, include_details)
    
    def fetch_org_members(self, org: str, use_cache: Optional[bool] = None,
                         use_cache_only: Optional[bool] = None, include_details: bool = True) -> List[Dict[str, Any]]:
        """Fetch all members of an organization with complete data."""
        return fetch_org_members(self, org, use_cache, use_cache_only, include_details)
    
    def fetch_pull_requests(self, repo_owner: str, repo_name: str, state: str = 'all',
                           since: Optional[datetime] = None, use_cache: Optional[bool] = None,
                           use_cache_only: Optional[bool] = None, include_details: bool = True) -> List[Dict[str, Any]]:
        """Fetch pull requests for a repository with complete data."""
        return fetch_pull_requests(self, repo_owner, repo_name, state, since, use_cache, use_cache_only, include_details)
    
    def fetch_item_details(self, repo_owner: str, repo_name: str, item_type: str, number: int) -> Optional[Dict[str, Any]]:
        """Fetch full details for an issue or PR including comments and events."""
        return fetch_item_details(self, repo_owner, repo_name, item_type, number)
