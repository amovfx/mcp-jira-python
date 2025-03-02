import unittest
import os
import base64
import json
import time
from jira import JIRA

class TestJiraApiIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure environment variables are set
        required_vars = ["JIRA_HOST", "JIRA_EMAIL", "JIRA_API_TOKEN"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Initialize JIRA client
        cls.jira = JIRA(
            server=f"https://{os.getenv('JIRA_HOST')}",
            basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
        )
        
        cls.project_key = "TEST"
        cls.test_user_email = os.getenv("JIRA_EMAIL")

    def setUp(self):
        """Create a test issue for each test method"""
        self.test_issue = None
        self.test_issue_key = None

    def tearDown(self):
        """Clean up test issue after each test method"""
        if self.test_issue_key:
            try:
                issue = self.jira.issue(self.test_issue_key)
                issue.delete()
                print(f"Deleted test issue: {self.test_issue_key}")
            except Exception as e:
                print(f"Failed to delete test issue {self.test_issue_key}: {str(e)}")

    def test_0_create_jira_issue(self):
        """Test creating a new Jira issue"""
        issue_dict = {
            'project': {'key': self.project_key},
            'summary': 'Test Issue Created via API',
            'description': 'This is a test issue created by the create_jira_issue endpoint',
            'issuetype': {'name': 'Task'},
            'priority': {'name': 'Medium'},
            'assignee': {'emailAddress': self.test_user_email}
        }
        
        new_issue = self.jira.create_issue(fields=issue_dict)
        self.test_issue_key = new_issue.key
        
        # Verify issue was created with correct fields
        created_issue = self.jira.issue(self.test_issue_key)
        self.assertEqual(created_issue.fields.summary, 'Test Issue Created via API')
        self.assertEqual(created_issue.fields.description, 'This is a test issue created by the create_jira_issue endpoint')
        self.assertEqual(created_issue.fields.issuetype.name, 'Task')
        self.assertEqual(created_issue.fields.priority.name, 'Medium')
        # Check assignee only if it exists
        if hasattr(created_issue.fields.assignee, 'emailAddress'):
            self.assertEqual(created_issue.fields.assignee.emailAddress, self.test_user_email)
        print(f"Successfully created new issue: {self.test_issue_key}")

    def test_1_add_comment(self):
        """Test adding a comment to an issue"""
        # Create test issue first
        issue_dict = {
            'project': {'key': self.project_key},
            'summary': 'Test Issue for Integration Tests',
            'description': 'This is a test issue created by integration tests',
            'issuetype': {'name': 'Task'}
        }
        self.test_issue = self.jira.create_issue(fields=issue_dict)
        self.test_issue_key = self.test_issue.key

        comment_text = "Test comment from integration tests"
        comment = self.jira.add_comment(self.test_issue_key, comment_text)
        
        # Verify comment was added
        issue = self.jira.issue(self.test_issue_key)
        self.assertIn(comment_text, [c.body for c in issue.fields.comment.comments])
        print(f"Successfully added comment to {self.test_issue_key}")

    def test_2_add_comment_with_attachment(self):
        """Test adding a comment with an attachment"""
        # Create test issue first
        issue_dict = {
            'project': {'key': self.project_key},
            'summary': 'Test Issue for Integration Tests',
            'description': 'This is a test issue created by integration tests',
            'issuetype': {'name': 'Task'}
        }
        self.test_issue = self.jira.create_issue(fields=issue_dict)
        self.test_issue_key = self.test_issue.key

        comment_text = "Test comment with attachment"
        
        # Create a test file
        test_content = "This is a test file content"
        test_content_b64 = base64.b64encode(test_content.encode()).decode()
        
        # Add comment with attachment
        comment = self.jira.add_comment(self.test_issue_key, comment_text)
        
        # Add attachment
        with open('test_attachment.txt', 'w') as f:
            f.write(test_content)
        
        with open('test_attachment.txt', 'rb') as f:
            attachment = self.jira.add_attachment(
                issue=self.test_issue_key,
                attachment=f
            )
        
        # Verify attachment was added
        issue = self.jira.issue(self.test_issue_key)
        self.assertTrue(any(a.filename == 'test_attachment.txt' for a in issue.fields.attachment))
        print(f"Successfully added comment with attachment to {self.test_issue_key}")
        
        # Clean up
        os.remove('test_attachment.txt')

    def test_3_search_issues(self):
        """Test searching for issues"""
        # Create test issue first
        issue_dict = {
            'project': {'key': self.project_key},
            'summary': 'Test Issue for Integration Tests',
            'description': 'This is a test issue created by integration tests',
            'issuetype': {'name': 'Task'}
        }
        self.test_issue = self.jira.create_issue(fields=issue_dict)
        self.test_issue_key = self.test_issue.key

        # Search for our test issue
        jql = f"project = {self.project_key} AND summary ~ 'Test Issue for Integration Tests'"
        issues = self.jira.search_issues(jql)
        
        # Verify our test issue is found
        self.assertTrue(any(i.key == self.test_issue_key for i in issues))
        print(f"Successfully searched for issues in project {self.project_key}")

    def test_4_get_issue(self):
        """Test getting issue details"""
        # Create test issue first
        issue_dict = {
            'project': {'key': self.project_key},
            'summary': 'Test Issue for Integration Tests',
            'description': 'This is a test issue created by integration tests',
            'issuetype': {'name': 'Task'}
        }
        self.test_issue = self.jira.create_issue(fields=issue_dict)
        self.test_issue_key = self.test_issue.key

        issue = self.jira.issue(self.test_issue_key)
        
        # Verify issue details
        self.assertEqual(issue.fields.summary, 'Test Issue for Integration Tests')
        self.assertEqual(issue.fields.description, 'This is a test issue created by integration tests')
        print(f"Successfully retrieved issue details for {self.test_issue_key}")

    def test_5_create_issue_link(self):
        """Test creating issue links"""
        # Create first test issue
        issue_dict = {
            'project': {'key': self.project_key},
            'summary': 'Test Issue for Integration Tests',
            'description': 'This is a test issue created by integration tests',
            'issuetype': {'name': 'Task'}
        }
        self.test_issue = self.jira.create_issue(fields=issue_dict)
        self.test_issue_key = self.test_issue.key

        # Create another issue to link to
        second_issue = self.jira.create_issue(fields=issue_dict)
        
        try:
            # Create link
            self.jira.create_issue_link(
                type="Relates",
                inwardIssue=self.test_issue_key,
                outwardIssue=second_issue.key
            )
            
            # Verify link was created
            links = self.jira.issue(self.test_issue_key).fields.issuelinks
            self.assertTrue(any(l.outwardIssue.key == second_issue.key for l in links))
            print(f"Successfully created issue link between {self.test_issue_key} and {second_issue.key}")
        
        finally:
            # Clean up second issue
            try:
                issue = self.jira.issue(second_issue.key)
                issue.delete()
            except Exception as e:
                print(f"Failed to delete second issue: {str(e)}")

    def test_6_update_issue(self):
        """Test updating an issue"""
        # Create test issue first
        issue_dict = {
            'project': {'key': self.project_key},
            'summary': 'Test Issue for Integration Tests',
            'description': 'This is a test issue created by integration tests',
            'issuetype': {'name': 'Task'}
        }
        self.test_issue = self.jira.create_issue(fields=issue_dict)
        self.test_issue_key = self.test_issue.key

        update_fields = {
            "summary": "Updated Test Issue",
            "description": "Updated test description"
        }
        
        self.jira.issue(self.test_issue_key).update(fields=update_fields)
        
        # Verify updates
        updated_issue = self.jira.issue(self.test_issue_key)
        self.assertEqual(updated_issue.fields.summary, "Updated Test Issue")
        self.assertEqual(updated_issue.fields.description, "Updated test description")
        print(f"Successfully updated issue {self.test_issue_key}")

    def test_7_get_user(self):
        """Test getting user details"""
        users = self.jira.search_users(query=self.test_user_email)
        
        # Verify user is found
        self.assertTrue(len(users) > 0)
        self.assertEqual(users[0].emailAddress, self.test_user_email)
        print(f"Successfully retrieved user details for {self.test_user_email}")

    def test_8_list_fields(self):
        """Test listing available fields"""
        fields = self.jira.fields()
        
        # Verify common fields exist
        field_names = [f['name'] for f in fields]
        required_fields = ['Summary', 'Description', 'Issue Type']
        for field in required_fields:
            self.assertTrue(any(field.lower() in f.lower() for f in field_names))
        print("Successfully retrieved field list")

    def test_9_list_issue_types(self):
        """Test listing issue types"""
        issue_types = self.jira.issue_types()
        
        # Verify common issue types exist
        type_names = [it.name for it in issue_types]
        self.assertTrue(any('Task' in t for t in type_names))
        print("Successfully retrieved issue types")

    def test_a_list_link_types(self):
        """Test listing link types"""
        link_types = self.jira.issue_link_types()
        
        # Verify common link types exist
        self.assertTrue(len(link_types) > 0)
        print("Successfully retrieved link types")

    def test_b_delete_issue(self):
        """Test deleting an issue"""
        # Create test issue first
        issue_dict = {
            'project': {'key': self.project_key},
            'summary': 'Test Issue to be Deleted',
            'description': 'This is a test issue that will be deleted',
            'issuetype': {'name': 'Task'}
        }
        new_issue = self.jira.create_issue(fields=issue_dict)
        
        # Store the key for verification
        issue_key = new_issue.key
        print(f"Created issue {issue_key} for deletion test")
        
        # Delete the issue
        new_issue.delete()
        
        # Verify the issue is deleted
        try:
            self.jira.issue(issue_key)
            self.fail("Issue still exists after deletion")
        except Exception as e:
            self.assertTrue("Issue Does Not Exist" in str(e) or "404" in str(e))
            print(f"Successfully verified deletion of issue {issue_key}")
if __name__ == '__main__':
    unittest.main(verbosity=2)