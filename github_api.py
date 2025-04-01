"""
GitHub API client for repository analysis.

This module provides a client for the GitHub API that uses the GraphQL API
internally. It maintains the same interface as the original REST API client
for backward compatibility.
"""

from github_api_compat import GitHubAPI

# Re-export the GitHubAPI class
__all__ = ['GitHubAPI']
