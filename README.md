# OpenCode Client

A Python client for interacting with the [OpenCode](https://opencode.ai) server, enabling programmatic access to AI-powered coding sessions with file operations and conversation history.

## Installation

```bash
pip install opencode-client
```

## Quick Start

```python
import asyncio
from opencode_client import OpenCodeClient


async def main():
    # Initialize client
    client = OpenCodeClient(
        base_url="http://localhost:8080",
        model_provider="anthropic",
        model="claude-sonnet-4",
        timeout=600,
    )

    # Create a session
    session = await client.create_current_session(title="My Coding Session")

    # Send a message
    response = await client.send_message(
        "Write a hello world function in Python"
    )
    print(response.to_string())


asyncio.run(main())
```

## Features

- **Session Management**: Create, list, update, and delete coding sessions
- **Message Handling**: Send text and file-based messages with system prompts
- **File Operations**: Search files by name or content, read directories, check file status
- **Chat History**: Automatic tracking of conversation history

## Usage Examples

### Session Management

```python
# Create a new session
session = await client.create_current_session(title="Debug Session")

# List all sessions
sessions = await client.list_sessions()

# Update session title
await client.update_session(title="New Title")

# Abort running session
await client.abort_session()

# Delete session
await client.delete_session()
```

### Sending Messages

```python
# Simple text message
response = await client.send_message("Explain async/await in Python")

# Message with system prompt
response = await client.send_message(
    "Write tests for this function",
    system_message="You are an expert in pytest",
)

# Message with file attachment
response = await client.send_message(
    "Review this code", file="path/to/script.py"
)

# Message with multiple files
response = await client.send_message(
    "Compare these implementations", file=["version1.py", "version2.py"]
)

# Message with URL
response = await client.send_message(
    "Analyze this code", file="https://example.com/code.py"
)
```

### File Operations

```python
# Search files by name
files = await client.search_file_by_name("README")

# Search files by content
matches = await client.search_file_by_text("def main")

# Read directory contents
file_info = await client.read_directory_files("/path/to/dir")

# Get file status
status = await client.get_files_status()
```

### Chat History

```python
# Access structured chat history
for message in client.chat_history:
    print(message)

# Access string representation of chat history
for msg_string in client.string_chat_history:
    print(msg_string)
```

## Configuration

### Client Parameters

- `base_url`: API endpoint URL
- `model_provider`: Provider name (e.g., "anthropic", "openai")
- `model`: Model identifier (e.g., "claude-sonnet-4")
- `timeout`: Request timeout in seconds (default: 600)

## Advanced Usage

### Working with Multiple Sessions

```python
# Create parent session
parent = await client.create_current_session(title="Parent Session")

# Create child session
child = await client.create_current_session(
    title="Child Session", parent_id=parent.id
)

# Send message to specific session
response = await client.send_message(
    "Help with this bug", session_id=parent.id
)
```

### Error Handling

```python
try:
    response = await client.send_message("Your question")
except ValueError as e:
    print(f"Invalid input: {e}")
except httpx.HTTPError as e:
    print(f"API error: {e}")
```

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) to get started.

## License

This project is licensed under the [MIT License](./LICENSE).
