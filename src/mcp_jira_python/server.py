import asyncio
import os
import base64
from tempfile import NamedTemporaryFile

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
from jira import JIRA

# Initialize server
server = Server("jira-api")

# Environment variables for Jira authentication
JIRA_HOST = os.getenv("JIRA_HOST")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

if not all([JIRA_HOST, JIRA_EMAIL, JIRA_API_TOKEN]):
    raise ValueError(
        "Missing required environment variables: JIRA_HOST, JIRA_EMAIL, and JIRA_API_TOKEN"
    )

# Initialize Jira client
jira = JIRA(
    server=f"https://{JIRA_HOST}",
    basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for JIRA integration."""
    return [
        types.Tool(
            name="delete_issue",
            description="Delete a Jira issue or subtask",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue to delete"
                    }
                },
                "required": ["issueKey"]
            }
        ),
        types.Tool(
    name="create_jira_issue",
    description="Create a new Jira issue",
    inputSchema={
        "type": "object",
        "properties": {
            "projectKey": {
                "type": "string",
                "description": "Project key where the issue will be created (e.g., 'MRR')"
            },
            "summary": {
                "type": "string",
                "description": "Issue summary/title"
            },
            "description": {
                "type": "string",
                "description": "Issue description"
            },
            "issueType": {
                "type": "string",
                "description": "Type of issue (e.g., 'Bug', 'Task', 'Story')"
            },
            "priority": {
                "type": "string",
                "description": "Issue priority"
            },
            "assignee": {
                "type": "string",
                "description": "Email of the assignee"
            }
        },
        "required": ["projectKey", "summary", "issueType"]
    }
),
        types.Tool(
            name="get_issue",
            description="Get complete issue details including comments and attachments",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Issue key (e.g., MRR-86)"
                    }
                },
                "required": ["issueKey"]
            }
        ),
        types.Tool(
            name="create_issue_link",
            description="Create a link between two issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "inwardIssueKey": {
                        "type": "string",
                        "description": "Key of the inward issue (e.g., blocked issue)"
                    },
                    "outwardIssueKey": {
                        "type": "string",
                        "description": "Key of the outward issue (e.g., blocking issue)"
                    },
                    "linkType": {
                        "type": "string",
                        "description": "Type of link (e.g., 'blocks')"
                    }
                },
                "required": ["inwardIssueKey", "outwardIssueKey", "linkType"]
            }
        ),
        types.Tool(
            name="update_issue",
            description="Update an existing Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue to update"
                    },
                    "summary": {
                        "type": "string",
                        "description": "New summary/title"
                    },
                    "description": {
                        "type": "string",
                        "description": "New description"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Email of new assignee"
                    },
                    "status": {
                        "type": "string",
                        "description": "New status"
                    },
                    "priority": {
                        "type": "string",
                        "description": "New priority"
                    }
                },
                "required": ["issueKey"]
            }
        ),
        types.Tool(
            name="get_user",
            description="Get a user's account ID by email address",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "User's email address"
                    }
                },
                "required": ["email"]
            }
        ),
        types.Tool(
            name="list_fields",
            description="List all available Jira fields",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="list_issue_types",
            description="List all available issue types", 
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="list_link_types",
            description="List all available issue link types",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),        
        types.Tool(
            name="search_issues",
            description="Search for issues in a project using JQL",
            inputSchema={
                "type": "object",
                "properties": {
                    "projectKey": {
                        "type": "string",
                        "description": 'Project key (e.g., "MRR")'
                    },
                    "jql": {
                        "type": "string",
                        "description": "JQL filter statement"
                    }
                },
                "required": ["projectKey", "jql"]
            }
        ),
        types.Tool(
            name="add_comment",
            description="Add a comment to a Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue to comment on"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment text content"
                    }
                },
                "required": ["issueKey", "comment"]
            }
        ),
        types.Tool(
            name="add_comment_with_attachment",
            description="Add a comment with an attachment to a Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issueKey": {
                        "type": "string",
                        "description": "Key of the issue to comment on"
                    },
                    "comment": {
                        "type": "string",
                        "description": "Comment text content"
                    },
                    "attachment": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Name of the attachment file"
                            },
                            "content": {
                                "type": "string",
                                "description": "Base64 encoded file content"
                            },
                            "mimeType": {
                                "type": "string",
                                "description": "MIME type of the attachment"
                            }
                        },
                        "required": ["filename", "content", "mimeType"]
                    }
                },
                "required": ["issueKey", "comment", "attachment"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    """Handle tool execution requests for JIRA operations."""
    try:
        if not arguments:
            raise ValueError("Arguments are required")

        if name == "add_comment":
            issue_key = arguments.get("issueKey")
            comment_text = arguments.get("comment")
            
            if not issue_key or not comment_text:
                raise ValueError("issueKey and comment are required")
                
            comment = jira.add_comment(issue_key, comment_text)
            
            return [types.TextContent(
                type="text",
                text=f'{{"message": "Comment added successfully", "id": "{comment.id}"}}'
            )]

        elif name == "add_comment_with_attachment":
            issue_key = arguments.get("issueKey")
            comment_text = arguments.get("comment")
            attachment = arguments.get("attachment")
            
            if not all([issue_key, comment_text, attachment]):
                raise ValueError("issueKey, comment, and attachment are required")
                
            # First add the comment
            comment = jira.add_comment(issue_key, comment_text)
            
            # Then handle the attachment
            with NamedTemporaryFile(delete=False) as temp_file:
                content = base64.b64decode(attachment["content"])
                temp_file.write(content)
                temp_file.flush()
                
                # Add attachment to the issue
                with open(temp_file.name, 'rb') as f:
                    attachment = jira.add_attachment(
                        issue=issue_key,
                        attachment=f,
                        filename=attachment["filename"]
                    )
            
            return [types.TextContent(
                type="text",
                text=f'{{"message": "Comment and attachment added successfully", "comment_id": "{comment.id}", "attachment_id": "{attachment.id}"}}'
            )]

        elif name == "search_issues":
            project_key = arguments.get("projectKey")
            jql = arguments.get("jql")
            
            if not project_key or not jql:
                raise ValueError("projectKey and jql are required")
                
            full_jql = f"project = {project_key} AND {jql}"
            issues = jira.search_issues(
                full_jql,
                maxResults=30,
                fields="summary,description,status,priority,assignee,issuetype"
            )
            
            return [types.TextContent(
                type="text",
                text=str([{
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": str(issue.fields.status),
                    "priority": str(issue.fields.priority) if hasattr(issue.fields, 'priority') else None,
                    "assignee": str(issue.fields.assignee) if hasattr(issue.fields, 'assignee') else None,
                    "type": str(issue.fields.issuetype)
                } for issue in issues])
            )]

        elif name == "delete_issue":
            issue_key = arguments.get("issueKey")
            
            if not issue_key:
                raise ValueError("issueKey is required")
                
            jira.delete_issue(issue_key)
            
            return [types.TextContent(
                type="text",
                text=f'{{"message": "Issue {issue_key} deleted successfully"}}'
            )]

        elif name == "get_issue":
            issue_key = arguments.get("issueKey")
            
            if not issue_key:
                raise ValueError("issueKey is required")
                
            issue = jira.issue(issue_key, expand='comments,attachments')
            
            comments = [{
                "id": comment.id,
                "author": str(comment.author),
                "body": comment.body,
                "created": str(comment.created)
            } for comment in issue.fields.comment.comments]
            
            attachments = [{
                "id": attachment.id,
                "filename": attachment.filename,
                "size": attachment.size,
                "created": str(attachment.created)
            } for attachment in issue.fields.attachment]
            
            return [types.TextContent(
                type="text",
                text=str({
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "description": issue.fields.description,
                    "status": str(issue.fields.status),
                    "priority": str(issue.fields.priority) if hasattr(issue.fields, 'priority') else None,
                    "assignee": str(issue.fields.assignee) if hasattr(issue.fields, 'assignee') else None,
                    "type": str(issue.fields.issuetype),
                    "comments": comments,
                    "attachments": attachments
                })
            )]

        elif name == "create_issue_link":
            inward_issue = arguments.get("inwardIssueKey")
            outward_issue = arguments.get("outwardIssueKey")
            link_type = arguments.get("linkType")
            
            if not all([inward_issue, outward_issue, link_type]):
                raise ValueError("inwardIssueKey, outwardIssueKey, and linkType are required")
                
            jira.create_issue_link(
                type=link_type,
                inwardIssue=inward_issue,
                outwardIssue=outward_issue
            )
            
            return [types.TextContent(
                type="text",
                text='{"message": "Issue link created successfully"}'
            )]

        elif name == "update_issue":
            issue_key = arguments.get("issueKey")
            
            if not issue_key:
                raise ValueError("issueKey is required")
                
            update_fields = {}
            if "summary" in arguments:
                update_fields["summary"] = arguments["summary"]
            if "description" in arguments:
                update_fields["description"] = arguments["description"]
            if "assignee" in arguments:
                update_fields["assignee"] = {"emailAddress": arguments["assignee"]}
            if "status" in arguments:
                update_fields["status"] = {"name": arguments["status"]}
            if "priority" in arguments:
                update_fields["priority"] = {"name": arguments["priority"]}

            issue = jira.issue(issue_key)
            issue.update(fields=update_fields)
            
            return [types.TextContent(
                type="text",
                text=f'{{"message": "Issue {issue_key} updated successfully"}}'
            )]

        elif name == "get_user":
            email = arguments.get("email")
            
            if not email:
                raise ValueError("email is required")
                
            users = jira.search_users(query=email)
            if not users:
                raise ValueError(f"No user found with email: {email}")
                
            user = users[0]
            return [types.TextContent(
                type="text",
                text=str({
                    "accountId": user.accountId,
                    "displayName": user.displayName,
                    "emailAddress": user.emailAddress,
                    "active": user.active
                })
            )]

        elif name == "list_fields":
            fields = jira.fields()
            return [types.TextContent(
                type="text",
                text=str([{
                    "id": field["id"],
                    "name": field["name"],
                    "custom": field["custom"],
                    "type": field["schema"]["type"] if "schema" in field else None
                } for field in fields])
            )]

        elif name == "list_issue_types":
            issue_types = jira.issue_types()
            return [types.TextContent(
                type="text",
                text=str([{
                    "id": it.id,
                    "name": it.name,
                    "description": it.description,
                    "subtask": it.subtask
                } for it in issue_types])
            )]

        elif name == "list_link_types":
            link_types = jira.issue_link_types()
            return [types.TextContent(
                type="text",
                text=str([{
                    "id": lt.id,
                    "name": lt.name,
                    "inward": lt.inward,
                    "outward": lt.outward
                } for lt in link_types])
            )]

        elif name == "create_jira_issue":
            project_key = arguments.get("projectKey")
            summary = arguments.get("summary")
            issue_type = arguments.get("issueType")
            
            if not all([project_key, summary, issue_type]):
                raise ValueError("projectKey, summary, and issueType are required")
            
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'issuetype': {'name': issue_type}
            }
            
            # Add optional fields if provided
            if "description" in arguments:
                issue_dict['description'] = arguments["description"]
            if "priority" in arguments:
                issue_dict['priority'] = {'name': arguments["priority"]}
            if "assignee" in arguments:
                issue_dict['assignee'] = {'emailAddress': arguments["assignee"]}
            
            issue = jira.create_issue(fields=issue_dict)
            
            return [types.TextContent(
                type="text",
                text=str({
                    "key": issue.key,
                    "id": issue.id,
                    "self": issue.self
                })
            )]

        raise ValueError(f"Unknown tool: {name}")
        
    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Operation failed: {str(e)}",
            isError=True
        )]

async def main():
    """Run the JIRA MCP server using stdin/stdout streams."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jira-api",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
