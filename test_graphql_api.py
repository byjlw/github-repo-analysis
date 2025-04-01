#!/usr/bin/env python3
"""
Test script for the GitHub GraphQL API implementation.

This script tests the basic functionality of the GitHub GraphQL API implementation
by fetching issues, pull requests, contributors, and organization members for a
repository.
"""

import os
import sys
import argparse
from github_api import GitHubAPI

def test_issues(api, repo):
    """Test fetching issues."""
    print(f"\nTesting issues for {repo}...")
    issues = api.fetch_issues(repo, limit=5, include_details=False)
    print(f"Fetched {len(issues)} issues")
    if issues:
        print(f"First issue: #{issues[0]['number']} - {issues[0]['title']}")

def test_pull_requests(api, repo_owner, repo_name):
    """Test fetching pull requests."""
    print(f"\nTesting pull requests for {repo_owner}/{repo_name}...")
    prs = api.fetch_pull_requests(repo_owner, repo_name, limit=5, include_details=False)
    print(f"Fetched {len(prs)} pull requests")
    if prs:
        print(f"First PR: #{prs[0]['number']} - {prs[0]['title']}")

def test_contributors(api, repo_owner, repo_name):
    """Test fetching contributors."""
    print(f"\nTesting contributors for {repo_owner}/{repo_name}...")
    contributors = api.fetch_contributors(repo_owner, repo_name, include_details=False)
    print(f"Fetched {len(contributors)} contributors")
    if contributors:
        print(f"First contributor: {contributors[0]['login']} - {contributors[0]['contributions']} contributions")

def test_org_members(api, org):
    """Test fetching organization members."""
    print(f"\nTesting organization members for {org}...")
    members = api.fetch_org_members(org, include_details=False)
    print(f"Fetched {len(members)} members")
    if members:
        print(f"First member: {members[0]['login']}")

def main():
    parser = argparse.ArgumentParser(description="Test the GitHub GraphQL API implementation")
    parser.add_argument("--repo", help="Repository in format 'owner/name'", default="octocat/Hello-World")
    parser.add_argument("--org", help="Organization name", default="github")
    parser.add_argument("--token", help="GitHub API token", default=os.environ.get("GITHUB_TOKEN"))
    
    args = parser.parse_args()
    
    if not args.token:
        print("Error: GitHub token is required. Set the GITHUB_TOKEN environment variable or use --token.")
        sys.exit(1)
    
    repo_parts = args.repo.split('/')
    if len(repo_parts) != 2:
        print(f"Error: Invalid repository format: {args.repo}. Expected format: owner/name")
        sys.exit(1)
    
    repo_owner, repo_name = repo_parts
    
    api = GitHubAPI(args.token)
    
    print(f"Testing GitHub GraphQL API implementation with repository {args.repo} and organization {args.org}")
    
    test_issues(api, args.repo)
    test_pull_requests(api, repo_owner, repo_name)
    test_contributors(api, repo_owner, repo_name)
    test_org_members(api, args.org)
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    main()
