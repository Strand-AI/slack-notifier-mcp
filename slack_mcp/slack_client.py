"""Slack API client wrapper for MCP server."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


@dataclass
class SlackConfig:
    """Configuration for Slack client."""

    bot_token: str
    default_channel: str | None = None
    user_id: str | None = None

    @classmethod
    def from_env(cls) -> "SlackConfig":
        """Load configuration from environment variables."""
        bot_token = os.environ.get("SLACK_BOT_TOKEN")
        if not bot_token:
            raise ValueError(
                "SLACK_BOT_TOKEN environment variable is required. "
                "Create a Slack app at https://api.slack.com/apps and add a bot token."
            )

        default_channel = os.environ.get("SLACK_DEFAULT_CHANNEL")
        user_id = os.environ.get("SLACK_USER_ID")

        return cls(bot_token=bot_token, default_channel=default_channel, user_id=user_id)


@dataclass
class Message:
    """A Slack message."""

    text: str
    user: str
    user_name: str | None
    ts: str
    thread_ts: str | None
    channel: str


@dataclass
class SendResult:
    """Result of sending a message."""

    ok: bool
    ts: str | None = None
    channel: str | None = None
    error: str | None = None


class SlackClient:
    """Wrapper around Slack WebClient for MCP operations."""

    def __init__(self, config: SlackConfig):
        self.config = config
        self.client = WebClient(token=config.bot_token)
        self._user_cache: dict[str, str] = {}

    def _get_user_name(self, user_id: str) -> str | None:
        """Get user's display name from user ID."""
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        try:
            result = self.client.users_info(user=user_id)
            if result["ok"]:
                user = result["user"]
                name = user.get("real_name") or user.get("name") or user_id
                self._user_cache[user_id] = name
                return name
        except SlackApiError:
            pass

        return None

    def send_message(
        self,
        text: str,
        channel: str | None = None,
        thread_ts: str | None = None,
    ) -> SendResult:
        """Send a message to a Slack channel or thread.

        Args:
            text: Message text (supports Slack mrkdwn formatting)
            channel: Channel ID or name. Uses default if not specified.
            thread_ts: Thread timestamp to reply in a thread.

        Returns:
            SendResult with message timestamp if successful.
        """
        target_channel = channel or self.config.default_channel
        if not target_channel:
            return SendResult(
                ok=False,
                error="No channel specified and no default channel configured. "
                "Set SLACK_DEFAULT_CHANNEL or pass channel parameter.",
            )

        try:
            result = self.client.chat_postMessage(
                channel=target_channel,
                text=text,
                thread_ts=thread_ts,
            )

            return SendResult(
                ok=True,
                ts=result["ts"],
                channel=result["channel"],
            )

        except SlackApiError as e:
            return SendResult(ok=False, error=str(e.response["error"]))

    def get_thread_replies(
        self,
        channel: str,
        thread_ts: str,
        since_ts: str | None = None,
    ) -> list[Message]:
        """Get replies in a thread.

        Args:
            channel: Channel ID containing the thread.
            thread_ts: Timestamp of the parent message.
            since_ts: Only return messages after this timestamp.

        Returns:
            List of messages in the thread.
        """
        try:
            result = self.client.conversations_replies(
                channel=channel,
                ts=thread_ts,
                oldest=since_ts,
            )

            messages = []
            for msg in result.get("messages", []):
                # Skip the parent message and bot messages
                if msg.get("ts") == thread_ts:
                    continue
                if msg.get("bot_id"):
                    continue
                if since_ts and float(msg["ts"]) <= float(since_ts):
                    continue

                messages.append(
                    Message(
                        text=msg.get("text", ""),
                        user=msg.get("user", ""),
                        user_name=self._get_user_name(msg.get("user", "")),
                        ts=msg["ts"],
                        thread_ts=msg.get("thread_ts"),
                        channel=channel,
                    )
                )

            return messages

        except SlackApiError as e:
            raise RuntimeError(f"Failed to get thread replies: {e.response['error']}") from e

    def wait_for_reply(
        self,
        channel: str,
        thread_ts: str,
        timeout_seconds: int = 300,
        poll_interval: int = 5,
    ) -> Message | None:
        """Wait for a reply in a thread.

        Args:
            channel: Channel ID containing the thread.
            thread_ts: Timestamp of the parent message.
            timeout_seconds: Maximum time to wait (default 5 minutes).
            poll_interval: Seconds between poll attempts (default 5).

        Returns:
            First new message in the thread, or None if timeout.
        """
        start_time = time.time()
        last_ts = thread_ts

        while time.time() - start_time < timeout_seconds:
            replies = self.get_thread_replies(channel, thread_ts, since_ts=last_ts)

            if replies:
                return replies[0]

            time.sleep(poll_interval)

        return None

    def get_channel_id(self, channel_name: str) -> str | None:
        """Get channel ID from channel name.

        Args:
            channel_name: Channel name (with or without #).

        Returns:
            Channel ID or None if not found.
        """
        name = channel_name.lstrip("#")

        try:
            # Try public channels first
            result = self.client.conversations_list(types="public_channel,private_channel")
            for channel in result.get("channels", []):
                if channel["name"] == name:
                    return channel["id"]

            # Paginate if needed
            while result.get("response_metadata", {}).get("next_cursor"):
                result = self.client.conversations_list(
                    types="public_channel,private_channel",
                    cursor=result["response_metadata"]["next_cursor"],
                )
                for channel in result.get("channels", []):
                    if channel["name"] == name:
                        return channel["id"]

        except SlackApiError:
            pass

        return None

    def get_bot_user_id(self) -> str | None:
        """Get the bot's own user ID."""
        try:
            result = self.client.auth_test()
            return result.get("user_id")
        except SlackApiError:
            return None

    def get_user_id(self) -> str | None:
        """Get the configured user ID for mentions."""
        return self.config.user_id

    def mention_user(self) -> str | None:
        """Get a mention string for the configured user, e.g. <@U12345>."""
        if self.config.user_id:
            return f"<@{self.config.user_id}>"
        return None
