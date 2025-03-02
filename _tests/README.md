# MCP JIRA Python Tests

This directory contains the test suite for the MCP JIRA Python server. The tests are organized into several categories to ensure comprehensive coverage of functionality.

## Test Files Overview

### test_jira_api.py
- Unit tests for the JIRA API interface
- Uses mocks to test API functionality without making actual JIRA calls
- Focuses on testing the business logic and data transformations
- Verifies error handling and edge cases

### test_jira_connection.py
- Tests basic connectivity to JIRA
- Verifies authentication and configuration
- Checks network-related error handling
- Ensures proper timeout and retry behavior

### test_jira_endpoints.py
- Tests all endpoints used by server.py
- Verifies correct request/response handling
- Ensures proper parameter validation
- Tests endpoint-specific error conditions
- Checks content type and response format handling

### test_jira_mcp_integration.py
- Integration tests that make actual server requests
- Tests the MCP server's handling of JIRA operations
- Verifies proper tool registration and discovery
- Tests the full request-response cycle through the MCP protocol
- Checks proper environment variable handling

### test_jira_mcp_system.py
- System-level tests focusing on user patterns
- Tests heavy usage scenarios and load handling
- Verifies system stability under various conditions
- Tests complex workflows and multi-step operations
- Includes performance and resource utilization tests

## Running the Tests

To run the full test suite:

```bash
python -m unittest discover tests
```

To run a specific test file:

```bash
python -m unittest tests/test_jira_api.py
```

## Environment Setup

The integration and system tests require proper JIRA credentials. Set these environment variables before running the tests:

```bash
export JIRA_HOST="your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

## Test Coverage

TODO: Add coverage reporting and maintain a minimum coverage threshold