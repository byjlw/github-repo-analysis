"""
Utility functions for the GitHub GraphQL API.
"""

from typing import Dict, List, Any, Optional

def map_timeline_type_to_event(typename: str) -> str:
    """Map GraphQL timeline item type to REST API event type.
    
    Args:
        typename: GraphQL typename (e.g., 'ClosedEvent')
        
    Returns:
        REST API event type (e.g., 'closed')
    """
    mapping = {
        'ClosedEvent': 'closed',
        'ReopenedEvent': 'reopened',
        'LabeledEvent': 'labeled',
        'UnlabeledEvent': 'unlabeled',
        'AssignedEvent': 'assigned',
        'UnassignedEvent': 'unassigned',
        'MergedEvent': 'merged',
        'ReferencedEvent': 'referenced',
        'CrossReferencedEvent': 'cross-referenced',
        'MilestonedEvent': 'milestoned',
        'DemilestonedEvent': 'demilestoned',
        'RenamedTitleEvent': 'renamed',
        'LockedEvent': 'locked',
        'UnlockedEvent': 'unlocked',
        'MarkedAsDuplicateEvent': 'marked_as_duplicate',
        'UnmarkedAsDuplicateEvent': 'unmarked_as_duplicate',
        'PinnedEvent': 'pinned',
        'UnpinnedEvent': 'unpinned',
        'TransferredEvent': 'transferred',
        'ConvertedToDiscussionEvent': 'converted_to_discussion'
    }
    return mapping.get(typename, typename.lower().replace('event', ''))

def extract_data_from_path(data: Dict[str, Any], path: List[str]) -> Optional[Dict[str, Any]]:
    """Extract data from a nested dictionary using a path.
    
    Args:
        data: Dictionary to extract data from
        path: List of keys to navigate the dictionary
        
    Returns:
        Extracted data or None if path is invalid
    """
    current = data
    for key in path:
        if not current or key not in current:
            return None
        current = current[key]
    return current
