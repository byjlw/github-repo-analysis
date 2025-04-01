import logging
from typing import Dict, Optional, Any
from github_graphql_utils import map_timeline_type_to_event

def fetch_issue_details(api, repo_owner: str, repo_name: str, number: int) -> Optional[Dict[str, Any]]:
    """Fetch full details for an issue including comments and events.
    
    Args:
        api: GitHubGraphQLAPI instance
        repo_owner: Repository owner
        repo_name: Repository name
        number: Issue number
        
    Returns:
        Issue details including comments and events, or None if fetch fails
    """
    query = """
    query($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        issue(number: $number) {
          id
          number
          title
          body
          state
          createdAt
          updatedAt
          closedAt
          url
          author {
            login
            url
            avatarUrl
          }
          labels(first: 100) {
            nodes {
              name
              color
              description
            }
          }
          comments(first: 100) {
            nodes {
              id
              author {
                login
              }
              body
              createdAt
              url
            }
          }
          timelineItems(first: 100, itemTypes: [CLOSED_EVENT, REOPENED_EVENT, LABELED_EVENT, UNLABELED_EVENT, ASSIGNED_EVENT, UNASSIGNED_EVENT]) {
            nodes {
              __typename
              ... on ClosedEvent {
                actor {
                  login
                }
                createdAt
              }
              ... on ReopenedEvent {
                actor {
                  login
                }
                createdAt
              }
              ... on LabeledEvent {
                actor {
                  login
                }
                createdAt
                label {
                  name
                }
              }
              ... on UnlabeledEvent {
                actor {
                  login
                }
                createdAt
                label {
                  name
                }
              }
              ... on AssignedEvent {
                actor {
                  login
                }
                createdAt
                assignee {
                  ... on User {
                    login
                  }
                }
              }
              ... on UnassignedEvent {
                actor {
                  login
                }
                createdAt
                assignee {
                  ... on User {
                    login
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    variables = {
        "owner": repo_owner,
        "name": repo_name,
        "number": number
    }
    
    result = api.execute_query(query, variables)
    
    if not result.get("data") or not result.get("data").get("repository") or not result.get("data").get("repository").get("issue"):
        logging.warning(f"Failed to fetch issue {number}")
        return None
        
    issue_data = result["data"]["repository"]["issue"]
    
    # Transform GraphQL response to match REST API format
    issue = {
        "id": issue_data["id"],
        "number": issue_data["number"],
        "title": issue_data["title"],
        "body": issue_data["body"],
        "state": issue_data["state"].lower(),
        "created_at": issue_data["createdAt"],
        "updated_at": issue_data["updatedAt"],
        "closed_at": issue_data["closedAt"],
        "html_url": issue_data["url"],
        "user": {
            "login": issue_data["author"]["login"] if issue_data["author"] else None,
            "html_url": issue_data["author"]["url"] if issue_data["author"] else None,
            "avatar_url": issue_data["author"]["avatarUrl"] if issue_data["author"] else None
        },
        "labels": [
            {
                "name": label["name"],
                "color": label["color"],
                "description": label["description"]
            }
            for label in issue_data["labels"]["nodes"]
        ],
        "comments_data": [
            {
                "id": comment["id"],
                "user": {
                    "login": comment["author"]["login"] if comment["author"] else None
                },
                "body": comment["body"],
                "created_at": comment["createdAt"],
                "html_url": comment["url"]
            }
            for comment in issue_data["comments"]["nodes"]
        ],
        "events_data": [
            {
                "event": map_timeline_type_to_event(item["__typename"]),
                "actor": {
                    "login": item["actor"]["login"] if item["actor"] else None
                },
                "created_at": item["createdAt"],
                "label": {"name": item["label"]["name"]} if "__typename" in item and item["__typename"] in ["LabeledEvent", "UnlabeledEvent"] and "label" in item else None,
                "assignee": {"login": item["assignee"]["login"]} if "__typename" in item and item["__typename"] in ["AssignedEvent", "UnassignedEvent"] and "assignee" in item else None
            }
            for item in issue_data["timelineItems"]["nodes"]
        ]
    }
    
    return issue

def fetch_pull_request_details(api, repo_owner: str, repo_name: str, number: int) -> Optional[Dict[str, Any]]:
    """Fetch full details for a pull request including comments, reviews, and events.
    
    Args:
        api: GitHubGraphQLAPI instance
        repo_owner: Repository owner
        repo_name: Repository name
        number: PR number
        
    Returns:
        Pull request details including comments and events, or None if fetch fails
    """
    query = """
    query($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        pullRequest(number: $number) {
          id
          number
          title
          body
          state
          createdAt
          updatedAt
          closedAt
          mergedAt
          url
          author {
            login
            url
            avatarUrl
          }
          baseRefName
          headRefName
          labels(first: 100) {
            nodes {
              name
              color
              description
            }
          }
          comments(first: 100) {
            nodes {
              id
              author {
                login
              }
              body
              createdAt
              url
            }
          }
          reviews(first: 100) {
            nodes {
              id
              author {
                login
              }
              body
              state
              submittedAt
              url
            }
          }
          timelineItems(first: 100, itemTypes: [CLOSED_EVENT, REOPENED_EVENT, LABELED_EVENT, UNLABELED_EVENT, ASSIGNED_EVENT, UNASSIGNED_EVENT, MERGED_EVENT]) {
            nodes {
              __typename
              ... on ClosedEvent {
                actor {
                  login
                }
                createdAt
              }
              ... on ReopenedEvent {
                actor {
                  login
                }
                createdAt
              }
              ... on LabeledEvent {
                actor {
                  login
                }
                createdAt
                label {
                  name
                }
              }
              ... on UnlabeledEvent {
                actor {
                  login
                }
                createdAt
                label {
                  name
                }
              }
              ... on AssignedEvent {
                actor {
                  login
                }
                createdAt
                assignee {
                  ... on User {
                    login
                  }
                }
              }
              ... on UnassignedEvent {
                actor {
                  login
                }
                createdAt
                assignee {
                  ... on User {
                    login
                  }
                }
              }
              ... on MergedEvent {
                actor {
                  login
                }
                createdAt
                commit {
                  oid
                }
              }
            }
          }
        }
      }
    }
    """
    
    variables = {
        "owner": repo_owner,
        "name": repo_name,
        "number": number
    }
    
    result = api.execute_query(query, variables)
    
    if not result.get("data") or not result.get("data").get("repository") or not result.get("data").get("repository").get("pullRequest"):
        logging.warning(f"Failed to fetch pull request {number}")
        return None
        
    pr_data = result["data"]["repository"]["pullRequest"]
    
    # Transform GraphQL response to match REST API format
    pr = {
        "id": pr_data["id"],
        "number": pr_data["number"],
        "title": pr_data["title"],
        "body": pr_data["body"],
        "state": pr_data["state"].lower(),
        "created_at": pr_data["createdAt"],
        "updated_at": pr_data["updatedAt"],
        "closed_at": pr_data["closedAt"],
        "merged_at": pr_data["mergedAt"],
        "html_url": pr_data["url"],
        "user": {
            "login": pr_data["author"]["login"] if pr_data["author"] else None,
            "html_url": pr_data["author"]["url"] if pr_data["author"] else None,
            "avatar_url": pr_data["author"]["avatarUrl"] if pr_data["author"] else None
        },
        "base": {
            "ref": pr_data["baseRefName"]
        },
        "head": {
            "ref": pr_data["headRefName"]
        },
        "labels": [
            {
                "name": label["name"],
                "color": label["color"],
                "description": label["description"]
            }
            for label in pr_data["labels"]["nodes"]
        ],
        "comments_data": [
            {
                "id": comment["id"],
                "user": {
                    "login": comment["author"]["login"] if comment["author"] else None
                },
                "body": comment["body"],
                "created_at": comment["createdAt"],
                "html_url": comment["url"]
            }
            for comment in pr_data["comments"]["nodes"]
        ],
        "reviews": [
            {
                "id": review["id"],
                "user": {
                    "login": review["author"]["login"] if review["author"] else None
                },
                "body": review["body"],
                "state": review["state"],
                "submitted_at": review["submittedAt"],
                "html_url": review["url"]
            }
            for review in pr_data["reviews"]["nodes"]
        ],
        "events_data": [
            {
                "event": map_timeline_type_to_event(item["__typename"]),
                "actor": {
                    "login": item["actor"]["login"] if item["actor"] else None
                },
                "created_at": item["createdAt"],
                "label": {"name": item["label"]["name"]} if "__typename" in item and item["__typename"] in ["LabeledEvent", "UnlabeledEvent"] and "label" in item else None,
                "assignee": {"login": item["assignee"]["login"]} if "__typename" in item and item["__typename"] in ["AssignedEvent", "UnassignedEvent"] and "assignee" in item else None,
                "commit_id": item["commit"]["oid"] if "__typename" in item and item["__typename"] == "MergedEvent" and "commit" in item else None
            }
            for item in pr_data["timelineItems"]["nodes"]
        ]
    }
    
    return pr

def fetch_item_details(api, repo_owner: str, repo_name: str, item_type: str, number: int) -> Optional[Dict[str, Any]]:
    """Fetch full details for an issue or PR including comments and events.
    
    Args:
        api: GitHubGraphQLAPI instance
        repo_owner: Repository owner
        repo_name: Repository name
        item_type: Type of item ('issues' or 'pulls')
        number: Item number
        
    Returns:
        Item details including comments and events, or None if fetch fails
    """
    if item_type == "issues":
        return fetch_issue_details(api, repo_owner, repo_name, number)
    elif item_type == "pulls":
        return fetch_pull_request_details(api, repo_owner, repo_name, number)
    return None
