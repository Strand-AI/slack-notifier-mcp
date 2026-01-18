# Slack Notifier MCP

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

MCP server for **bidirectional Slack communication** with Claude Code. Get notified when tasks complete, and respond to Claude's questions directly from Slack.

## Quick Start

```bash
# Add to Claude Code (one command)
claude mcp add slack-notifier -s user \
  -e SLACK_BOT_TOKEN=xoxb-your-token \
  -e SLACK_DEFAULT_CHANNEL=C1234567890 \
  -- uvx slack-notifier-mcp
```

## Features

- **Notify** - Send notifications when tasks complete, errors occur, or when stepping away
- **Ask & Wait** - Ask questions and wait for replies via Slack threads
- **Bidirectional** - Reply to Claude from Slack, get responses back in your terminal
- **Urgency Levels** - Normal, important, and critical notifications with appropriate formatting

## Slack App Setup

Before using this server, you need to create a Slack app:

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App**
2. Choose **From scratch**, name it (e.g., "Claude Code"), and select your workspace
3. Go to **OAuth & Permissions** in the sidebar
4. Under **Scopes > Bot Token Scopes**, add:
   - `chat:write` - Send messages
   - `channels:history` - Read public channel messages
   - `groups:history` - Read private channel messages
   - `im:history` - Read DM messages
   - `users:read` - Get user display names
5. Click **Install to Workspace** at the top
6. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

To get your default channel ID:
- Open Slack, right-click the channel, and select **View channel details**
- At the bottom, copy the **Channel ID** (starts with `C`)

## Installation

### Claude Code (Recommended)

```bash
claude mcp add slack-notifier -s user \
  -e SLACK_BOT_TOKEN=xoxb-your-token \
  -e SLACK_DEFAULT_CHANNEL=C1234567890 \
  -- uvx slack-notifier-mcp
```

### VS Code

```bash
code --add-mcp '{"name":"slack-notifier","command":"uvx","args":["slack-notifier-mcp"],"env":{"SLACK_BOT_TOKEN":"xoxb-your-token","SLACK_DEFAULT_CHANNEL":"C1234567890"}}'
```

### Other MCP Clients

<details>
<summary><strong>Claude Desktop</strong></summary>

Add to your Claude Desktop config:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "slack-notifier": {
      "command": "uvx",
      "args": ["slack-notifier-mcp"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-token",
        "SLACK_DEFAULT_CHANNEL": "C1234567890"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Cursor</strong></summary>

1. Go to **Settings → MCP → Add new MCP Server**
2. Select `command` type
3. Enter command: `uvx slack-notifier-mcp`
4. Add environment variables for `SLACK_BOT_TOKEN` and `SLACK_DEFAULT_CHANNEL`

Or add to `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "slack-notifier": {
      "command": "uvx",
      "args": ["slack-notifier-mcp"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-token",
        "SLACK_DEFAULT_CHANNEL": "C1234567890"
      }
    }
  }
}
```

</details>

<details>
<summary><strong>Windsurf / Other MCP Clients</strong></summary>

Any MCP-compatible client can use slack-notifier:

```json
{
  "mcpServers": {
    "slack-notifier": {
      "command": "uvx",
      "args": ["slack-notifier-mcp"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-token",
        "SLACK_DEFAULT_CHANNEL": "C1234567890"
      }
    }
  }
}
```

</details>

### Local Development

```bash
git clone https://github.com/strand-ai/slack-notifier-mcp.git
cd slack-notifier-mcp
uv sync
uv run slack-notifier-mcp
```

## MCP Tools

### `notify`

Send a notification to Slack.

```python
notify(
    message="GPU instance is ready! SSH: ubuntu@192.168.1.100",
    urgency="important"  # or "normal", "critical"
)
```

**Parameters:**
- `message` (required): Notification text (supports Slack mrkdwn)
- `channel` (optional): Channel ID or name (uses default if not set)
- `urgency` (optional): `normal`, `important`, or `critical`

### `ask_user`

Send a question and wait for the user's reply.

```python
ask_user(
    question="Should I use PostgreSQL or SQLite for the database?",
    context="Setting up the backend for the new API",
    timeout_minutes=10
)
# Returns: {"success": True, "reply": "Use PostgreSQL", ...}
```

**Parameters:**
- `question` (required): The question to ask
- `channel` (optional): Channel ID or name
- `context` (optional): Additional context about what you're working on
- `timeout_minutes` (optional): How long to wait (default 5, max 30)

### `send_message`

Lower-level message sending for conversational use.

```python
send_message(
    message="Done with the first step, moving on...",
    thread_ts="1234567890.123456"  # Reply in thread
)
```

### `get_thread_replies`

Check for new replies in a thread.

```python
get_thread_replies(
    channel="C1234567890",
    thread_ts="1234567890.123456",
    since_ts="1234567891.000000"  # Only newer messages
)
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SLACK_BOT_TOKEN` | Yes | Bot token from Slack app (xoxb-...) |
| `SLACK_DEFAULT_CHANNEL` | No | Default channel for notifications |

## Example Usage

Tell Claude Code:

> "Notify me on Slack when the tests finish running"

> "Ask me on Slack whether to proceed with the database migration"

> "Send a Slack notification if any errors occur while I'm away"

## Debugging

Run the MCP inspector to test tools:

```bash
npx @anthropics/mcp-inspector uvx slack-notifier-mcp
```

Check if your token works:

```bash
curl -H "Authorization: Bearer xoxb-your-token" \
  https://slack.com/api/auth.test
```

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Format code
uv run black slack_mcp
uv run ruff check slack_mcp --fix
```

## License

MIT
