# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.0] - 2025-01-17

### Changed
- **BREAKING**: Merged `notify` and `send_message` tools into single `send` tool
- `send` now supports all features: urgency levels, thread replies, and user mentions

### Removed
- `notify` tool (use `send` with `urgency` parameter instead)
- `send_message` tool (use `send` with `thread_ts` parameter instead)

## [0.2.1] - 2025-01-17

### Changed
- Updated server instructions to explain blocking behavior of ask_user
- Added example in ask_user docstring showing how to run non-blocking with Task tool
- Clearer documentation for agents on async usage pattern

## [0.2.0] - 2025-01-17

### Added
- **MCP Tasks support** for async `ask_user` execution via FastMCP 2.x
- Background task execution - `ask_user` can now run as a non-blocking task
- Progress reporting during long waits for user replies
- Async polling for Slack thread replies with configurable intervals

### Changed
- Switched from official MCP SDK to FastMCP 2.x for enhanced task support
- `ask_user` is now an async function with `task=True` decorator
- Improved wait loop with 5-second polling intervals instead of blocking wait

## [0.1.0] - 2025-01-17

### Added
- Initial release of slack-notifier-mcp server
- `notify` tool for sending notifications with urgency levels (normal, important, critical)
- `ask_user` tool for bidirectional communication - ask questions and wait for Slack replies
- `send_message` tool for lower-level message sending and thread replies
- `get_thread_replies` tool for checking thread responses
- User mention support via `SLACK_USER_ID` environment variable
- Slack mrkdwn formatting support in all messages
- Comprehensive README with setup instructions for Claude Code, VS Code, Cursor, and other MCP clients
