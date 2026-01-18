# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
