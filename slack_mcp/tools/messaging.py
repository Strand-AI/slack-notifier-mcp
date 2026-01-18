"""Slack messaging tools for MCP server."""

from __future__ import annotations

from typing import Literal

from ..slack_client import SlackClient, SlackConfig


def _get_client() -> SlackClient:
    """Get or create a Slack client."""
    config = SlackConfig.from_env()
    return SlackClient(config)


def ask_user(
    question: str,
    channel: str | None = None,
    context: str | None = None,
    timeout_minutes: int = 5,
) -> dict:
    """Send a question to the user via Slack and wait for their reply.

    Use this when you need user input or a decision. The user will be notified
    and can reply in the Slack thread.

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

    # Send the question
    send_result = client.send_message(text=formatted_message, channel=channel)

    if not send_result.ok:
        return {
            "success": False,
            "message": f"Failed to send question: {send_result.error}",
            "error": send_result.error,
            "reply": None,
        }

    # Wait for reply
    reply = client.wait_for_reply(
        channel=send_result.channel,
        thread_ts=send_result.ts,
        timeout_seconds=timeout_seconds,
    )

    if reply:
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
    else:
        # Send timeout message
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
    client = _get_client()

    # Add user mention if requested
    mention_prefix = ""
    if mention_user:
        mention = client.mention_user()
        if mention:
            mention_prefix = f"{mention} "

    # Format message based on urgency
    if urgency == "critical":
        formatted_message = f"{mention_prefix}<!here> :rotating_light: *CRITICAL*\n{message}"
    elif urgency == "important":
        formatted_message = f"{mention_prefix}:warning: *Important*\n{message}"
    else:
        formatted_message = f"{mention_prefix}{message}"

    result = client.send_message(text=formatted_message, channel=channel, thread_ts=thread_ts)

    if result.ok:
        return {
            "success": True,
            "message": "Message sent",
            "ts": result.ts,
            "channel": result.channel,
        }
    else:
        return {
            "success": False,
            "message": f"Failed to send message: {result.error}",
            "error": result.error,
        }


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
    client = _get_client()

    try:
        replies = client.get_thread_replies(channel, thread_ts, since_ts)

        return {
            "success": True,
            "message": f"Found {len(replies)} replies",
            "replies": [
                {
                    "text": r.text,
                    "user": r.user_name or r.user,
                    "user_id": r.user,
                    "ts": r.ts,
                }
                for r in replies
            ],
            "count": len(replies),
        }
    except RuntimeError as e:
        return {
            "success": False,
            "message": str(e),
            "replies": [],
            "count": 0,
        }
