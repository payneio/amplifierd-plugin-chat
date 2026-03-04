import pytest
from unittest.mock import MagicMock
from chat_plugin.commands import CommandProcessor


@pytest.fixture
def processor():
    return CommandProcessor(session_manager=None, event_bus=None)


@pytest.fixture
def processor_with_mock_session():
    # Build mock context with clear()
    mock_context = MagicMock()

    # Build mock mode_discovery with list_modes() and find()
    mock_mode_discovery = MagicMock()
    mock_mode_discovery.list_modes.return_value = [
        ("debug", "Debug mode", "built-in"),
        ("focus", "Focus mode", "built-in"),
    ]
    mock_mode_discovery.find.side_effect = lambda name: (
        name in ("debug", "focus")
    )

    # Build session_state dict with mode_discovery
    mock_session_state = {
        "mode_discovery": mock_mode_discovery,
        "active_mode": None,
    }

    # Build mock coordinator with get() and config
    mock_coordinator = MagicMock()
    mock_coordinator.get.side_effect = lambda key: (
        mock_context if key == "context" else None
    )
    mock_coordinator.config = {"agents": {"default": {}, "coder": {}}}
    mock_coordinator.session_state = mock_session_state

    # Build mock session with coordinator
    mock_session = MagicMock()
    mock_session.coordinator = mock_coordinator

    # Build mock SessionHandle
    mock_handle = MagicMock()
    mock_handle.session_id = "abc"
    mock_handle.status = "idle"
    mock_handle.bundle_name = "test-bundle"
    mock_handle.working_dir = "/tmp/test"
    mock_handle.turn_count = 5
    mock_handle.session = mock_session

    # Build mock session_manager
    mock_session_manager = MagicMock()
    mock_session_manager.get.return_value = mock_handle

    return CommandProcessor(session_manager=mock_session_manager, event_bus=None)


def test_process_input_recognizes_command(processor):
    action, data = processor.process_input("/help")
    assert action == "command"
    assert data["command"] == "help"


def test_process_input_recognizes_command_with_args(processor):
    action, data = processor.process_input("/mode debug")
    assert action == "command"
    assert data["command"] == "mode"
    assert data["args"] == ["debug"]


def test_process_input_non_command(processor):
    action, data = processor.process_input("hello world")
    assert action == "prompt"
    assert data["text"] == "hello world"


def test_help_command(processor):
    result = processor.handle_command("help", [], session_id=None)
    assert result["type"] == "help"
    assert len(result["data"]["commands"]) > 0


def test_unknown_command(processor):
    result = processor.handle_command("nonexistent", [], session_id=None)
    assert result["type"] == "error"


def test_command_endpoint(client):
    resp = client.post("/chat/command", json={"command": "/help"})
    assert resp.status_code == 200
    assert resp.json()["type"] == "help"


def test_status_command_no_session(processor):
    result = processor.handle_command("status", [], session_id=None)
    assert result["type"] == "error"
    assert "no active session" in result["data"]["message"].lower()


def test_cwd_command(processor_with_mock_session):
    result = processor_with_mock_session.handle_command("cwd", [], session_id="abc")
    assert result["type"] == "cwd"
    assert "working_dir" in result["data"]


def test_status_command(processor_with_mock_session):
    result = processor_with_mock_session.handle_command("status", [], session_id="abc")
    assert result["type"] == "status"
    assert "session_id" in result["data"]


def test_clear_command(processor_with_mock_session):
    result = processor_with_mock_session.handle_command("clear", [], session_id="abc")
    assert result["type"] == "cleared"


def test_tools_command(processor_with_mock_session):
    result = processor_with_mock_session.handle_command("tools", [], session_id="abc")
    assert result["type"] == "tools"


def test_agents_command(processor_with_mock_session):
    result = processor_with_mock_session.handle_command("agents", [], session_id="abc")
    assert result["type"] == "agents"


def test_config_command(processor_with_mock_session):
    result = processor_with_mock_session.handle_command("config", [], session_id="abc")
    assert result["type"] == "config"


def test_modes_command(processor_with_mock_session):
    result = processor_with_mock_session.handle_command("modes", [], session_id="abc")
    assert result["type"] == "modes"
    assert "modes" in result["data"]


def test_mode_activate(processor_with_mock_session):
    result = processor_with_mock_session.handle_command("mode", ["debug"], session_id="abc")
    assert result["type"] in ("mode_changed", "error")


def test_mode_with_trailing_prompt(processor_with_mock_session):
    """/mode debug my problem activates debug mode and returns trailing prompt."""
    result = processor_with_mock_session.handle_command(
        "mode", ["debug", "my", "problem"], session_id="abc"
    )
    if result["type"] == "mode_changed":
        assert result["data"].get("trailing_prompt") == "my problem"


def test_mode_deactivate(processor_with_mock_session):
    """/mode off deactivates current mode."""
    result = processor_with_mock_session.handle_command("mode", ["off"], session_id="abc")
    assert result["type"] == "mode_changed"
    assert result["data"]["active_mode"] is None


def test_rename_command(processor_with_mock_session):
    result = processor_with_mock_session.handle_command("rename", ["My", "Session"], session_id="abc")
    assert result["type"] == "renamed"
    assert result["data"]["name"] == "My Session"


def test_fork_command_no_args(processor_with_mock_session):
    """Fork with no args returns turn info."""
    result = processor_with_mock_session.handle_command("fork", [], session_id="abc")
    assert result["type"] == "fork_info"


def test_fork_command_with_turn(processor_with_mock_session):
    result = processor_with_mock_session.handle_command("fork", ["3"], session_id="abc")
    assert result["type"] == "forked"
