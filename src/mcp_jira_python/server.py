"""Jira API MCP Service

This module implements a Jira API service using the Python Jira library.
It provides functionality to interact with Jira issues, comments, attachments,
and other Jira resources through a FastMCP interface.

The service exposes multiple tools for Jira operations including:
- Creating, updating, and deleting issues
- Adding comments and attachments
- Searching issues
- Managing issue links
- User operations

Dependencies:
    - jira: For Jira API interactions
    - httpx: For HTTP requests
    - mcp: For FastMCP server implementation

Usage:
    Run this file directly to start the Jira API server:
    ```
    python server.py
    ```
"""

import os
import base64
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from jira import JIRA

# Load environment variables from .env file
load_dotenv()

# Environment variables for Jira authentication
JIRA_HOST = os.getenv("JIRA_HOST")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

if not all([JIRA_HOST, JIRA_EMAIL, JIRA_API_TOKEN]):
    raise ValueError(
        "Missing required environment variables: JIRA_HOST, JIRA_EMAIL, and JIRA_API_TOKEN"
    )

# Initialize FastMCP server
mcp = FastMCP("jira-api")

# Initialize Jira client
jira = JIRA(server=JIRA_HOST, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))


@mcp.tool(
    name="delete_issue",
    description="Delete a Jira issue or subtask",
)
async def delete_issue(issueKey: str) -> str:
    """Delete a Jira issue.

    Args:
        issueKey: Key of the issue to delete
    """
    jira.delete_issue(issueKey)
    return f'{{"message": "Issue {issueKey} deleted successfully"}}'


@mcp.tool(
    name="create_jira_issue",
    description="Create a new Jira issue",
)
async def create_jira_issue(
    projectKey: str,
    summary: str,
    issueType: str,
    description: str = None,
    priority: str = None,
    assignee: str = None,
) -> str:
    """Create a new Jira issue.

    Args:
        projectKey: Project key where the issue will be created
        summary: Issue summary/title
        issueType: Type of issue
        description: Issue description
        priority: Issue priority
        assignee: Email of the assignee
    """
    issue_dict = {
        "project": {"key": projectKey},
        "summary": summary,
        "issuetype": {"name": issueType},
    }

    if description:
        issue_dict["description"] = description
    if priority:
        issue_dict["priority"] = {"name": priority}
    if assignee:
        issue_dict["assignee"] = {"emailAddress": assignee}

    issue = jira.create_issue(fields=issue_dict)
    return str({"key": issue.key, "id": issue.id, "self": issue.self})


@mcp.tool(
    name="get_issue",
    description="Get complete issue details including comments and attachments",
)
async def get_issue(issueKey: str) -> str:
    """Get issue details.

    Args:
        issueKey: Issue key to retrieve
    """
    issue = jira.issue(issueKey, expand="comments,attachments")

    comments = [
        {
            "id": comment.id,
            "author": str(comment.author),
            "body": comment.body,
            "created": str(comment.created),
        }
        for comment in issue.fields.comment.comments
    ]

    attachments = [
        {
            "id": attachment.id,
            "filename": attachment.filename,
            "size": attachment.size,
            "created": str(attachment.created),
        }
        for attachment in issue.fields.attachment
    ]

    return str(
        {
            "key": issue.key,
            "summary": issue.fields.summary,
            "description": issue.fields.description,
            "status": str(issue.fields.status),
            "priority": (
                str(issue.fields.priority)
                if hasattr(issue.fields, "priority")
                else None
            ),
            "assignee": (
                str(issue.fields.assignee)
                if hasattr(issue.fields, "assignee")
                else None
            ),
            "type": str(issue.fields.issuetype),
            "comments": comments,
            "attachments": attachments,
        }
    )


@mcp.tool(
    name="create_issue_link",
    description="Create a link between two issues",
)
async def create_issue_link(
    inwardIssueKey: str, outwardIssueKey: str, linkType: str
) -> str:
    """Create a link between two issues.

    Args:
        inwardIssueKey: Key of the inward issue
        outwardIssueKey: Key of the outward issue
        linkType: Type of link
    """
    jira.create_issue_link(
        type=linkType, inwardIssue=inwardIssueKey, outwardIssue=outwardIssueKey
    )
    return '{"message": "Issue link created successfully"}'


@mcp.tool(
    name="update_issue",
    description="Update an existing Jira issue",
)
async def update_issue(
    issueKey: str,
    summary: str = None,
    description: str = None,
    assignee: str = None,
    status: str = None,
    priority: str = None,
) -> str:
    """Update an existing issue.

    Args:
        issueKey: Key of the issue to update
        summary: New summary
        description: New description
        assignee: New assignee email
        status: New status
        priority: New priority
    """
    update_fields = {}
    if summary:
        update_fields["summary"] = summary
    if description:
        update_fields["description"] = description
    if assignee:
        update_fields["assignee"] = {"emailAddress": assignee}
    if status:
        update_fields["status"] = {"name": status}
    if priority:
        update_fields["priority"] = {"name": priority}

    issue = jira.issue(issueKey)
    issue.update(fields=update_fields)
    return f'{{"message": "Issue {issueKey} updated successfully"}}'


@mcp.tool(
    name="get_user",
    description="Get a user's account ID by email address",
)
async def get_user(email: str) -> str:
    """Get user details by email.

    Args:
        email: User's email address
    """
    users = jira.search_users(query=email)
    if not users:
        raise ValueError(f"No user found with email: {email}")

    user = users[0]
    return str(
        {
            "accountId": user.accountId,
            "displayName": user.displayName,
            "emailAddress": user.emailAddress,
            "active": user.active,
        }
    )


@mcp.tool(
    name="list_fields",
    description="List all available Jira fields",
)
async def list_fields() -> str:
    """List all available Jira fields."""
    fields = jira.fields()
    return str(
        [
            {
                "id": field["id"],
                "name": field["name"],
                "custom": field["custom"],
                "type": field["schema"]["type"] if "schema" in field else None,
            }
            for field in fields
        ]
    )


@mcp.tool(
    name="list_issue_types",
    description="List all available issue types",
)
async def list_issue_types() -> str:
    """List all available issue types."""
    issue_types = jira.issue_types()
    return str(
        [
            {
                "id": it.id,
                "name": it.name,
                "description": it.description,
                "subtask": it.subtask,
            }
            for it in issue_types
        ]
    )


@mcp.tool(
    name="list_link_types",
    description="List all available issue link types",
)
async def list_link_types() -> str:
    """List all available issue link types."""
    link_types = jira.issue_link_types()
    return str(
        [
            {
                "id": lt.id,
                "name": lt.name,
                "inward": lt.inward,
                "outward": lt.outward,
            }
            for lt in link_types
        ]
    )


@mcp.tool(
    name="search_issues",
    description="Search for issues in a project using JQL",
)
async def search_issues(projectKey: str, jql: str) -> str:
    """Search for issues using JQL.

    Args:
        projectKey: Project key to search in
        jql: JQL filter statement
    """
    full_jql = f"project = {projectKey} AND {jql}"
    issues = jira.search_issues(
        full_jql,
        maxResults=30,
        fields="summary,description,status,priority,assignee,issuetype",
    )

    return str(
        [
            {
                "key": issue.key,
                "summary": issue.fields.summary,
                "status": str(issue.fields.status),
                "priority": (
                    str(issue.fields.priority)
                    if hasattr(issue.fields, "priority")
                    else None
                ),
                "assignee": (
                    str(issue.fields.assignee)
                    if hasattr(issue.fields, "assignee")
                    else None
                ),
                "type": str(issue.fields.issuetype),
            }
            for issue in issues
        ]
    )


@mcp.tool(
    name="add_comment",
    description="Add a comment to a Jira issue",
)
async def add_comment(issueKey: str, comment: str) -> str:
    """Add a comment to an issue.

    Args:
        issueKey: Key of the issue to comment on
        comment: Comment text content
    """
    comment_obj = jira.add_comment(issueKey, comment)
    return f'{{"message": "Comment added successfully", "id": "{comment_obj.id}"}}'


@mcp.tool(
    name="add_comment_with_attachment",
    description="Add a comment with an attachment to a Jira issue",
)
async def add_comment_with_attachment(
    issueKey: str,
    comment: str,
    attachment: dict,
) -> str:
    """Add a comment with attachment to an issue.

    Args:
        issueKey: Key of the issue to comment on
        comment: Comment text content
        attachment: Dictionary containing filename, content (base64), and mimeType
    """
    comment_obj = jira.add_comment(issueKey, comment)

    with NamedTemporaryFile(delete=False) as temp_file:
        content = base64.b64decode(attachment["content"])
        temp_file.write(content)
        temp_file.flush()

        with open(temp_file.name, "rb") as f:
            attachment_obj = jira.add_attachment(
                issue=issueKey, attachment=f, filename=attachment["filename"]
            )

    return f'{{"message": "Comment and attachment added successfully", "comment_id": "{comment_obj.id}", "attachment_id": "{attachment_obj.id}"}}'


if __name__ == "__main__":
    mcp.run(transport="stdio")
