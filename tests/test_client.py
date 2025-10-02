import socket
import pytest
import httpx

from src.opencode_client import OpenCodeClient
from src.opencode_client.session import Session


def is_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP port is open on a given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        return result == 0


@pytest.fixture()
def opencode_client() -> OpenCodeClient:
    return OpenCodeClient(
        base_url="http://127.0.0.1:4596",
        model_provider="openai",
        model="gpt-5",
        timeout=600,
    )


async def apply_cleanup(opencode_client: OpenCodeClient) -> None:
    sessions = await opencode_client.list_sessions()
    for session in sessions:
        await opencode_client.delete_session(session.id)


@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=(not is_port_open("127.0.0.1", 4596)),
    reason="OpenCode Server not available",
)
async def test_crud_operations_with_sessions(opencode_client: OpenCodeClient) -> None:
    await apply_cleanup(opencode_client)
    assert opencode_client._current_session is None
    assert opencode_client._sessions == {}
    sessions = await opencode_client.list_sessions()
    assert len(sessions) == 0
    session = await opencode_client.create_current_session(title="test")
    assert session.title == "test"
    assert opencode_client._current_session is not None and isinstance(
        opencode_client._current_session, Session
    )
    assert opencode_client._current_session.id == session.id
    sessions = await opencode_client.list_sessions()
    assert len(sessions) == 1 and session == sessions[0]
    session = await opencode_client.update_session(title="hello")
    assert session is not None
    sessions = await opencode_client.list_sessions()
    assert len(sessions) == 1 and sessions[0].title == "hello"
    session1 = await opencode_client.create_current_session(title="test")
    sessions = await opencode_client.list_sessions()
    assert (
        len(sessions) == 2
        and session1 == sessions[0]
        and session.title == sessions[1].title
    )
    assert len(opencode_client._sessions) == 2
    assert opencode_client._current_session.id == session1.id
    await opencode_client.delete_session()
    sessions = await opencode_client.list_sessions()
    assert (
        len(sessions) == 1
        and session.title == sessions[0].title
        and session.id == sessions[0].id
    )
    await opencode_client.delete_session(session_id=session.id)
    sessions = await opencode_client.list_sessions()
    assert len(sessions) == 0


@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=(not is_port_open("127.0.0.1", 4596)),
    reason="OpenCode Server not available",
)
async def test_send_messages(opencode_client: OpenCodeClient) -> None:
    await apply_cleanup(opencode_client)
    await opencode_client.create_current_session(title="test")
    assistant_message = await opencode_client.send_message(
        text=["Hey there, can you tell me how to install OpenCode python client?"],
        file=["testfiles/file.txt"],
        system_message="You are an expert pythonista",
    )
    assert len(opencode_client.chat_history) == 2
    assert assistant_message in opencode_client.chat_history
    assert any("text" in part for part in assistant_message.parts)
    assert (
        "Hey there, can you tell me how to install OpenCode python client?"
        in "\n".join(opencode_client.string_chat_history)
    )
    assert "<assistant>" in "\n".join(
        opencode_client.string_chat_history
    ) and "<answer>" in "\n".join(opencode_client.string_chat_history)


@pytest.mark.asyncio
@pytest.mark.skipif(
    condition=(not is_port_open("127.0.0.1", 4596)),
    reason="OpenCode Server not available",
)
async def test_file_operations(opencode_client: OpenCodeClient) -> None:
    matches = await opencode_client.search_file_by_text("Installation")
    assert len(matches) > 0
    assert "README" in "\n".join([match.path.get("text", "") for match in matches])
    names = await opencode_client.search_file_by_name("README.md")
    assert "README.md" in "\n".join(names)
    files = await opencode_client.read_directory_files(path="./testfiles")
    assert len(files) == 1
    assert "file.txt" in files[0].path
    try:
        status = await opencode_client.get_files_status()
    except httpx.HTTPStatusError:
        status = None
    assert isinstance(status, list)
