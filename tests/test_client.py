import socket
import pytest

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
