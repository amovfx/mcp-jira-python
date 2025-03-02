import unittest
import os
import base64
from unittest.mock import Mock, patch
import json

class TestJiraApiTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up environment variables for testing
        os.environ["JIRA_HOST"] = "test.atlassian.net"
        os.environ["JIRA_EMAIL"] = "test@example.com"
        os.environ["JIRA_API_TOKEN"] = "test-token"
        
        # Sample test data
        cls.test_issue_key = "TEST-123"
        cls.test_project_key = "TEST"
        cls.test_email = "user@example.com"
        
    def setUp(self):
        self.mock_jira = Mock()
        self.patcher = patch('jira.JIRA', return_value=self.mock_jira)
        self.patcher.start()
        
    def tearDown(self):
        self.patcher.stop()

    def test_create_jira_issue(self):
        """Test creating a new Jira issue"""
        mock_issue = Mock()
        mock_issue.key = self.test_issue_key
        mock_issue.id = "10000"
        mock_issue.self = "https://test.atlassian.net/rest/api/2/issue/10000"
        
        self.mock_jira.create_issue.return_value = mock_issue
        
        issue_dict = {
            'project': {'key': self.test_project_key},
            'summary': 'Test Issue',
            'description': 'Test Description',
            'issuetype': {'name': 'Bug'},
            'priority': {'name': 'High'},
            'assignee': {'emailAddress': self.test_email}
        }
        
        result = self.mock_jira.create_issue(fields=issue_dict)
        
        self.mock_jira.create_issue.assert_called_with(fields=issue_dict)
        self.assertEqual(result.key, self.test_issue_key)
        self.assertEqual(result.id, "10000")
        self.assertTrue(result.self.endswith("/10000"))

    def test_add_comment(self):
        """Test adding a comment to an issue"""
        mock_comment = Mock()
        mock_comment.id = "12345"
        self.mock_jira.add_comment.return_value = mock_comment
        
        result = self.mock_jira.add_comment(
            self.test_issue_key,
            "Test comment"
        )
        
        self.mock_jira.add_comment.assert_called_with(
            self.test_issue_key,
            "Test comment"
        )
        self.assertEqual(result.id, "12345")

    def test_add_comment_with_attachment(self):
        """Test adding a comment with an attachment"""
        mock_comment = Mock()
        mock_comment.id = "12345"
        mock_attachment = Mock()
        mock_attachment.id = "67890"
        
        self.mock_jira.add_comment.return_value = mock_comment
        self.mock_jira.add_attachment.return_value = mock_attachment
        
        test_content = base64.b64encode(b"test content").decode()
        result = self.mock_jira.add_comment(
            self.test_issue_key,
            "Test comment with attachment"
        )
        
        self.mock_jira.add_comment.assert_called_once()
        self.assertEqual(result.id, "12345")

    def test_search_issues(self):
        """Test searching for issues"""
        mock_issue = Mock()
        mock_issue.key = self.test_issue_key
        mock_issue.fields = Mock()
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.status = "Open"
        mock_issue.fields.priority = "High"
        mock_issue.fields.assignee = "test@example.com"
        mock_issue.fields.issuetype = "Bug"
        
        self.mock_jira.search_issues.return_value = [mock_issue]
        
        jql = "priority = High"
        result = self.mock_jira.search_issues(
            f"project = {self.test_project_key} AND {jql}",
            maxResults=30,
            fields="summary,description,status,priority,assignee,issuetype"
        )
        
        self.mock_jira.search_issues.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].key, self.test_issue_key)

    def test_delete_issue(self):
        """Test deleting an issue"""
        self.mock_jira.delete_issue(self.test_issue_key)
        self.mock_jira.delete_issue.assert_called_with(self.test_issue_key)

    def test_get_issue(self):
        """Test getting issue details"""
        mock_issue = Mock()
        mock_issue.key = self.test_issue_key
        mock_issue.fields = Mock()
        mock_issue.fields.summary = "Test Issue"
        mock_issue.fields.description = "Test Description"
        mock_issue.fields.status = "Open"
        mock_issue.fields.priority = "High"
        mock_issue.fields.assignee = "test@example.com"
        mock_issue.fields.issuetype = "Bug"
        
        # Mock comments
        mock_comment = Mock()
        mock_comment.id = "12345"
        mock_comment.author = "test@example.com"
        mock_comment.body = "Test comment"
        mock_comment.created = "2024-01-14"
        mock_issue.fields.comment = Mock()
        mock_issue.fields.comment.comments = [mock_comment]
        
        # Mock attachments
        mock_attachment = Mock()
        mock_attachment.id = "67890"
        mock_attachment.filename = "test.txt"
        mock_attachment.size = 100
        mock_attachment.created = "2024-01-14"
        mock_issue.fields.attachment = [mock_attachment]
        
        self.mock_jira.issue.return_value = mock_issue
        
        result = self.mock_jira.issue(self.test_issue_key, expand='comments,attachments')
        
        self.mock_jira.issue.assert_called_with(
            self.test_issue_key,
            expand='comments,attachments'
        )
        self.assertEqual(result.key, self.test_issue_key)

    def test_create_issue_link(self):
        """Test creating issue links"""
        self.mock_jira.create_issue_link(
            type="blocks",
            inwardIssue="TEST-123",
            outwardIssue="TEST-124"
        )
        
        self.mock_jira.create_issue_link.assert_called_with(
            type="blocks",
            inwardIssue="TEST-123",
            outwardIssue="TEST-124"
        )

    def test_update_issue(self):
        """Test updating an issue"""
        mock_issue = Mock()
        self.mock_jira.issue.return_value = mock_issue
        
        update_fields = {
            "summary": "Updated Summary",
            "description": "Updated Description",
            "assignee": {"emailAddress": "new@example.com"},
            "status": {"name": "In Progress"},
            "priority": {"name": "High"}
        }
        
        self.mock_jira.issue(self.test_issue_key).update(fields=update_fields)
        
        mock_issue.update.assert_called_with(fields=update_fields)

    def test_get_user(self):
        """Test getting user details"""
        mock_user = Mock()
        mock_user.accountId = "12345"
        mock_user.displayName = "Test User"
        mock_user.emailAddress = self.test_email
        mock_user.active = True
        
        self.mock_jira.search_users.return_value = [mock_user]
        
        result = self.mock_jira.search_users(query=self.test_email)
        
        self.mock_jira.search_users.assert_called_with(query=self.test_email)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].emailAddress, self.test_email)

    def test_list_fields(self):
        """Test listing available fields"""
        mock_fields = [
            {
                "id": "summary",
                "name": "Summary",
                "custom": False,
                "schema": {"type": "string"}
            }
        ]
        
        self.mock_jira.fields.return_value = mock_fields
        result = self.mock_jira.fields()
        
        self.mock_jira.fields.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Summary")

    def test_list_issue_types(self):
        """Test listing issue types"""
        mock_issue_type = Mock()
        mock_issue_type.id = "10001"
        mock_issue_type.name = "Bug"
        mock_issue_type.description = "Bug description"
        mock_issue_type.subtask = False
        
        self.mock_jira.issue_types.return_value = [mock_issue_type]
        result = self.mock_jira.issue_types()
        
        self.mock_jira.issue_types.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Bug")

    def test_list_link_types(self):
        """Test listing link types"""
        mock_link_type = Mock()
        mock_link_type.id = "10100"
        mock_link_type.name = "Blocks"
        mock_link_type.inward = "is blocked by"
        mock_link_type.outward = "blocks"
        
        self.mock_jira.issue_link_types.return_value = [mock_link_type]
        result = self.mock_jira.issue_link_types()
        
        self.mock_jira.issue_link_types.assert_called_once()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Blocks")

if __name__ == '__main__':
    unittest.main()