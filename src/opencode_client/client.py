import httpx
import warnings

from dataclasses import asdict
from pathlib import Path
from typing import AsyncIterator, Optional, Union, List, cast
from contextlib import asynccontextmanager
from .session import Session, UserMessage, AssistantMessage, TextPart, FilePart
from .files import FileOperation, File, Match, FileInfo


class OpenCodeClient:
    """Client for interacting with OpenCode API."""

    def __init__(
        self, base_url: str, model_provider: str, model: str, timeout: int = 600
    ) -> None:
        """Initializes the OpenCode client.

        Args:
            base_url (str): API base URL.
            model_provider (str): Model provider name.
            model (str): Model identifier.
            timeout (int): Request timeout in seconds.
        """
        self.base_url = base_url
        self.model_provider = model_provider
        self.model = model
        self.timeout = timeout
        self._current_session: Optional[Session] = None
        self.chat_history: List[Union[UserMessage, AssistantMessage]] = []
        self.string_chat_history: List[str] = []

    @asynccontextmanager
    async def _get_client(self) -> AsyncIterator[httpx.AsyncClient]:
        """Creates async HTTP client context."""
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        ) as client:
            yield client

    async def create_current_session(
        self, title: Optional[str] = None, parent_id: Optional[str] = None
    ) -> Session:
        """Creates and stores a new session.

        Args:
            title (Optional[str]): Session title.
            parent_id (Optional[str]): Parent session ID.

        Returns:
            Session: Created session.
        """
        async with self._get_client() as client:
            res = await client.post(
                "/session", json={"parentID": parent_id or "", "title": title}
            )
            res.raise_for_status()
            self._current_session = Session(**res.json())
            return self._current_session

    async def list_sessions(self) -> list[Session]:
        """Lists all sessions.

        Returns:
            list[Session]: List of sessions.
        """
        async with self._get_client() as client:
            res = await client.get("/session")
            res.raise_for_status()
            payload = res.json()
            sessions = []
            for session in payload:
                sessions.append(Session(**session))
            return sessions

    async def _delete_session(self, session_id: str):
        """Deletes a session by ID.

        Args:
            session_id (str): Session ID to delete.
        """
        async with self._get_client() as client:
            res = await client.delete(f"/session/{session_id}")
            res.raise_for_status()

    async def _update_session(self, session_id: str, title: str):
        """Updates session title.

        Args:
            session_id (str): Session ID to update.
            title (str): New session title.
        """
        async with self._get_client() as client:
            res = await client.patch(f"/session/{session_id}", json={"title": title})
            res.raise_for_status()

    async def _abort_session(self, session_id: str):
        """Aborts a running session.

        Args:
            session_id (str): Session ID to abort.
        """
        async with self._get_client() as client:
            res = await client.post(f"/session/{session_id}/abort")
            res.raise_for_status()

    async def _send_message_to_session(
        self, session_id: str, message: UserMessage
    ) -> AssistantMessage:
        """Sends message to session and returns response.

        Args:
            session_id (str): Target session ID.
            message (UserMessage): Message to send.

        Returns:
            AssistantMessage: Assistant's response.
        """
        message_dict = asdict(message)
        message_dict_copy = message_dict.copy()
        for k, v in message_dict.items():
            if v == type(v)():
                message_dict_copy.pop(k)
        async with self._get_client() as client:
            res = await client.post(
                f"/session/{session_id}/message", json=message_dict_copy
            )
            res.raise_for_status()
            return AssistantMessage(**res.json())

    async def _perform_file_operation(
        self, operation: FileOperation, query: Optional[str] = None
    ) -> Union[List[File], List[Match], List[str], List[FileInfo]]:
        """Performs file operations.

        Args:
            operation (FileOperation): Operation type.
            query (Optional[str]): Query parameter for operation.

        Returns:
            Union[List[File], List[Match], List[str], List[FileInfo]]: Operation results.
        """
        if not query and operation != "get_status":
            raise ValueError(f"Operation {operation} requires a query value.")
        async with self._get_client() as client:
            if operation == "get_status":
                res = await client.get("/file/status")
                res.raise_for_status()
                files = []
                for f in res.json():
                    files.append(File(**f))
                return files
            elif operation == "read":
                if not Path(cast(str, query)).is_dir():
                    query = str(Path(cast(str, query)).parent)
                res = await client.get("/file", params={"path": query})
                res.raise_for_status()
                read_files = []
                for file in res.json():
                    read_files.append(FileInfo(**file))
                return read_files
            elif operation == "search_by_name":
                res = await client.get("/find/file", params={"query": query})
                res.raise_for_status()
                return res.json()
            else:
                res = await client.get("/find", params={"pattern": query})
                res.raise_for_status()
                matches = []
                for match in res.json():
                    matches.append(Match(**match))
                return matches

    async def delete_session(self, session_id: Optional[str] = None) -> None:
        """Deletes session by ID or current session.

        Args:
            session_id (Optional[str]): Session ID to delete.
        """
        session_id = session_id or (
            self._current_session.id if self._current_session else None
        )
        if not session_id:
            raise ValueError(
                "No session ID provided and no session ID available from current session"
            )
        await self._delete_session(session_id)

    async def update_session(
        self, session_id: Optional[str] = None, title: Optional[str] = None
    ) -> None:
        """Updates session title by ID or current session.

        Args:
            session_id (Optional[str]): Session ID to update.
            title (Optional[str]): New session title.
        """
        if not title:
            return
        else:
            session_id = session_id or (
                self._current_session.id if self._current_session else None
            )
            if not session_id:
                raise ValueError(
                    "No session ID provided and no session ID available from current session"
                )
            await self._update_session(session_id, title)

    async def abort_session(self, session_id: Optional[str] = None) -> None:
        """Aborts session by ID or current session.

        Args:
            session_id (Optional[str]): Session ID to abort.
        """
        session_id = session_id or (
            self._current_session.id if self._current_session else None
        )
        if not session_id:
            raise ValueError(
                "No session ID provided and no session ID available from current session"
            )
        await self._abort_session(session_id)

    async def send_message(
        self,
        text: Union[str, List[str]],
        file: Optional[Union[str, List[str]]] = None,
        system_message: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AssistantMessage:
        """Sends message with optional files to session.

        Args:
            text (Union[str, List[str]]): Message text or list of texts.
            file (Optional[Union[str, List[str]]]): File path(s) or URL(s).
            system_message (Optional[str]): System prompt.
            session_id (Optional[str]): Target session ID.

        Returns:
            AssistantMessage: Assistant's response.
        """
        session_id = session_id or (
            self._current_session.id if self._current_session else None
        )
        if not session_id:
            raise ValueError(
                "No session ID provided and no session ID available from current session"
            )
        parts = []
        if isinstance(text, list):
            for t in text:
                parts.append(TextPart.from_string(t))
        else:
            parts.append(TextPart.from_string(text))
        if file:
            if isinstance(file, list):
                for f in file:
                    if f.startswith(("http://", "https://", "ftp://", "file://")):
                        parts.append(FilePart.from_url(f))
                    else:
                        try:
                            parts.append(FilePart.from_file(f))
                        except ValueError as e:
                            warnings.warn(
                                f"It was not possible to include file {f} as FilePart because of: {e}"
                            )
                            continue
            else:
                if file.startswith(("http://", "https://", "ftp://", "file://")):
                    parts.append(FilePart.from_url(file))
                else:
                    try:
                        parts.append(FilePart.from_file(file))
                    except ValueError as e:
                        warnings.warn(
                            f"It was not possible to include file {file} as FilePart because of: {e}"
                        )
        user_message = UserMessage(
            modelID=self.model,
            providerID=self.model_provider,
            parts=parts,
            system=system_message or "",
        )
        self.chat_history.append(user_message)
        self.string_chat_history.append(
            user_message.to_string(include_system_prompt=True)
        )
        assistant_message = await self._send_message_to_session(
            session_id=session_id, message=user_message
        )
        self.chat_history.append(assistant_message)
        self.string_chat_history.append(assistant_message.to_string())
        return assistant_message

    async def search_file_by_name(self, name: str) -> List[str]:
        """Searches files by name.

        Args:
            name (str): Filename to search.

        Returns:
            List[str]: List of matching file paths.
        """
        return await self._perform_file_operation(
            operation="search_by_name", query=name
        )  # type: ignore

    async def search_file_by_text(self, pattern: str) -> List[Match]:
        """Searches files by text pattern.

        Args:
            pattern (str): Text pattern to search.

        Returns:
            List[Match]: List of matches.
        """
        return await self._perform_file_operation(
            operation="search_by_text", query=pattern
        )  # type: ignore

    async def read_directory_files(self, path: str) -> List[FileInfo]:
        """Reads files in directory.

        Args:
            path (str): Directory path.

        Returns:
            List[FileInfo]: List of file information.
        """
        return await self._perform_file_operation(operation="read", query=path)  # type: ignore

    async def get_files_status(self) -> List[File]:
        """Gets status of all files.

        Returns:
            List[File]: List of files with status.
        """
        return await self._perform_file_operation(operation="get_status")  # type: ignore
