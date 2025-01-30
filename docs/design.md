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
                                   └─────────────┘
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

### External Contributor Analysis (external_contributors.py)

Analyzes contribution patterns from external contributors:
- Filters contributors based on organization membership
- Tracks PR creation and closure over time
- Aggregates contributions by time period
- Maintains contributor statistics and history
- Processes PR state changes for timeline analysis
- Handles excluded contributor filtering

### Visualization Engine (chart.py)

Generates standardized visualizations of repository metrics:
- Manages consistent chart styling and formatting
- Handles date range calculations from data
- Creates time series visualizations
- Manages multi-axis charts for related metrics
- Handles legend positioning and formatting
- Provides output file management

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
   - Create filtered contributor list
   - Initialize tracking structures

2. Data Processing:
   - Process PR data for each contributor
   - Track PR states over time
   - Aggregate contributions by time period
   - Calculate contributor statistics

3. Output Generation:
   - Generate contributor trend visualizations
   - Create PR timeline charts
   - Output contributor statistics

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
- Add new chart types to chart.py
- Maintain consistent styling
- Support standard date filtering
- Follow existing output patterns

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
   - Follow established chart formatting
   - Support standard date range parameters
   - Maintain consistent output handling
