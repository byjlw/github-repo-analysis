import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class GitHubCache:
    """Handles caching of GitHub API responses."""
    
    def __init__(self, cache_dir: str = ".cache"):
        """Initialize the cache handler.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_cache_path(self, endpoint: str, params: Optional[Dict] = None) -> str:
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
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def save(self, path: str, data: Any, metadata: Optional[Dict] = None, repo_stats: Optional[Dict] = None) -> None:
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
    
    def load(self, path: str, use_cache_only: bool = False) -> Optional[Dict]:
        """Load data from cache file if it exists and is not stale.
        
        Args:
            path: Cache file path
            use_cache_only: If True, return cached data regardless of staleness
            
        Returns:
            Cache data if available and not stale (or if use_cache_only is True), None otherwise
        """
        if not os.path.exists(path):
            return None
            
        with open(path, 'r') as f:
            cache = json.load(f)
        
        if not use_cache_only:
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
