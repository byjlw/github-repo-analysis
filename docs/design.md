# Design Documentation

This document explains how the github-repo-analysis system works internally and how its components interact.

## System Architecture

The system is built around a central GitHub API client with specialized analysis modules that process and visualize specific aspects of repository data:

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
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
            ┌───────┴───────┐      ┌───────┴───────┐      ┌───────┴───────┐
            │               │      │               │      │               │
            │ issue_stats.py│      │github_cache.py│      │external_contributors.py│
            │               │      │               │      │               │
            └───────┬───────┘      └───────────────┘      └───────┬───────┘
                    │                                             │
                    └──────────────────────┬──────────────────────┘
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

### GitHub API Client (github_api.py)

The API client manages all communication with GitHub's REST API:
- Handles authentication and request headers
- Implements automatic pagination for all API endpoints
- Manages rate limiting with exponential backoff retry logic
- Normalizes response data into consistent formats
- Integrates with the caching system for all requests
- Provides high-level methods for fetching issues, PRs, and user data

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
- Handles issue-specific data processing

#### chart_contributors.py
- Focuses on contributor-related visualizations
- Creates contributor trend charts
- Implements open PR timeline visualizations
- Processes contributor-specific data

## Data Flow

### Issue Analysis Pipeline

1. Data Collection:
   - API client fetches issues with full details
   - Response data is cached for future use
   - Issue data is normalized into consistent format

2. Processing:
   - Raw data is converted to time series format
   - Issue states are tracked over time
   - Labels are processed for categorization
   - Statistics are calculated for each time period

3. Visualization:
   - Data is filtered to requested date range
   - Charts are generated with standard formatting
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
