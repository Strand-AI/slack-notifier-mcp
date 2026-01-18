"""Basic tests for slack-notifier-mcp server."""

import pytest


def test_server_import():
    """Test that the server can be imported."""
    from slack_mcp.server import mcp

    assert mcp is not None


def test_tools_registered():
    """Test that all tools are registered."""
    from slack_mcp.server import mcp

    tool_names = list(mcp._tool_manager._tools.keys())
    assert "send" in tool_names
    assert "ask_user" in tool_names
    assert "get_thread_replies" in tool_names


def test_slack_config_requires_token():
    """Test that SlackConfig requires SLACK_BOT_TOKEN."""
    import os

    from slack_mcp.slack_client import SlackConfig

    # Remove token if present
    original = os.environ.pop("SLACK_BOT_TOKEN", None)

    try:
        with pytest.raises(ValueError, match="SLACK_BOT_TOKEN"):
            SlackConfig.from_env()
    finally:
        # Restore original
        if original:
            os.environ["SLACK_BOT_TOKEN"] = original


def test_slack_config_from_env():
    """Test that SlackConfig loads from environment."""
    import os

    from slack_mcp.slack_client import SlackConfig

    # Set test values
    os.environ["SLACK_BOT_TOKEN"] = "xoxb-test-token"
    os.environ["SLACK_DEFAULT_CHANNEL"] = "C12345"

    try:
        config = SlackConfig.from_env()
        assert config.bot_token == "xoxb-test-token"
        assert config.default_channel == "C12345"
    finally:
        # Clean up
        del os.environ["SLACK_BOT_TOKEN"]
        del os.environ["SLACK_DEFAULT_CHANNEL"]
