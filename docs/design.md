# Design Documentation

This document explains how the github-repo-analysis system works internally and how its components interact.

## System Architecture

The system is built around a central GitHub API client with specialized analysis modules that process and visualize specific aspects of repository data. The system now supports both REST and GraphQL APIs with a compatibility layer to maintain backward compatibility:

```
                                    ┌─────────────────┐
                                    │                 │
                                    │   GitHub API    │
                                    │                 │
                                    └────────┬────────┘
                                            │
                                    ┌────────┴────────┐
                                    │                 │
                                    │  github_api.py  │
                                    │                 │
                                    └────────┬────────┘
                                            │
                                    ┌────────┴────────┐
                                    │                 │
                                    │github_api_compat.py│
                                    │                 │
                                    └────────┬────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
            ┌───────┴───────┐      ┌───────┴───────┐      ┌───────┴───────┐
            │               │      │               │      │               │
            │github_api_rest.py│   │github_graphql_api.py│ │github_cache.py│
            │               │      │               │      │               │
            └───────────────┘      └───────┬───────┘      └───────────────┘
                                          │
                    ┌───────────────────────────────────────────────┐
                    │                     │                         │
            ┌───────┴───────┐    ┌───────┴───────┐         ┌───────┴───────┐
            │               │    │               │         │               │
            │github_graphql_utils.py│github_graphql_issues.py│github_graphql_pulls.py│
            │               │    │               │         │               │
            └───────────────┘    └───────────────┘         └───────────────┘
                                                           │
                                                   ┌───────┴───────┐
                                                   │               │
                                                   │github_graphql_contributors.py│
                                                   │               │
                                                   └───────┬───────┘
                                                          │
                                                   ┌──────┴──────┐
                                                   │             │
                                                   │github_graphql_item_details.py│
                                                   │             │
                                                   └─────────────┘


                    ┌───────────────────────┬───────────────────────┐
                    │                       │                       │
            ┌───────┴───────┐      ┌───────┴───────┐      ┌───────┴───────┐
            │               │      │               │      │               │
            │ issue_stats.py│      │external_contributors.py│test_graphql_api.py│
            │               │      │               │      │               │
            └───────┬───────┘      └───────┬───────┘      └───────────────┘
                    │                      │
                    └─────────────────────┬┴──────────────────────┐
                                          │
                                   ┌──────┴──────┐
                                   │             │
                                   │  chart.py   │
                                   │             │
                                   └──────┬──────┘
                                          │
                    ┌───────────────────────────────────────┐
                    │                     │                 │
            ┌───────┴───────┐    ┌───────┴───────┐ ┌───────┴───────┐
            │               │    │               │ │               │
            │chart_utils.py │    │chart_base.py  │ │chart_issues.py│
            │               │    │               │ │               │
            └───────────────┘    └───────────────┘ └───────────────┘
                                                    │
                                          ┌─────────┴─────────┐
                                          │                   │
                                          │chart_contributors.py│
                                          │                   │
                                          └───────────────────┘
```

## Component Details

### GitHub API Architecture

The system now supports both REST and GraphQL APIs with a compatibility layer to maintain backward compatibility:

#### GitHub API Entry Point (github_api.py)
- Acts as the main entry point for all GitHub API interactions
- Imports from the compatibility layer to maintain backward compatibility
- Provides the same interface as the original REST API client

#### Compatibility Layer (github_api_compat.py)
- Implements the same interface as the original REST API client
- Delegates to the appropriate API implementation (REST or GraphQL)
- Ensures backward compatibility with existing code

#### REST API Client (github_api_rest.py)
- The original REST API client (renamed from github_api.py)
- Handles authentication and request headers for REST API
- Implements automatic pagination for all REST API endpoints
- Manages rate limiting with exponential backoff retry logic
- Normalizes response data into consistent formats
- Integrates with the caching system for all requests
- Provides high-level methods for fetching issues, PRs, and user data

#### GraphQL API Client (github_graphql_api.py)
- Manages all communication with GitHub's GraphQL API
- Handles authentication and request headers for GraphQL API
- Implements cursor-based pagination for GraphQL queries
- Supports special feature flags like issue types
- Provides a centralized interface for all GraphQL operations
- Integrates with the caching system for all requests

#### GraphQL Utility Functions (github_graphql_utils.py)
- Provides utility functions for GraphQL operations
- Handles data extraction from nested GraphQL responses
- Maps GraphQL types to REST API equivalents
- Implements helper functions for common operations

#### GraphQL Specialized Modules
- **github_graphql_issues.py**: Handles issue-related GraphQL queries
- **github_graphql_pulls.py**: Manages pull request-related GraphQL queries
- **github_graphql_contributors.py**: Handles contributor-related GraphQL queries
- **github_graphql_item_details.py**: Provides shared functionality for fetching detailed information about issues and PRs

### Caching System (github_cache.py)

The caching system provides efficient data storage and retrieval:
- Creates unique cache keys based on endpoint and parameters
- Stores responses as JSON files with metadata
- Tracks cache staleness and validity
- Handles cache invalidation and updates
- Supports different operating modes (normal, no-cache, cache-only)
- Maintains metadata about rate limits and request timestamps

### Issue Analysis (issue_stats.py)

Processes and analyzes repository issue data:
- Converts raw API data into time series format
- Tracks issue states (open/closed) over time
- Processes label information for categorization
- Calculates daily and cumulative statistics
- Handles date range filtering while maintaining data accuracy
- Feeds processed data to visualization system

### Contributor Analysis (external_contributors.py)

Analyzes contribution patterns from internal, external, and unknown contributors:
- Classifies contributors based on organization membership and explicit lists
- Identifies "unknown" contributors when both internal and external lists are provided
- Tracks PR creation and closure over time by contributor type
- Aggregates contributions by time period and contributor type
- Maintains contributor statistics and history
- Processes PR state changes for timeline analysis
- Supports visualization of internal vs. external vs. unknown contribution patterns
- Handles contributor classification with precedence rules

### Visualization Engine

The visualization system is modularized into several components:

#### chart.py
- Acts as a thin wrapper around specialized chart modules
- Re-exports all chart functions to maintain backward compatibility
- Provides a unified interface for all visualization needs

#### chart_utils.py
- Contains constants and utility functions
- Manages output directory creation
- Handles chart saving and file management
- Provides date range calculation utilities

#### chart_base.py
- Implements common chart setup and configuration
- Provides base chart styling and formatting
- Handles dual-axis chart creation
- Contains shared data processing functions

#### chart_issues.py
- Specializes in issue-related visualizations
- Implements issue trend charts
- Creates label-based issue analysis charts
- Provides issue type trend visualization
- Implements helper functions for counting issues by type
- Handles issue-specific data processing
- Supports conditional chart generation based on data availability

#### chart_contributors.py
- Focuses on contributor-related visualizations
- Creates contributor trend charts
- Implements open PR timeline visualizations
- Processes contributor-specific data

## Data Flow

### Issue Analysis Pipeline

1. Data Collection:
   - API client fetches issues with full details
   - GraphQL API includes issue type information when available
   - Special GraphQL feature flag is used to access issue types
   - Response data is cached for future use
   - Issue data is normalized into consistent format

2. Processing:
   - Raw data is converted to time series format
   - Issue states are tracked over time
   - Labels are processed for categorization
   - Issue types are extracted and processed
   - Statistics are calculated for each time period

3. Visualization:
   - Data is filtered to requested date range
   - Standard issue trend charts are generated
   - Label-based issue charts are created
   - Issue type charts are conditionally generated when type data is available
   - Charts are formatted with consistent styling
   - Output files are created in specified directory

### Contributor Analysis Pipeline

1. Initial Setup:
   - Fetch and cache organization member lists
   - Classify contributors based on the following precedence rules:
     - Explicit external contributor list (highest priority)
     - Explicit internal contributor list
     - Organization membership
     - If both internal and external lists are provided, contributors not in either list are classified as "unknown"
     - Otherwise, default to external
   - Initialize tracking structures by contributor type (internal, external, unknown)

2. Data Processing:
   - Process PR data for each contributor
   - Track PR states over time by contributor type
   - Aggregate contributions by time period and contributor type
   - Calculate contributor statistics

3. Output Generation:
   - Generate contributor trend visualizations with optional filtering
   - Create PR timeline charts with contributor type differentiation
   - Output contributor statistics with type information
   - Filter output based on show flags

## Component Interaction

- The API client provides data to both analysis modules
- The cache system intercepts all API requests
- Analysis modules process raw data into time series
- The chart system receives processed data from analysis modules
- All components share consistent date handling

## Extension Points

The system can be extended in several ways:

### New Analysis Types
- Create new analysis modules
- Use existing API client and cache
- Follow established data processing patterns
- Add corresponding visualization support

### Additional Data Sources
- Extend API client for new endpoints
- Implement appropriate caching
- Add new data processing pipelines
- Create visualization support

### Enhanced Visualization
- Add new chart types to the appropriate specialized module
- Create new chart modules for entirely new visualization categories
- Extend chart_base.py for new shared chart functionality
- Update chart.py to re-export any new functions
- Maintain consistent styling across all chart modules
- Support standard date filtering in all visualizations
- Follow existing output patterns for consistency

## Best Practices

When modifying or extending the system:

1. Data Handling:
   - Use the API client for all GitHub interactions
   - Leverage the caching system appropriately
   - Maintain consistent data formats

2. Analysis:
   - Process data into time series where appropriate
   - Support date range filtering
   - Maintain data accuracy across date ranges

3. Visualization:
   - Place new chart functions in the appropriate specialized module
   - Leverage common functionality from chart_base.py and chart_utils.py
   - Follow established chart formatting and styling conventions
   - Support standard date range parameters in all chart functions
   - Maintain consistent output handling across all chart types
   - Update chart.py to re-export any new functions for backward compatibility
