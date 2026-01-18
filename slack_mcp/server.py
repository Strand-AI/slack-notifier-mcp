"""Slack Notifier MCP Server - Bidirectional Slack communication for Claude Code."""

from __future__ import annotations

from typing import Literal

from mcp.server.fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP(
    "slack-notifier",
    instructions="""Slack notification and communication server for Claude Code.

Use this server to:
- Send notifications when tasks complete or need attention
- Ask the user questions and wait for their reply via Slack
- Communicate asynchronously when the user is away from their terminal

Environment variables required:
- SLACK_BOT_TOKEN: Your Slack bot token (xoxb-...)
- SLACK_DEFAULT_CHANNEL: Optional default channel for messages
- SLACK_USER_ID: Optional user ID for @mentions (get from Slack profile)

The user can reply to your messages in Slack threads, and you can
retrieve their responses using the ask_user tool or get_thread_replies.""",
)


@mcp.tool()
def notify(
    message: str,
    channel: str | None = None,
    urgency: Literal["normal", "important", "critical"] = "normal",
    mention_user: bool = False,
) -> dict:
    """Send a notification message to Slack.

    Use this to notify the user about task completion, errors, or when you need their input.

    Args:
        message: The notification message. Supports Slack mrkdwn formatting.
        channel: Channel name or ID. Uses SLACK_DEFAULT_CHANNEL if not specified.
        urgency: Message urgency level. 'critical' adds @here mention.
        mention_user: If True, @mentions the configured user (requires SLACK_USER_ID).

    Returns:
        Dict with success status, message timestamp, and channel.
    """
    from .tools.messaging import notify as _notify

    return _notify(message=message, channel=channel, urgency=urgency, mention_user=mention_user)


@mcp.tool()
def ask_user(
    question: str,
    channel: str | None = None,
    context: str | None = None,
    timeout_minutes: int = 5,
) -> dict:
    """Send a question to the user via Slack and wait for their reply.

    Use this when you need user input or a decision. The user will be notified
    and can reply in the Slack thread. This will BLOCK until the user replies
    or the timeout is reached.

    Args:
        question: The question to ask the user.
        channel: Channel name or ID. Uses SLACK_DEFAULT_CHANNEL if not specified.
        context: Optional context to include (e.g., what you're working on).
        timeout_minutes: How long to wait for a reply (default 5 minutes, max 30).

    Returns:
        Dict with success status and user's reply text if received.
    """
    from .tools.messaging import ask_user as _ask_user

    return _ask_user(
        question=question,
        channel=channel,
        context=context,
        timeout_minutes=timeout_minutes,
    )


@mcp.tool()
def send_message(
    message: str,
    channel: str | None = None,
    thread_ts: str | None = None,
) -> dict:
    """Send a message to a Slack channel or thread.

    Lower-level than notify() - use this for conversational messages or
    when you need to reply in a specific thread.

    Args:
        message: Message text. Supports Slack mrkdwn formatting.
        channel: Channel name or ID. Uses SLACK_DEFAULT_CHANNEL if not specified.
        thread_ts: Thread timestamp to reply in a thread.

    Returns:
        Dict with success status and message details.
    """
    from .tools.messaging import send_message as _send_message

    return _send_message(message=message, channel=channel, thread_ts=thread_ts)


@mcp.tool()
def get_thread_replies(
    channel: str,
    thread_ts: str,
    since_ts: str | None = None,
) -> dict:
    """Get replies in a Slack thread.

    Use this to check for new messages in a thread you started.

    Args:
        channel: Channel ID containing the thread.
        thread_ts: Timestamp of the parent message.
        since_ts: Only return messages after this timestamp (optional).

    Returns:
        Dict with success status and list of replies.
    """
    from .tools.messaging import get_thread_replies as _get_thread_replies

    return _get_thread_replies(channel=channel, thread_ts=thread_ts, since_ts=since_ts)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
