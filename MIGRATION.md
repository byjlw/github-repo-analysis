# Migration to GitHub GraphQL API

This document describes the migration from GitHub's REST API to their GraphQL API in the github-repo-analysis project.

## Overview

The project has been migrated from using GitHub's REST API to their GraphQL API. The migration was done in a way that maintains backward compatibility with the existing codebase. This means that all scripts and commands will continue to work as before, but they will now use the GraphQL API internally.

## Architecture

The migration involved creating several new files:

1. `github_graphql_api.py` - The main GraphQL API client
2. `github_graphql_utils.py` - Utility functions for the GraphQL API
3. `github_graphql_issues.py` - Issues-related functionality
4. `github_graphql_pulls.py` - Pull requests-related functionality
5. `github_graphql_contributors.py` - Contributors-related functionality
6. `github_graphql_item_details.py` - Shared functionality for fetching item details
7. `github_api_compat.py` - Compatibility layer that provides the same interface as the original REST API client
8. `github_api_rest.py` - The original REST API client (renamed from `github_api.py`)

The main entry point is still `github_api.py`, which now imports from `github_api_compat.py` to provide the same interface as before.

## Benefits of GraphQL

The migration to GraphQL provides several benefits:

1. **Reduced API calls**: GraphQL allows fetching multiple resources in a single request, reducing the number of API calls needed.
2. **More efficient data fetching**: With GraphQL, you can specify exactly what data you need, reducing the amount of data transferred.
3. **Better rate limit handling**: GraphQL has a different rate limiting system that is based on query complexity rather than the number of requests.
4. **More flexible queries**: GraphQL allows for more complex queries that can fetch related data in a single request.
5. **Access to new features**: GraphQL provides access to features not available in the REST API, such as issue types.

## Issue Type Support

One of the key enhancements in this migration is the addition of issue type support. GitHub's issue types (Bug, Feature, Task, etc.) are only available through the GraphQL API with a special feature flag.

### Implementation

1. **GraphQL Feature Flag**: The GraphQL API client now supports the `GraphQL-Features: issue_types` header for queries that need to access issue types.

2. **Issue Type Queries**: The GraphQL queries for issues have been updated to include the `issueType` field:

```graphql
issueType {
  name
  id
}
```

3. **Visualization**: A new chart function `plot_issues_by_type` has been added to visualize issue trends by type:
   - Shows trends for different issue types (Bug, Feature, Task, etc.)
   - Includes a line for issues with no type
   - Each line represents a different issue type
   - Legend shows current count for each type
   - Types sorted by current count for easy reference

4. **Conditional Generation**: The issue type chart is only generated when issue type data is available, ensuring backward compatibility with repositories that don't use issue types.

## Implementation Details

### GraphQL Queries

The GraphQL API uses queries to fetch data. For example, to fetch repository statistics, we use:

```graphql
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
```

### Pagination

GraphQL uses cursor-based pagination instead of page-based pagination. This is handled by the `fetch_paginated_data` method in `github_graphql_api.py`.

### Data Transformation

The GraphQL API returns data in a different format than the REST API. The code transforms the GraphQL responses to match the format expected by the existing codebase.

## Testing

The migration has been tested to ensure that the functionality is the same as before. This includes:

1. Fetching issues
2. Fetching pull requests
3. Fetching contributors
4. Fetching organization members

## Future Improvements

While the current implementation maintains backward compatibility, there are opportunities for future improvements:

1. **Optimize queries**: The current implementation uses separate queries for different types of data. These could be combined to reduce the number of API calls.
2. **Use GraphQL fragments**: GraphQL fragments could be used to reuse common parts of queries.
3. **Implement batching**: GraphQL allows batching multiple queries into a single request, which could further reduce API calls.
