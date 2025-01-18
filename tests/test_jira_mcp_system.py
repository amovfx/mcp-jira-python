import unittest
import asyncio
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import json
import ast
import warnings
import sys
import tracemalloc
from io import StringIO
import base64

class TestJiraMCPSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up the path to the MCP server script
        cls.server_script = os.getenv("MCP_SERVER_SCRIPT", "server.py")
        cls.command = "python" if cls.server_script.endswith(".py") else "node"

    async def setup_session(self):
        """Set up the MCP client session."""
        self.exit_stack = AsyncExitStack()
        server_params = StdioServerParameters(
            command=self.command,
            args=[self.server_script],
            env=dict(os.environ),
        )
        # Use AsyncExitStack to ensure proper cleanup
        self.stdio, self.write = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()

    async def teardown_session(self):
        """Tear down the MCP client session."""
        await self.exit_stack.aclose()

    async def get_tools(self):
        """Retrieve the list of tools from the MCP session."""
        tools_response = await self.session.list_tools()
        return tools_response.tools

    async def simulate_llm_request(self, tool_name, arguments):
        """Simulate an LLM request to a tool via MCP."""
        try:
            tools = await self.get_tools()
            tool_found = next((tool for tool in tools if tool.name == tool_name), None)
            if not tool_found:
                raise ValueError(f"Tool {tool_name} not found")
            response = await self.session.call_tool(tool_name, arguments)

            # Debug: Log the raw response
            print(f"Debug: Response content from {tool_name}: {response.content} (type: {type(response.content)})")

            # Handle `TextContent` objects if the response is a list
            if isinstance(response.content, list) and len(response.content) > 0:
                first_item = response.content[0]
                if hasattr(first_item, "text"):
                    # Convert the text content to a dictionary
                    return json.loads(first_item.text.replace("'", '"'))  # Replace single quotes with double quotes for JSON compatibility
                else:
                    raise ValueError(f"Unexpected response format: {response.content}")

            # Return raw content if it doesn't fit the above pattern
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"

    def run_async_test(self, coroutine):
        """Helper to run async tests."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coroutine)
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def test_1_server_initialization(self):
        async def test_init():
            await self.setup_session()
            try:
                tools = await self.get_tools()
                self.assertTrue(len(tools) > 0)
                self.assertTrue(any(tool.name == "create_jira_issue" for tool in tools))
                print("Server initialized successfully with tools:", [tool.name for tool in tools])
            finally:
                await self.teardown_session()

        self.run_async_test(test_init())

    def test_2_llm_workflow_success(self):
        async def test_workflow():
            await self.setup_session()
            try:
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
                self.assertTrue("key" in create_result)
                issue_key = create_result["key"]

                comment_result = await self.simulate_llm_request(
                    "add_comment",
                    {
                        "issueKey": issue_key,
                        "comment": "Testing from LLM workflow"
                    }
                )
                self.assertTrue("message" in comment_result)
            finally:
                await self.teardown_session()

        self.run_async_test(test_workflow())

    def test_3_error_handling(self):
        """Test how the system handles various error scenarios an LLM might encounter"""
        async def test_errors():
            await self.setup_session()
            try:
                # Test invalid issue key
                result = await self.simulate_llm_request(
                    "get_issue",
                    {
                        "issueKey": "INVALID-999"
                    }
                )
                self.assertTrue("Error" in str(result))
                
                # Test missing required arguments
                result = await self.simulate_llm_request(
                    "add_comment",
                    {
                        "issueKey": "TEST-123"
                        # Missing required 'comment' field
                    }
                )
                self.assertTrue("Error" in str(result))
                
                # Test invalid tool name
                result = await self.simulate_llm_request(
                    "nonexistent_tool",
                    {}
                )
                self.assertTrue("Error" in str(result))
                print("Error handling tests completed")
            finally:
                await self.teardown_session()
            
        self.run_async_test(test_errors())

    def test_4_response_format(self):
        """Test that responses are properly formatted for LLM consumption"""
        async def test_formats():
            await self.setup_session()
            try:
                # Test list_fields response format
                fields_result = await self.simulate_llm_request(
                    "list_fields",
                    {}
                )
                self.assertTrue(isinstance(fields_result, (list, dict)))
                if isinstance(fields_result, list) and len(fields_result) > 0:
                    self.assertTrue(all(isinstance(f, dict) for f in fields_result))
                    self.assertTrue(all("id" in f for f in fields_result))
                
                # Test get_user response format
                user_result = await self.simulate_llm_request(
                    "get_user",
                    {"email": os.getenv("JIRA_EMAIL")}
                )
                self.assertTrue(isinstance(user_result, dict))
                self.assertTrue("accountId" in user_result)
                print("Response format tests completed")
            finally:
                await self.teardown_session()
            
        self.run_async_test(test_formats())

    def test_5_complex_data_handling(self):
        """Test handling of complex data types and attachments"""
        async def test_complex_data():
            await self.setup_session()
            try:
                # Test comment with attachment
                test_content = "Test file content"
                test_content_b64 = base64.b64encode(test_content.encode()).decode()
                
                result = await self.simulate_llm_request(
                    "add_comment_with_attachment",
                    {
                        "issueKey": "TEST-123",
                        "comment": "Test comment with attachment",
                        "attachment": {
                            "filename": "test.txt",
                            "content": test_content_b64,
                            "mimeType": "text/plain"
                        }
                    }
                )
                self.assertTrue(isinstance(result, dict))
                self.assertTrue("attachment_id" in result or "id" in result)
                print("Complex data handling tests completed")
            finally:
                await self.teardown_session()
            
        self.run_async_test(test_complex_data())

    def test_6_rate_limiting(self):
        """Test system behavior under rapid LLM requests"""
        async def test_rate_limits():
            await self.setup_session()
            try:
                # Make multiple rapid requests
                tasks = []
                for _ in range(5):
                    tasks.append(self.simulate_llm_request(
                        "get_issue",
                        {"issueKey": "TEST-123"}
                    ))
                
                # Run requests concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Verify all requests completed
                self.assertEqual(len(results), 5)
                # Check if any rate limiting errors occurred
                rate_limited = any("rate" in str(r).lower() for r in results if isinstance(r, str))
                print(f"Rate limiting test completed {'with rate limits' if rate_limited else 'without rate limits'}")
            finally:
                await self.teardown_session()
            
        self.run_async_test(test_rate_limits())

def main():
    # Enable tracemalloc for debugging
    tracemalloc.start()

    # Capture warnings
    warnings.simplefilter("always", ResourceWarning)
    warning_stream = StringIO()
    with warnings.catch_warnings(record=True) as captured_warnings:
        warnings.simplefilter("always")

        # Run the tests
        test_runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        test_suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestJiraMCPSystem)
        result = test_runner.run(test_suite)

    # Gather warnings and memory usage
    warning_summary = [str(warning.message) for warning in captured_warnings]
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")

    # Pass/fail summary
    if result.wasSuccessful():
        print("\n[PASS] All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed.")
        sys.exit(1)

    # Additional debugging output
    print("\n[Warnings]")
    for warning in warning_summary:
        print(f"- {warning}")

    print("\n[Memory Debugging (Top 10)]")
    for stat in top_stats[:10]:
        print(stat)

if __name__ == "__main__":
    main()