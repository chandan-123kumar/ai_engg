import pytest
from unittest.mock import patch, MagicMock
from src.agents.worker.claude_cli import ClaudeCliProvider
from src.agents.worker.claude_api import ClaudeApiProvider

# --- Claude CLI Provider ---

def test_claude_cli_returns_text():
    provider = ClaudeCliProvider(cli_path="claude", model="claude-sonnet-4-6")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"result": "here is the code"}',
            stderr=""
        )
        result = provider.call(
            system_prompt="You are a coder.",
            user_message="Write a hello world function."
        )
    assert isinstance(result, str)
    assert len(result) > 0

def test_claude_cli_raises_on_nonzero_exit():
    provider = ClaudeCliProvider(cli_path="claude", model="claude-sonnet-4-6")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        with pytest.raises(RuntimeError, match="Claude CLI error"):
            provider.call(system_prompt="You are a coder.", user_message="Write code.")

# --- Claude API Provider ---

def test_claude_api_returns_text():
    provider = ClaudeApiProvider(api_key="sk-test", model="claude-sonnet-4-6")
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="def hello(): return 'world'")]
    with patch("anthropic.Anthropic") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
        result = provider.call(
            system_prompt="You are a coder.",
            user_message="Write a hello world function."
        )
    assert result == "def hello(): return 'world'"

def test_claude_api_passes_correct_model():
    provider = ClaudeApiProvider(api_key="sk-test", model="claude-opus-4-7")
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="output")]
    with patch("anthropic.Anthropic") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.messages.create.return_value = mock_message
        provider.call(system_prompt="sys", user_message="msg")
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-opus-4-7"
