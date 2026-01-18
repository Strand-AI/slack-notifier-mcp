"""Slack Notifier MCP Server - Bidirectional Slack communication for Claude Code."""

from __future__ import annotations

import asyncio
from typing import Literal

from fastmcp import FastMCP
from fastmcp.dependencies import Progress

from .slack_client import SlackClient, SlackConfig

# Create the MCP server with task support
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
retrieve their responses using the ask_user tool or get_thread_replies.

IMPORTANT: The ask_user tool BLOCKS while waiting for a reply. To run it
non-blocking, wrap the call in a background task/agent. This allows you to
continue working while waiting for the user's Slack reply.""",
)


def _get_client() -> SlackClient:
    """Get or create a Slack client."""
    config = SlackConfig.from_env()
    return SlackClient(config)


@mcp.tool(task=True)
async def ask_user(
    question: str,
    channel: str | None = None,
    context: str | None = None,
    timeout_minutes: int = 5,
    progress: Progress = Progress(),
) -> dict:
    """Send a question to the user via Slack and wait for their reply.

    Use this when you need user input or a decision. The user will be notified
    and can reply in the Slack thread. This will BLOCK until the user replies
    or the timeout is reached.

    IMPORTANT - NON-BLOCKING USAGE: To avoid blocking, run this tool in a
    background agent/task. Example with Claude Code's Task tool:

        Task(
            prompt="Call ask_user with question='Your question here'",
            run_in_background=True
        )

    This lets you continue working while waiting for the Slack reply. You'll
    be notified when the background task completes with the user's response.

    Args:
        question: The question to ask the user.
        channel: Channel name or ID. Uses SLACK_DEFAULT_CHANNEL if not specified.
        context: Optional context to include (e.g., what you're working on).
        timeout_minutes: How long to wait for a reply (default 5 minutes, max 30).

    Returns:
        Dict with success status and user's reply text if received.
    """
    client = _get_client()

    # Cap timeout at 30 minutes
    timeout_minutes = min(timeout_minutes, 30)
    timeout_seconds = timeout_minutes * 60

    # Format the question message
    if context:
        formatted_message = (
            f":question: *Claude Code needs your input*\n\n"
            f"*Context:* {context}\n\n"
            f"*Question:* {question}\n\n"
            f"_Reply in this thread within {timeout_minutes} minutes._"
        )
    else:
        formatted_message = (
            f":question: *Claude Code needs your input*\n\n"
            f"{question}\n\n"
            f"_Reply in this thread within {timeout_minutes} minutes._"
        )

    # Report progress: sending question
    await progress.set_message("Sending question to Slack...")

    # Send the question
    send_result = client.send_message(text=formatted_message, channel=channel)

    if not send_result.ok:
        return {
            "success": False,
            "message": f"Failed to send question: {send_result.error}",
            "error": send_result.error,
            "reply": None,
        }

    # Report progress: waiting for reply
    await progress.set_message(f"Waiting for reply (up to {timeout_minutes} min)...")
    await progress.set_total(timeout_seconds)

    # Poll for reply with progress updates
    poll_interval = 5  # seconds
    elapsed = 0

    while elapsed < timeout_seconds:
        # Check for replies
        replies = client.get_thread_replies(
            channel=send_result.channel,
            thread_ts=send_result.ts,
            since_ts=None,
        )

        if replies:
            reply = replies[0]  # Get the first reply
            # Send acknowledgment
            client.send_message(
                text=":white_check_mark: Got it, thanks!",
                channel=send_result.channel,
                thread_ts=send_result.ts,
            )

            return {
                "success": True,
                "message": "Received user reply",
                "reply": reply.text,
                "replied_by": reply.user_name or reply.user,
                "user_id": reply.user,
                "ts": reply.ts,
                "channel": send_result.channel,
                "thread_ts": send_result.ts,
            }

        # Update progress
        await progress.set_current(elapsed)
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    # Timeout reached
    client.send_message(
        text=f":hourglass: No reply received after {timeout_minutes} minutes. Continuing without input.",
        channel=send_result.channel,
        thread_ts=send_result.ts,
    )

    return {
        "success": False,
        "message": f"No reply received within {timeout_minutes} minutes",
        "reply": None,
        "channel": send_result.channel,
        "thread_ts": send_result.ts,
    }


@mcp.tool()
def send(
    message: str,
    channel: str | None = None,
    thread_ts: str | None = None,
    urgency: Literal["normal", "important", "critical"] = "normal",
    mention_user: bool = False,
) -> dict:
    """Send a message to a Slack channel or thread.

    Args:
        message: Message text. Supports Slack mrkdwn formatting.
        channel: Channel name or ID. Uses SLACK_DEFAULT_CHANNEL if not specified.
        thread_ts: Thread timestamp to reply in a thread.
        urgency: Message urgency level. 'critical' adds @here mention.
        mention_user: If True, @mentions the configured user (requires SLACK_USER_ID).

    Returns:
        Dict with success status and message details.
    """
    from .tools.messaging import send as _send

    return _send(
        message=message,
        channel=channel,
        thread_ts=thread_ts,
        urgency=urgency,
        mention_user=mention_user,
    )


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
