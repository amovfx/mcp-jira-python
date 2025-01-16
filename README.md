# MCP-JIRA-Python

A Python implementation of an MCP server for JIRA integration.

## Installation

```bash
# Install the package in editable mode with test dependencies
pip install -e ".[test]"
```

## Running Tests

The project uses pytest for testing. There are three test suites:

1. Unit Tests:
```bash
pytest tests/test_jira_api.py -v
```

2. Integration Tests:
```bash
pytest tests/test_jira_integration.py -v
```

3. System Tests:
```bash
pytest tests/test_jira_mcp_system.py -v
```

To run all tests:
```bash
pytest tests/ -v
```

### Environment Variables

The integration and system tests require the following environment variables:

```bash
export JIRA_HOST="your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-api-token"
```

## Test Coverage

To generate a test coverage report:

```bash
pytest --cov=jira_api tests/
```

## Project Structure

```
mcp-jira-python/
├── README.md
├── pyproject.toml
├── src/
│   └── jira_api/
│       ├── __init__.py
│       └── server.py
└── tests/
    ├── __init__.py
    ├── test_jira_api.py
    ├── test_jira_integration.py
    └── test_jira_mcp_system.py
```