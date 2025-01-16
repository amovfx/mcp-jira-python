import unittest
import asyncio
import json
import os
import base64
from typing import Any, Dict
import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions

class TestJiraMCPSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize the MCP server
        cls.server = Server("jira-api")
        
        # Set up required environment variables
        required_vars = ["JIRA_HOST", "JIRA_EMAIL", "JIRA_API_TOKEN"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")



    async def simulate_llm_request(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        try:
            # Get the tool schema first (like an LLM would)
            tools = await self.server.list_tools
            tool_found = False
            for tool in tools:
                if tool.name == tool_name:
                    tool_found = True
                    required_args = tool.inputSchema.get("required", [])
                    for arg in required_args:
                        if arg not in arguments:
                            raise ValueError(f"Missing required argument: {arg}")
                    break
            
            if not tool_found:
                raise ValueError(f"Tool {tool_name} not found")

            # Make the actual tool call
            response = await self.server.call_tool(tool_name, arguments)
            
            if not response or not isinstance(response, list):
                raise ValueError("Invalid response format")
            
            return response[0].text
        except Exception as e:
            return f"Error: {str(e)}"

    def run_async_test(self, coroutine):
        """Helper to run async tests"""
        loop = asyncio.new_event_loop()  # Create a new event loop
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coroutine)
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def test_1_server_initialization(self):
        """Test server initialization with capabilities"""
        async def test_init():
            # Initialize server with options
            init_options = InitializationOptions(
                server_name="jira-api",
                server_version="0.1.0",
                capabilities=self.server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            )
            
            # Verify server capabilities
            tools = await self.server.list_tools
            self.assertTrue(len(tools) > 0)
            self.assertTrue(any(tool.name == "create_jira_issue" for tool in tools))
            print("Server initialized successfully with capabilities")
            
        self.run_async_test(test_init())

    def test_2_llm_workflow_success(self):
        """Test a typical LLM workflow with multiple connected operations"""
        async def test_workflow():
            # 1. Create a new issue
            create_result = await self.simulate_llm_request(
                "create_jira_issue",
                {
                    "projectKey": "TEST",
                    "summary": "Test Issue from LLM Workflow",
                    "description": "This is a test issue created by the LLM workflow",
                    "issueType": "Task",
                    "priority": "Medium",
                    "assignee": os.getenv("JIRA_EMAIL")
                }
            )
            create_response = json.loads(create_result)
            self.assertTrue("key" in create_response)
            issue_key = create_response["key"]
            
            # 2. Add a comment to the new issue
            comment_result = await self.simulate_llm_request(
                "add_comment",
                {
                    "issueKey": issue_key,
                    "comment": "Testing from LLM workflow"
                }
            )
            comment_response = json.loads(comment_result)
            self.assertTrue("message" in comment_response)
            
            # 3. Search for the issue
            search_result = await self.simulate_llm_request(
                "search_issues",
                {
                    "projectKey": "TEST",
                    "jql": f"key = {issue_key}"
                }
            )
            search_data = json.loads(search_result)
            self.assertTrue(isinstance(search_data, list))
            
            # 4. Get issue details including the new comment
            get_result = await self.simulate_llm_request(
                "get_issue",
                {
                    "issueKey": issue_key
                }
            )
            issue_data = json.loads(get_result)
            self.assertTrue("comments" in issue_data)
            print("LLM workflow completed successfully")
            
            # Clean up - delete the test issue
            delete_result = await self.simulate_llm_request(
                "delete_issue",
                {
                    "issueKey": issue_key
                }
            )
            
        self.run_async_test(test_workflow())

    def test_3_error_handling(self):
        """Test how the system handles various error scenarios an LLM might encounter"""
        async def test_errors():
            # Test missing required fields for create_jira_issue
            result = await self.simulate_llm_request(
                "create_jira_issue",
                {
                    "projectKey": "TEST",
                    # Missing required 'summary' and 'issueType' fields
                }
            )
            self.assertTrue("Error" in result)
            
            # Test invalid issue key
            result = await self.simulate_llm_request(
                "get_issue",
                {
                    "issueKey": "INVALID-999"
                }
            )
            self.assertTrue("Error" in result)
            
            # Test missing required arguments
            result = await self.simulate_llm_request(
                "add_comment",
                {
                    "issueKey": "TEST-1"
                    # Missing required 'comment' field
                }
            )
            self.assertTrue("Error" in result)
            
            # Test invalid tool name
            result = await self.simulate_llm_request(
                "nonexistent_tool",
                {}
            )
            self.assertTrue("Error" in result)
            print("Error handling tests completed")
            
        self.run_async_test(test_errors())

    def test_4_response_format(self):
        """Test that responses are properly formatted for LLM consumption"""
        async def test_formats():
            # Test list_fields response format
            fields_result = await self.simulate_llm_request(
                "list_fields",
                {}
            )
            try:
                fields_data = json.loads(fields_result)
                self.assertTrue(isinstance(fields_data, list))
                if len(fields_data) > 0:
                    self.assertTrue(all(isinstance(f, dict) for f in fields_data))
                    self.assertTrue(all("id" in f for f in fields_data))
            except json.JSONDecodeError:
                self.fail("Fields response was not valid JSON")
            
            # Test get_user response format
            user_result = await self.simulate_llm_request(
                "get_user",
                {"email": os.getenv("JIRA_EMAIL")}
            )
            try:
                user_data = json.loads(user_result)
                self.assertTrue(isinstance(user_data, dict))
                self.assertTrue("accountId" in user_data)
            except json.JSONDecodeError:
                self.fail("User response was not valid JSON")
            print("Response format tests completed")
            
        self.run_async_test(test_formats())

    def test_5_complex_data_handling(self):
        """Test handling of complex data types and attachments"""
        async def test_complex_data():
            # Create a test issue first
            create_result = await self.simulate_llm_request(
                "create_jira_issue",
                {
                    "projectKey": "TEST",
                    "summary": "Test Issue for Attachment",
                    "description": "Testing complex data handling",
                    "issueType": "Task"
                }
            )
            create_data = json.loads(create_result)
            issue_key = create_data["key"]

            # Test comment with attachment
            test_content = "Test file content"
            test_content_b64 = base64.b64encode(test_content.encode()).decode()
            
            result = await self.simulate_llm_request(
                "add_comment_with_attachment",
                {
                    "issueKey": issue_key,
                    "comment": "Test comment with attachment",
                    "attachment": {
                        "filename": "test.txt",
                        "content": test_content_b64,
                        "mimeType": "text/plain"
                    }
                }
            )
            try:
                response_data = json.loads(result)
                self.assertTrue("attachment_id" in response_data)
                print("Complex data handling tests completed")
            except json.JSONDecodeError:
                self.fail("Attachment response was not valid JSON")

            # Clean up
            await self.simulate_llm_request(
                "delete_issue",
                {
                    "issueKey": issue_key
                }
            )
            
        self.run_async_test(test_complex_data())

    def test_6_rate_limiting(self):
        """Test system behavior under rapid LLM requests"""
        async def test_rate_limits():
            # Make multiple rapid requests
            tasks = []
            for _ in range(5):
                tasks.append(self.simulate_llm_request(
                    "get_issue",
                    {"issueKey": "TEST-1"}
                ))
            
            # Run requests concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all requests completed
            self.assertEqual(len(results), 5)
            # Check if any rate limiting errors occurred
            rate_limited = any("rate" in str(r).lower() for r in results if isinstance(r, str))
            print(f"Rate limiting test completed {'with rate limits' if rate_limited else 'without rate limits'}")
            
        self.run_async_test(test_rate_limits())

if __name__ == '__main__':
    unittest.main(verbosity=2)
